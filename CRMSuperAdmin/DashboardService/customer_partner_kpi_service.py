"""Service layer for Customer & Partner KPIs dashboard APIs."""

from datetime import date

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from CRMSuperAdmin.DashboardService.superadmin_dashboard_service import (
    _build_free_to_paid_conversion,
    _build_month_slots,
    _build_monthly_customer_growth,
    _calc_growth,
    _compute_core_metrics,
    _format_inr,
    _paying_subscription_q,
    _sub_monthly_amount,
)
from CRMSuperAdmin.models import Account
from partneracademy.models import Certificate, ModuleEnrollment


def _build_filters_summary(filters):
    """Serialize applied filters consistently for API responses."""
    return {
        "date_range": filters["date_range"],
        "from_date": str(filters["start_date"]),
        "to_date": str(filters["end_date"]),
        "product_id": filters["product_id"],
        "country": filters["country"],
        "customer_type": filters["customer_type"],
        "partner_type": filters.get("partner_type"),
        "partner_id": filters["partner_id"],
    }


def _build_customer_growth_trend(core, filters):
    """Build monthly cumulative Total Customers vs Active Customers trend."""
    slots = _build_month_slots(filters["start_date"], filters["end_date"])
    total_series = _build_monthly_customer_growth(core["accounts_qs"], filters)

    active_inst_qs = core["active_instances_qs"]
    active_baseline = (
        active_inst_qs.filter(Created_Date__lt=filters["start_dt"])
        .values("Customer_Id_id")
        .distinct()
        .count()
    )
    active_rows = (
        active_inst_qs.filter(Created_Date__gte=filters["start_dt"], Created_Date__lte=filters["end_dt"])
        .annotate(month=TruncMonth("Created_Date"))
        .values("month")
        .annotate(total=Count("Customer_Id_id", distinct=True))
        .order_by("month")
    )
    active_by_ym = {(r["month"].year, r["month"].month): r["total"] for r in active_rows if r.get("month")}

    running_active = active_baseline
    combined = []
    for idx, (yr, mo) in enumerate(slots):
        running_active += active_by_ym.get((yr, mo), 0)
        total_val = total_series[idx]["total_tenants"] if idx < len(total_series) else 0
        combined.append(
            {
                "month": date(yr, mo, 1).strftime("%b"),
                "year_month": f"{yr:04d}-{mo:02d}",
                "total_customers": total_val,
                "active_customers": running_active,
            }
        )
    return combined


def _build_customer_segmentation(core):
    """Compute Customer Segmentation donut breakdown: Free Core, Paying, Trial, Inactive."""
    total = core["total_tenants"]
    paying = core["paying_tenants"]
    trial = core["trial_tenants"]
    free_core = core["free_core_tenants"]
    inactive = max(0, total - (free_core + paying + trial))

    def _pct(val):
        return round((val / total) * 100, 1) if total > 0 else 0.0

    return {
        "total_customers": total,
        "segments": [
            {"key": "free_core", "label": "Free Core", "count": free_core, "pct": _pct(free_core)},
            {"key": "paying", "label": "Paying", "count": paying, "pct": _pct(paying)},
            {"key": "trial", "label": "Trial", "count": trial, "pct": _pct(trial)},
            {"key": "inactive", "label": "Inactive", "count": inactive, "pct": _pct(inactive)},
        ],
    }


def _compute_customer_retention(core, filters):
    """Compute customer retention rate and pp delta from non-churned vs total subscribed customers."""
    subs_qs = core["subs_qs"]
    total_sub_customers = subs_qs.filter(Created_Date__lte=filters["end_dt"]).values("Customer_Id_id").distinct().count()
    churned_customers = (
        subs_qs.filter(Q(status__icontains="cancel") | Q(status__icontains="expir"))
        .filter(Created_Date__lte=filters["end_dt"])
        .values("Customer_Id_id")
        .distinct()
        .count()
    )
    retention = (
        round(((total_sub_customers - churned_customers) / total_sub_customers) * 100, 1)
        if total_sub_customers > 0
        else 0.0
    )

    prev_total = subs_qs.filter(Created_Date__lte=filters["prev_end_dt"]).values("Customer_Id_id").distinct().count()
    prev_churned = (
        subs_qs.filter(Q(status__icontains="cancel") | Q(status__icontains="expir"))
        .filter(Created_Date__lte=filters["prev_end_dt"])
        .values("Customer_Id_id")
        .distinct()
        .count()
    )
    prev_retention = (
        round(((prev_total - prev_churned) / prev_total) * 100, 1) if prev_total > 0 else retention
    )
    return {
        "rate": retention,
        "pp_change": round(retention - prev_retention, 1),
    }


