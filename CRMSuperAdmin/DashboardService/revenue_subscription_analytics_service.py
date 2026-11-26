"""Service layer for the Revenue & Subscription Analytics dashboard screen."""

from datetime import date, datetime, timedelta

from django.db.models import Count, FloatField, Q, Sum
from django.db.models.functions import Coalesce, TruncMonth

from CRMSuperAdmin.DashboardService.superadmin_dashboard_service import (
    _build_free_to_paid_conversion,
    _build_month_slots,
    _calc_growth,
    _compute_core_metrics,
    _filtered_addon_line_items_qs,
    _format_inr,
    _paying_subscription_q,
    _sub_monthly_amount,
    _to_aware_datetime,
)
from CRMSuperAdmin.models import InvoiceLineItem, Payments, ProductMaster, Renewal


def _compute_subscription_revenue(filters, start_dt, end_dt, arr_fallback=0.0):
    """Compute paid subscription (non-addon) revenue from InvoiceLineItem, Payments, or ARR fallback."""
    line_qs = (
        InvoiceLineItem.objects.filter(
            Is_Deleted=False,
            Invoice_Id__Is_Deleted=False,
            Invoice_Id__Payment_Status__icontains="paid",
            Invoice_Id__Invoice_Date__gte=start_dt,
            Invoice_Id__Invoice_Date__lte=end_dt,
        )
        .exclude(Item_Type__icontains="addon")
    )
    if filters["product_id"] is not None:
        line_qs = line_qs.filter(Product_Id_id=filters["product_id"])
    if filters["partner_id"] is not None:
        line_qs = line_qs.filter(Invoice_Id__Customer_Id__Partner_Id_id=filters["partner_id"])
    if filters.get("partner_type"):
        pt = filters["partner_type"]
        line_qs = line_qs.filter(
            Q(Invoice_Id__Customer_Id__Partner_Id__Tier__icontains=pt)
            | Q(Invoice_Id__Customer_Id__Partner_Id__Partner_Type__icontains=pt)
        )
    if filters["country"]:
        line_qs = line_qs.filter(Invoice_Id__Customer_Id__Country__icontains=filters["country"])

    line_total = float(
        line_qs.aggregate(total=Coalesce(Sum("TotalAmount"), 0.0, output_field=FloatField()))["total"]
        or 0.0
    )
    if line_total > 0:
        return round(line_total, 2)

    pay_qs = Payments.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        status__icontains="success",
        Payment_Date__gte=start_dt.date(),
        Payment_Date__lte=end_dt.date(),
    )
    if filters["product_id"] is not None:
        pay_qs = pay_qs.filter(Product_Id_id=filters["product_id"])
    if filters["partner_id"] is not None:
        pay_qs = pay_qs.filter(Customer_Id__Partner_Id_id=filters["partner_id"])
    if filters.get("partner_type"):
        pt = filters["partner_type"]
        pay_qs = pay_qs.filter(
            Q(Customer_Id__Partner_Id__Tier__icontains=pt)
            | Q(Customer_Id__Partner_Id__Partner_Type__icontains=pt)
        )
    if filters["country"]:
        pay_qs = pay_qs.filter(Customer_Id__Country__icontains=filters["country"])

    pay_total = float(
        pay_qs.aggregate(total=Coalesce(Sum("NetAmount"), 0.0, output_field=FloatField()))["total"]
        or 0.0
    )
    if pay_total > 0:
        return round(pay_total, 2)

    return round(float(arr_fallback or 0.0), 2)


def _filtered_renewals_qs(filters):
    """Build filtered Renewal queryset using icontains."""
    qs = Renewal.objects.filter(Is_Deleted=False)
    if filters["product_id"] is not None:
        qs = qs.filter(Product_Id_id=filters["product_id"])
    if filters["partner_id"] is not None:
        qs = qs.filter(Customer_Id__Partner_Id_id=filters["partner_id"])
    if filters.get("partner_type"):
        pt = filters["partner_type"]
        qs = qs.filter(
            Q(Customer_Id__Partner_Id__Tier__icontains=pt)
            | Q(Customer_Id__Partner_Id__Partner_Type__icontains=pt)
        )
    if filters["country"]:
        qs = qs.filter(Customer_Id__Country__icontains=filters["country"])
    return qs


def _completed_renewals_q():
    """Match completed/approved renewals via icontains."""
    return (
        Q(Renewal_Status__icontains="approv")
        | Q(Renewal_Status__icontains="complet")
        | Q(Renewal_Status__icontains="active")
        | Q(Payment_Status__icontains="paid")
    )


def _build_revenue_by_plan(subs_qs, end_dt):
    """Group normalized ARR by Plan PK for Revenue by Subscription Plan donut."""
    active_subs = list(
        subs_qs.filter(Q(status__icontains="active") | Q(status__icontains="trial"))
        .exclude(status__icontains="inactive")
        .filter(Created_Date__lte=end_dt)
        .select_related("Plan_Id")
    )

    by_plan = {}
    for sub in active_subs:
        plan_id = sub.Plan_Id_id
        plan_name = (
            (sub.Plan_Id.Plan_Name if sub.Plan_Id and sub.Plan_Id.Plan_Name else None)
            or sub.Plan_Name
            or "Free Core (Non-paid)"
        )
        key = plan_id if plan_id is not None else plan_name
        if key not in by_plan:
            by_plan[key] = {"plan_id": plan_id, "plan_name": plan_name, "revenue": 0.0}
        if not sub.is_trial and float(sub.SuscriptionAmount or 0) > 0:
            by_plan[key]["revenue"] += _sub_monthly_amount(sub) * 12.0

    total_rev = sum(item["revenue"] for item in by_plan.values())
    segments = []
    for item in sorted(by_plan.values(), key=lambda x: x["revenue"], reverse=True):
        rev = round(item["revenue"], 2)
        pct = round((rev / total_rev) * 100, 1) if total_rev > 0 else 0.0
        segments.append(
            {
                "plan_id": item["plan_id"],
                "plan_name": item["plan_name"],
                "revenue": rev,
                "revenue_formatted": _format_inr(rev),
                "pct": pct,
            }
        )
    return {
        "total_revenue": round(total_rev, 2),
        "total_revenue_formatted": _format_inr(total_rev),
        "segments": segments,
    }


def _build_plan_customer_distribution(subs_qs, end_dt):
    """Group distinct active customers by Plan PK for Plan-wise Customer Distribution donut."""
    active_subs = list(
        subs_qs.filter(Q(status__icontains="active") | Q(status__icontains="trial"))
        .exclude(status__icontains="inactive")
        .filter(Created_Date__lte=end_dt, Customer_Id_id__isnull=False)
        .select_related("Plan_Id")
    )

    by_plan = {}
    all_customers = set()
    for sub in active_subs:
        cid = sub.Customer_Id_id
        all_customers.add(cid)
        pid = sub.Plan_Id_id
        pname = (
            (sub.Plan_Id.Plan_Name if sub.Plan_Id and sub.Plan_Id.Plan_Name else None)
            or sub.Plan_Name
            or "Unassigned"
        )
        if pid not in by_plan:
            by_plan[pid] = {"plan_id": pid, "plan_name": pname, "customers": set()}
        by_plan[pid]["customers"].add(cid)

    total_customers = sum(len(item["customers"]) for item in by_plan.values())
    segments = []
    for item in sorted(by_plan.values(), key=lambda x: len(x["customers"]), reverse=True):
        cnt = len(item["customers"])
        segments.append(
            {
                "plan_id": item["plan_id"],
                "plan_name": item["plan_name"],
                "customers_count": cnt,
                "pct": round((cnt / total_customers) * 100, 1) if total_customers > 0 else 0.0,
            }
        )
    return {
        "total_active_tenants": len(all_customers),
        "segments": segments,
    }