def _build_top_customers_by_arr(core, filters, limit=5):
    """Aggregate normalized ARR per Account PK and return top N customers with YoY growth."""
    paying_subs = list(
        core["subs_qs"]
        .filter(status__icontains="active")
        .exclude(status__icontains="inactive")
        .filter(_paying_subscription_q(), Created_Date__lte=filters["end_dt"])
        .select_related("Customer_Id", "Customer_Id__Organization_Id", "Customer_Id__Product_Id", "Product_Id", "Plan_Id")
    )

    by_customer = {}
    for sub in paying_subs:
        if not sub.Customer_Id_id or not sub.Customer_Id:
            continue
        acc = sub.Customer_Id
        cid = acc.id
        sub_arr = _sub_monthly_amount(sub) * 12.0
        if cid not in by_customer:
            cust_name = (
                acc.Organization_Name
                or (acc.Organization_Id.Organization_Name if acc.Organization_Id else None)
                or acc.Contact_Name
                or f"Customer #{cid}"
            )
            prod = sub.Product_Id or acc.Product_Id
            by_customer[cid] = {
                "customer_id": cid,
                "customer_name": cust_name,
                "product_id": prod.id if prod else None,
                "product_name": (prod.Product_Name or prod.Product_Code) if prod else "N/A",
                "arr": 0.0,
                "prev_arr": 0.0,
            }
        by_customer[cid]["arr"] += sub_arr
        if sub.Created_Date and sub.Created_Date <= filters["prev_end_dt"]:
            by_customer[cid]["prev_arr"] += sub_arr

    ranked = sorted(by_customer.values(), key=lambda x: x["arr"], reverse=True)[:limit]
    rows = []
    for idx, item in enumerate(ranked, start=1):
        arr_val = round(item["arr"], 2)
        growth = _calc_growth(arr_val, item["prev_arr"])
        rows.append(
            {
                "rank": idx,
                "customer_id": item["customer_id"],
                "customer_name": item["customer_name"],
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "arr": arr_val,
                "arr_formatted": _format_inr(arr_val),
                "growth_yoy_pct": growth["growth_pct"],
                "direction": growth["direction"],
            }
        )
    return rows


def build_customer_kpi_dashboard(filters):
    """Build API 1 response: Customer KPIs, Growth Trend, Segmentation, Conversion/Retention, Top 5 Customers."""
    core = _compute_core_metrics(filters)
    free_to_paid = _build_free_to_paid_conversion(core)
    retention = _compute_customer_retention(core, filters)

    return {
        "filters_applied": _build_filters_summary(filters),
        "customer_kpis": {
            "total_customers": {
                "value": core["total_tenants"],
                **_calc_growth(core["total_tenants"], core["prev_total_tenants"]),
            },
            "active_customers": {
                "value": core["active_tenants"],
                **_calc_growth(core["active_tenants"], core["prev_active_tenants"]),
            },
            "paying_customers": {
                "value": core["paying_tenants"],
                **_calc_growth(core["paying_tenants"], core["prev_paying_tenants"]),
            },
            "trial_customers": {
                "value": core["trial_tenants"],
                **_calc_growth(core["trial_tenants"], core["prev_trial_tenants"]),
            },
        },
        "customer_growth_trend": {
            "monthly_data": _build_customer_growth_trend(core, filters),
        },
        "customer_segmentation": _build_customer_segmentation(core),
        "key_metrics": {
            "free_to_paid_conversion": {
                "rate": free_to_paid["conversion_rate"],
                "pp_change": free_to_paid["pp_change"],
            },
            "customer_retention_rate": retention,
        },
        "top_customers": _build_top_customers_by_arr(core, filters, limit=5),
    }