def _build_product_revenue_arr(subs_qs, filters):
    """Group normalized ARR by ProductMaster PK for Product-wise Revenue (ARR) horizontal bar chart."""
    products_qs = ProductMaster.objects.filter(Is_Deleted=False, Is_Active=True).order_by("id")
    if filters["product_id"] is not None:
        products_qs = products_qs.filter(pk=filters["product_id"])

    paying_subs = list(
        subs_qs.filter(status__icontains="active")
        .exclude(status__icontains="inactive")
        .filter(_paying_subscription_q(), Created_Date__lte=filters["end_dt"])
        .select_related("Product_Id", "Plan_Id")
    )
    arr_by_prod = {}
    for sub in paying_subs:
        pid = sub.Product_Id_id
        if pid is not None:
            arr_by_prod[pid] = arr_by_prod.get(pid, 0.0) + (_sub_monthly_amount(sub) * 12.0)

    bars = []
    for prod in products_qs:
        arr_val = round(arr_by_prod.get(prod.id, 0.0), 2)
        bars.append(
            {
                "product_id": prod.id,
                "product_name": prod.Product_Name or prod.Product_Code or f"Product #{prod.id}",
                "arr": arr_val,
                "arr_crores": round(arr_val / 10_000_000, 2),
            }
        )
    return sorted(bars, key=lambda x: x["arr"], reverse=True)