def _partner_cert_qs(partners_qs):
    """Build Certificate queryset scoped to filtered Partner PKs using icontains."""
    partner_ids = partners_qs.values_list("id", flat=True)
    return Certificate.objects.filter(
        Is_Deleted=False,
        Partner_id__in=partner_ids,
        Status__icontains="issued",
    ).filter(Q(Expiry_Date__isnull=True) | Q(Expiry_Date__gte=timezone.now()))


def _build_partner_trend(partners_qs, cert_qs, filters):
    """Build monthly grouped bar series for Total Partners vs Certified Partners."""
    slots = _build_month_slots(filters["start_date"], filters["end_date"])

    p_baseline = partners_qs.filter(Created_Date__lt=filters["start_dt"]).count()
    p_rows = (
        partners_qs.filter(Created_Date__gte=filters["start_dt"], Created_Date__lte=filters["end_dt"])
        .annotate(month=TruncMonth("Created_Date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    p_by_ym = {(r["month"].year, r["month"].month): r["total"] for r in p_rows if r.get("month")}

    c_baseline = cert_qs.filter(Created_Date__lt=filters["start_dt"]).values("Partner_id").distinct().count()
    c_rows = (
        cert_qs.filter(Created_Date__gte=filters["start_dt"], Created_Date__lte=filters["end_dt"])
        .annotate(month=TruncMonth("Created_Date"))
        .values("month")
        .annotate(total=Count("Partner_id", distinct=True))
        .order_by("month")
    )
    c_by_ym = {(r["month"].year, r["month"].month): r["total"] for r in c_rows if r.get("month")}

    running_p = p_baseline
    running_c = c_baseline
    series = []
    for yr, mo in slots:
        running_p += p_by_ym.get((yr, mo), 0)
        running_c += c_by_ym.get((yr, mo), 0)
        series.append(
            {
                "month": date(yr, mo, 1).strftime("%b"),
                "year_month": f"{yr:04d}-{mo:02d}",
                "total_partners": running_p,
                "certified_partners": running_c,
            }
        )
    return series


def _build_top_partners_by_revenue(partners_qs, core, filters, limit=5):
    """Aggregate ARR contributed by each Partner's linked Accounts and return top N partners."""
    partner_map = {p.id: p for p in partners_qs}
    if not partner_map:
        return []

    cust_counts = dict(
        Account.objects.filter(Is_Deleted=False, Partner_Id_id__in=partner_map.keys())
        .values("Partner_Id_id")
        .annotate(total=Count("id"))
        .values_list("Partner_Id_id", "total")
    )

    paying_subs = list(
        core["subs_qs"]
        .filter(status__icontains="active")
        .exclude(status__icontains="inactive")
        .filter(_paying_subscription_q(), Customer_Id__Partner_Id_id__in=partner_map.keys(), Created_Date__lte=filters["end_dt"])
        .select_related("Customer_Id", "Plan_Id")
    )

    rev_by_partner = {pid: 0.0 for pid in partner_map}
    for sub in paying_subs:
        pid = sub.Customer_Id.Partner_Id_id if sub.Customer_Id else None
        if pid in rev_by_partner:
            rev_by_partner[pid] += _sub_monthly_amount(sub) * 12.0

    total_partner_rev = sum(rev_by_partner.values())
    ranked = sorted(
        partner_map.values(),
        key=lambda p: (rev_by_partner.get(p.id, 0.0), cust_counts.get(p.id, 0)),
        reverse=True,
    )[:limit]

    rows = []
    for idx, partner in enumerate(ranked, start=1):
        rev = round(rev_by_partner.get(partner.id, 0.0), 2)
        contrib = round((rev / total_partner_rev) * 100, 1) if total_partner_rev > 0 else 0.0
        rows.append(
            {
                "rank": idx,
                "partner_id": partner.id,
                "partner_name": partner.Trade_Name or partner.Legal_Name or f"Partner #{partner.id}",
                "partner_type": partner.Tier or partner.Partner_Type or "Standard",
                "customers_count": cust_counts.get(partner.id, 0),
                "revenue": rev,
                "revenue_formatted": _format_inr(rev),
                "contribution_pct": contrib,
            }
        )
    return rows


def build_partner_kpi_dashboard(filters):
    """Build API 2 response: Partner KPIs, Acquisition & Certification Trend, Segmentation, Metrics, Top 5 Partners."""
    core = _compute_core_metrics(filters)
    partners_qs = core["partners_qs"]
    cert_qs = _partner_cert_qs(partners_qs)

    end_dt = filters["end_dt"]
    prev_end_dt = filters["prev_end_dt"]

    total_partners = partners_qs.filter(Created_Date__lte=end_dt).count()
    prev_total_partners = partners_qs.filter(Created_Date__lte=prev_end_dt).count()

    active_partners = core["active_partners"]
    prev_active_partners = core["prev_active_partners"]

    certified_partners = cert_qs.filter(Created_Date__lte=end_dt).values("Partner_id").distinct().count()
    prev_certified_partners = cert_qs.filter(Created_Date__lte=prev_end_dt).values("Partner_id").distinct().count()

    new_partners = partners_qs.filter(Created_Date__gte=filters["start_dt"], Created_Date__lte=end_dt).count()
    prev_new_partners = partners_qs.filter(Created_Date__gte=filters["prev_start_dt"], Created_Date__lte=prev_end_dt).count()

    certified_ids = set(cert_qs.filter(Created_Date__lte=end_dt).values_list("Partner_id", flat=True))
    in_training_count = (
        ModuleEnrollment.objects.filter(
            Is_Deleted=False,
            Partner_id__in=partners_qs.values_list("id", flat=True),
        )
        .filter(Q(Status__icontains="progress") | Q(Status__icontains="started"))
        .exclude(Partner_id__in=certified_ids)
        .values("Partner_id")
        .distinct()
        .count()
    )
    inactive_partners = partners_qs.filter(
        Q(Status__icontains="inactive") | Q(Status__icontains="suspend") | Q(Status__icontains="reject")
    ).count()

    def _pct(val, denom):
        return round((val / denom) * 100, 1) if denom > 0 else 0.0

    cert_rate = _pct(certified_partners, total_partners)
    prev_cert_rate = _pct(prev_certified_partners, prev_total_partners)

    activation_rate = _pct(active_partners, total_partners)
    prev_activation_rate = _pct(prev_active_partners, prev_total_partners)

    retention_rate = _pct(max(0, total_partners - inactive_partners), total_partners)
    prev_inactive = partners_qs.filter(Created_Date__lte=prev_end_dt).filter(
        Q(Status__icontains="inactive") | Q(Status__icontains="suspend") | Q(Status__icontains="reject")
    ).count()
    prev_retention_rate = _pct(max(0, prev_total_partners - prev_inactive), prev_total_partners)

    return {
        "filters_applied": _build_filters_summary(filters),
        "partner_kpis": {
            "total_partners": {
                "value": total_partners,
                **_calc_growth(total_partners, prev_total_partners),
            },
            "active_partners": {
                "value": active_partners,
                **_calc_growth(active_partners, prev_active_partners),
            },
            "certified_partners": {
                "value": certified_partners,
                **_calc_growth(certified_partners, prev_certified_partners),
            },
            "new_partners": {
                "value": new_partners,
                **_calc_growth(new_partners, prev_new_partners),
            },
        },
        "partner_acquisition_and_certification_trend": {
            "monthly_data": _build_partner_trend(partners_qs, cert_qs, filters),
        },
        "partner_segmentation": {
            "total_partners": total_partners,
            "segments": [
                {"key": "active", "label": "Active", "count": active_partners, "pct": _pct(active_partners, total_partners)},
                {"key": "certified", "label": "Certified", "count": certified_partners, "pct": _pct(certified_partners, total_partners)},
                {"key": "in_training", "label": "In Training", "count": in_training_count, "pct": _pct(in_training_count, total_partners)},
                {"key": "inactive", "label": "Inactive", "count": inactive_partners, "pct": _pct(inactive_partners, total_partners)},
            ],
        },
        "key_metrics": {
            "partner_certification_rate": {
                "rate": cert_rate,
                "pp_change": round(cert_rate - prev_cert_rate, 1),
            },
            "partner_activation_rate": {
                "rate": activation_rate,
                "pp_change": round(activation_rate - prev_activation_rate, 1),
            },
            "partner_retention_rate": {
                "rate": retention_rate,
                "pp_change": round(retention_rate - prev_retention_rate, 1),
            },
        },
        "top_partners": _build_top_partners_by_revenue(partners_qs, core, filters, limit=5),
    }