def build_revenue_subscription_analytics_dashboard(filters):
    """Build complete payload for the Revenue & Subscription Analytics dashboard screen."""
    core = _compute_core_metrics(filters)
    subs_qs = core["subs_qs"]
    end_dt = filters["end_dt"]
    prev_end_dt = filters["prev_end_dt"]

    # Revenue KPIs
    sub_rev = _compute_subscription_revenue(
        filters, filters["start_dt"], end_dt, arr_fallback=core["arr"]
    )
    prev_sub_rev = _compute_subscription_revenue(
        filters, filters["prev_start_dt"], prev_end_dt, arr_fallback=core["prev_arr"]
    )
    addon_rev = core["addon_rev"]
    prev_addon_rev = core["prev_addon_rev"]
    total_rev = round(sub_rev + addon_rev, 2)
    prev_total_rev = round(prev_sub_rev + prev_addon_rev, 2)

    # Subscription KPIs
    active_sub_qs = (
        subs_qs.filter(Q(status__icontains="active") | Q(status__icontains="trial"))
        .exclude(status__icontains="inactive")
    )
    active_subscriptions = active_sub_qs.filter(Created_Date__lte=end_dt).count()
    prev_active_subscriptions = active_sub_qs.filter(Created_Date__lte=prev_end_dt).count()

    new_subscriptions = subs_qs.filter(
        Created_Date__gte=filters["start_dt"], Created_Date__lte=end_dt
    ).count()
    prev_new_subscriptions = subs_qs.filter(
        Created_Date__gte=filters["prev_start_dt"], Created_Date__lte=prev_end_dt
    ).count()

    renewals_qs = _filtered_renewals_qs(filters).filter(_completed_renewals_q())
    renewals_count = renewals_qs.filter(
        Created_Date__gte=filters["start_dt"], Created_Date__lte=end_dt
    ).count()
    prev_renewals_count = renewals_qs.filter(
        Created_Date__gte=filters["prev_start_dt"], Created_Date__lte=prev_end_dt
    ).count()
    using_sub_renewal_fallback = False
    if renewals_count == 0:
        using_sub_renewal_fallback = True
        renewals_count = subs_qs.filter(
            previous_subscription__isnull=False,
            Created_Date__gte=filters["start_dt"],
            Created_Date__lte=end_dt,
        ).count()
        prev_renewals_count = subs_qs.filter(
            previous_subscription__isnull=False,
            Created_Date__gte=filters["prev_start_dt"],
            Created_Date__lte=prev_end_dt,
        ).count()

    churned_count = subs_qs.filter(
        Q(status__icontains="cancel") | Q(status__icontains="expir")
    ).filter(Updated_Date__gte=filters["start_dt"], Updated_Date__lte=end_dt).count()
    prev_churned_count = subs_qs.filter(
        Q(status__icontains="cancel") | Q(status__icontains="expir")
    ).filter(Updated_Date__gte=filters["prev_start_dt"], Updated_Date__lte=prev_end_dt).count()

    renewal_denom = renewals_count + churned_count
    renewal_rate = round((renewals_count / renewal_denom) * 100, 1) if renewal_denom > 0 else 0.0
    prev_renewal_denom = prev_renewals_count + prev_churned_count
    prev_renewal_rate = (
        round((prev_renewals_count / prev_renewal_denom) * 100, 1) if prev_renewal_denom > 0 else renewal_rate
    )

    total_subs_base = max(1, subs_qs.filter(Created_Date__lte=end_dt).count())
    prev_subs_base = max(1, subs_qs.filter(Created_Date__lte=prev_end_dt).count())
    churn_rate = round((churned_count / total_subs_base) * 100, 1)
    prev_churn_rate = round((prev_churned_count / prev_subs_base) * 100, 1)

    # Monthly trends
    slots = _build_month_slots(filters["start_date"], filters["end_date"])
    paying_subs = list(
        subs_qs.filter(status__icontains="active")
        .exclude(status__icontains="inactive")
        .filter(_paying_subscription_q())
    )
    rev_trend = []
    for yr, mo in slots:
        if mo == 12:
            month_end = _to_aware_datetime(datetime(yr + 1, 1, 1)) - timedelta(seconds=1)
        else:
            month_end = _to_aware_datetime(datetime(yr, mo + 1, 1)) - timedelta(seconds=1)
        month_mrr = sum(
            _sub_monthly_amount(s)
            for s in paying_subs
            if s.Created_Date is None or s.Created_Date <= month_end
        )
        rev_trend.append(
            {
                "month": date(yr, mo, 1).strftime("%b"),
                "year_month": f"{yr:04d}-{mo:02d}",
                "mrr_lakhs": round(month_mrr / 100_000, 1),
                "arr_crores": round((month_mrr * 12.0) / 10_000_000, 2),
            }
        )

    addon_rows = (
        _filtered_addon_line_items_qs(filters, filters["start_dt"], end_dt)
        .annotate(month=TruncMonth("Invoice_Id__Invoice_Date"))
        .values("month")
        .annotate(total=Coalesce(Sum("TotalAmount"), 0.0, output_field=FloatField()))
        .order_by("month")
    )
    addon_by_ym = {
        (r["month"].year, r["month"].month): float(r["total"] or 0.0)
        for r in addon_rows
        if r.get("month")
    }
    addon_trend = [
        {
            "month": date(yr, mo, 1).strftime("%b"),
            "year_month": f"{yr:04d}-{mo:02d}",
            "addon_revenue_cr": round(addon_by_ym.get((yr, mo), 0.0) / 10_000_000, 2),
        }
        for yr, mo in slots
    ]

    churn_rows = (
        subs_qs.filter(Q(status__icontains="cancel") | Q(status__icontains="expir"))
        .filter(Updated_Date__gte=filters["start_dt"], Updated_Date__lte=end_dt)
        .annotate(month=TruncMonth("Updated_Date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    churn_by_ym = {(r["month"].year, r["month"].month): r["total"] for r in churn_rows if r.get("month")}

    ren_source_qs = (
        subs_qs.filter(previous_subscription__isnull=False)
        if using_sub_renewal_fallback
        else renewals_qs
    )
    ren_rows = (
        ren_source_qs.filter(Created_Date__gte=filters["start_dt"], Created_Date__lte=end_dt)
        .annotate(month=TruncMonth("Created_Date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    ren_by_ym = {(r["month"].year, r["month"].month): r["total"] for r in ren_rows if r.get("month")}

    churn_trend = []
    renewal_rate_trend = []
    for yr, mo in slots:
        m_churn = churn_by_ym.get((yr, mo), 0)
        m_ren = ren_by_ym.get((yr, mo), 0)
        m_churn_pct = round((m_churn / total_subs_base) * 100, 1)
        m_denom = m_ren + m_churn
        m_ren_pct = round((m_ren / m_denom) * 100, 1) if m_denom > 0 else 0.0
        label = date(yr, mo, 1).strftime("%b")
        ym = f"{yr:04d}-{mo:02d}"
        churn_trend.append({"month": label, "year_month": ym, "churn_rate_pct": m_churn_pct})
        renewal_rate_trend.append({"month": label, "year_month": ym, "renewal_rate_pct": m_ren_pct})

    funnel = _build_free_to_paid_conversion(core)
    funnel["active_paying_tenants"] = core["paying_tenants"]

    sub_pct = round((sub_rev / total_rev) * 100, 1) if total_rev > 0 else 0.0
    addon_pct = round((addon_rev / total_rev) * 100, 1) if total_rev > 0 else 0.0

    return {
        "filters_applied": {
            "date_range": filters["date_range"],
            "from_date": str(filters["start_date"]),
            "to_date": str(filters["end_date"]),
            "product_id": filters["product_id"],
            "country": filters["country"],
            "customer_type": filters["customer_type"],
            "partner_type": filters.get("partner_type"),
            "partner_id": filters["partner_id"],
        },
        "kpis": {
            "mrr": {
                "value": core["mrr"],
                "formatted": _format_inr(core["mrr"]),
                **_calc_growth(core["mrr"], core["prev_mrr"]),
            },
            "arr": {
                "value": core["arr"],
                "formatted": _format_inr(core["arr"]),
                **_calc_growth(core["arr"], core["prev_arr"]),
            },
            "total_subscription_revenue": {
                "value": sub_rev,
                "formatted": _format_inr(sub_rev),
                **_calc_growth(sub_rev, prev_sub_rev),
            },
            "addon_revenue": {
                "value": addon_rev,
                "formatted": _format_inr(addon_rev),
                **_calc_growth(addon_rev, prev_addon_rev),
            },
            "total_revenue": {
                "value": total_rev,
                "formatted": _format_inr(total_rev),
                **_calc_growth(total_rev, prev_total_rev),
            },
            "active_subscriptions": {
                "value": active_subscriptions,
                **_calc_growth(active_subscriptions, prev_active_subscriptions),
            },
            "new_subscriptions": {
                "value": new_subscriptions,
                **_calc_growth(new_subscriptions, prev_new_subscriptions),
            },
            "subscription_renewals": {
                "value": renewals_count,
                **_calc_growth(renewals_count, prev_renewals_count),
            },
            "renewal_rate": {
                "value": renewal_rate,
                "pp_change": round(renewal_rate - prev_renewal_rate, 1),
            },
            "churn_rate": {
                "value": churn_rate,
                "pp_change": round(churn_rate - prev_churn_rate, 1),
            },
        },
        "charts": {
            "subscription_revenue_trend": {
                "latest_mrr_lakhs": rev_trend[-1]["mrr_lakhs"] if rev_trend else 0.0,
                "latest_arr_crores": rev_trend[-1]["arr_crores"] if rev_trend else 0.0,
                "monthly_data": rev_trend,
            },
            "revenue_by_subscription_plan": _build_revenue_by_plan(subs_qs, end_dt),
            "revenue_by_type": {
                "total_revenue": total_rev,
                "total_revenue_formatted": _format_inr(total_rev),
                "segments": [
                    {
                        "key": "subscription",
                        "label": "Subscription",
                        "revenue": sub_rev,
                        "revenue_formatted": _format_inr(sub_rev),
                        "pct": sub_pct,
                    },
                    {
                        "key": "addons",
                        "label": "Add-ons",
                        "revenue": addon_rev,
                        "revenue_formatted": _format_inr(addon_rev),
                        "pct": addon_pct,
                    },
                ],
            },
            "product_wise_revenue_arr": _build_product_revenue_arr(subs_qs, filters),
            "subscription_conversion_funnel": funnel,
            "plan_wise_customer_distribution": _build_plan_customer_distribution(subs_qs, end_dt),
            "addon_revenue_trend": {
                "latest_addon_cr": round(addon_rev / 10_000_000, 2),
                "monthly_data": addon_trend,
            },
            "churn_trend": {
                "latest_churn_pct": churn_rate,
                "monthly_data": churn_trend,
            },
            "renewal_rate_trend": {
                "latest_renewal_rate_pct": renewal_rate,
                "monthly_data": renewal_rate_trend,
            },
        },
    }
