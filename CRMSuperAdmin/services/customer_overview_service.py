"""Service layer for Customer Overview: Usage & Adoption, Customer Health, and Usage Trend."""

from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from CRMSuperAdmin.models import (
    Account,
    Cancelplans,
    Instance_Creation,
    Invoice,
    ModuleMaster,
    Payments,
    PlanFeature,
    PlanLimit,
    Renewal,
    Subscriptions,
    TicketManagement,
    UserActivity,
)

CLOSED_TICKET_STATUSES = ("fixed", "closed", "resolved")
DEFAULT_LOGINS_PER_SEAT_PER_MONTH = 20
DEFAULT_TREND_MONTHS = 12
DEFAULT_PERIOD_DAYS = 30


def parse_positive_int(raw_value, field_name):
    """Parse a positive integer query parameter or raise ValueError."""
    if raw_value is None or str(raw_value).strip() == "":
        raise ValueError(f"{field_name} is required.")
    try:
        parsed = int(str(raw_value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid integer primary key.") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")
    return parsed


def resolve_customer_account(customer_pk):
    """Look up a non-deleted Account strictly by its primary key (id)."""
    return (
        Account.objects.select_related("Organization_Id", "Product_Id")
        .filter(pk=customer_pk, Is_Deleted=False)
        .first()
    )


def _subtract_months(year, month, offset):
    """Return (year, month) offset months earlier."""
    total_months = year * 12 + (month - 1) - offset
    return total_months // 12, (total_months % 12) + 1


def _get_customer_scope(account, product_pk=None):
    """Fetch customer subscriptions, instances, and licensed seat capacity."""
    subs_qs = (
        Subscriptions.objects.select_related("Product_Id", "Plan_Id")
        .prefetch_related("Addtionaluser_Id")
        .filter(Customer_Id_id=account.id, Is_Deleted=False)
        .exclude(Is_Archived=True)
    )
    inst_qs = Instance_Creation.objects.select_related("Product_Id", "Subscription_Id").filter(
        Customer_Id_id=account.id, Is_Deleted=False
    )

    if product_pk is not None:
        subs_qs = subs_qs.filter(Product_Id_id=product_pk)
        inst_qs = inst_qs.filter(Product_Id_id=product_pk)

    active_subs = list(
        subs_qs.filter(Q(status__icontains="active") | Q(status__icontains="trial")).exclude(
            status__icontains="inactive"
        )
    )
    if not active_subs:
        active_subs = list(subs_qs)

    instances = list(inst_qs)

    licensed_seats = 0
    for sub in active_subs:
        base_users = sub.Base_Users or 0
        if base_users == 0 and sub.Plan_Id and sub.Plan_Id.No_Of_Users:
            base_users = sub.Plan_Id.No_Of_Users
        additional_users = sub.Additional_users or 0
        addon_pack_users = sum(
            (item.No_Of_Users or 0)
            for item in sub.Addtionaluser_Id.all()
            if not item.Is_Deleted
        )
        licensed_seats += base_users + additional_users + addon_pack_users

    return {
        "all_subscriptions": subs_qs,
        "active_subscriptions": active_subs,
        "instances": instances,
        "licensed_seats": licensed_seats,
    }


def _detect_product_categories(account, subscriptions, instances):
    """Infer normalized product keys ('education', 'retail', 'it', etc.) for module/label matching."""
    categories = set()

    def _collect(text):
        val = (text or "").strip().lower()
        if not val:
            return
        if "edu" in val or "academy" in val:
            categories.add("education")
        elif "retail" in val:
            categories.add("retail")
        elif "it" in val or "crm" in val:
            categories.add("it")

    for inst in instances:
        _collect(inst.product_type)
        if inst.Product_Id:
            _collect(inst.Product_Id.Product_Code)
            _collect(inst.Product_Id.Product_Name)

    for sub in subscriptions:
        if sub.Product_Id:
            _collect(sub.Product_Id.Product_Code)
            _collect(sub.Product_Id.Product_Name)

    if account.Product_Id:
        _collect(account.Product_Id.Product_Code)
        _collect(account.Product_Id.Product_Name)

    return categories


def _compute_usage_and_adoption(account, subscriptions, instances, licensed_seats, days=DEFAULT_PERIOD_DAYS):
    """Compute Usage & Adoption metrics over the trailing `days` window from UserActivity."""
    now_dt = timezone.now()
    start_dt = now_dt - timedelta(days=days)

    categories = _detect_product_categories(account, subscriptions, instances)
    login_label = "Student Logins" if "education" in categories else "User Logins"

    if instances:
        activity_qs = UserActivity.objects.filter(
            instance__in=instances,
            created_at__gte=start_dt,
            created_at__lte=now_dt,
        )
        active_users = activity_qs.values("external_user_id").distinct().count()
        login_count = activity_qs.filter(action__icontains="login").count()
        used_rows = list(activity_qs.values_list("action", "metadata"))
    else:
        active_users = 0
        login_count = 0
        used_rows = []

    active_users_pct = round((active_users / licensed_seats) * 100) if licensed_seats > 0 else 0

    plan_ids = [sub.Plan_Id_id for sub in subscriptions if sub.Plan_Id_id]
    target_logins = 0
    if plan_ids:
        login_limit = (
            PlanLimit.objects.filter(
                Plan_Id_id__in=plan_ids,
                Is_Active=True,
                Is_Deleted=False,
                Is_Unlimited=False,
                Limit_Value__isnull=False,
            )
            .filter(Q(Limit_Code__icontains="login") | Q(Limit_Name__icontains="login"))
            .order_by("-Limit_Value")
            .first()
        )
        if login_limit and login_limit.Limit_Value:
            target_logins = int(login_limit.Limit_Value)

    if target_logins <= 0 and licensed_seats > 0:
        # Scale default expected logins proportionally with the requested window.
        target_logins = max(1, round(licensed_seats * DEFAULT_LOGINS_PER_SEAT_PER_MONTH * (days / 30.0)))

    login_pct = round((login_count / target_logins) * 100) if target_logins > 0 else 0

    # Determine available key modules from ModuleMaster or included PlanFeatures.
    module_qs = ModuleMaster.objects.filter(Is_active=True, Is_Deleted=False)
    if categories:
        product_q = Q()
        for category in categories:
            product_q |= Q(Product__icontains=category)
        matched_modules = module_qs.filter(product_q)
        total_modules = matched_modules.count() if matched_modules.exists() else module_qs.count()
    else:
        total_modules = module_qs.count()

    if total_modules == 0 and plan_ids:
        total_modules = (
            PlanFeature.objects.filter(
                Plan_Id_id__in=plan_ids,
                Is_Included=True,
                Is_Active=True,
                Is_Deleted=False,
            )
            .values("Feature_Id")
            .distinct()
            .count()
        )

    used_modules = set()
    used_actions = set()
    for action, metadata in used_rows:
        if isinstance(metadata, dict):
            mod_name = (
                metadata.get("module")
                or metadata.get("module_code")
                or metadata.get("module_name")
            )
            if mod_name:
                used_modules.add(str(mod_name).strip().lower())
                continue
        if action:
            used_actions.add(str(action).strip().lower())

    raw_modules_used = len(used_modules) if used_modules else len(used_actions)
    modules_used = min(raw_modules_used, total_modules) if total_modules > 0 else raw_modules_used
    modules_pct = round((modules_used / total_modules) * 100) if total_modules > 0 else 0

    return {
        "active_users": {
            "label": "Active Users",
            "current": active_users,
            "total": licensed_seats,
            "pct": active_users_pct,
        },
        "logins": {
            "label": login_label,
            "current": login_count,
            "total": target_logins,
            "pct": login_pct,
        },
        "key_modules_used": {
            "label": "Key Modules Used",
            "current": modules_used,
            "total": total_modules,
            "pct": modules_pct,
        },
    }


def _count_open_critical_tickets(account, instances):
    """Count open P0-Critical tickets tied to the customer's organization or instances."""
    instance_refs = set()
    for inst in instances:
        for val in (inst.Instance_Request_No, inst.Domain_Name, inst.Database_Name, str(inst.id)):
            if val:
                instance_refs.add(str(val))

    scope_filter = Q()
    if account.Organization_Id_id:
        scope_filter |= Q(Organization_Id_id=account.Organization_Id_id)
    for ref in instance_refs:
        scope_filter |= Q(Instance__icontains=ref)

    if not scope_filter:
        return 0

    tickets = TicketManagement.objects.filter(
        scope_filter,
        Is_Deleted=False,
        Priority__icontains="critical",
    )
    for closed_status in CLOSED_TICKET_STATUSES:
        tickets = tickets.exclude(Ticket_Status__icontains=closed_status)
    return tickets.count()


def _compute_customer_health(account, all_subscriptions, active_subscriptions, instances, usage_data):
    """Compute Customer Health score (0-100), status, and 4 checklist items."""
    adoption_pct = usage_data["active_users"]["pct"]
    high_adoption_passed = adoption_pct >= 75
    adoption_points = round(min(adoption_pct, 100) * 0.35)

    open_critical_tickets = _count_open_critical_tickets(account, instances)
    no_critical_tickets_passed = open_critical_tickets == 0
    ticket_points = 25 if no_critical_tickets_passed else 0

    has_overdue_invoice = (
        Invoice.objects.filter(Customer_Id_id=account.id, Is_Deleted=False, Is_Archived=False)
        .filter(Q(Payment_Status__icontains="overdue") | Q(Payment_Status__icontains="failed"))
        .exists()
    )
    has_overdue_renewal = (
        Renewal.objects.filter(Customer_Id_id=account.id, Is_Deleted=False)
        .filter(Q(Payment_Status__icontains="overdue") | Q(Renewal_Status__icontains="overdue"))
        .exists()
    )
    has_failed_sub_payment = all_subscriptions.filter(
        Q(Last_Payment_Status__icontains="overdue") | Q(Last_Payment_Status__icontains="failed")
    ).exists()
    latest_payment = (
        Payments.objects.filter(Customer_Id_id=account.id, Is_Deleted=False, Is_Archived=False)
        .order_by("-Payment_Date", "-id")
        .first()
    )
    latest_payment_failed = bool(
        latest_payment and (latest_payment.status or "").strip().lower() == "failed"
    )
    on_time_payments_passed = not (
        has_overdue_invoice or has_overdue_renewal or has_failed_sub_payment or latest_payment_failed
    )
    payment_points = 25 if on_time_payments_passed else 0

    has_cancel_request = False
    if account.Organization_Id_id:
        has_cancel_request = Cancelplans.objects.filter(
            OrganizationId_id=account.Organization_Id_id,
            Is_Deleted=False,
            status=False,
        ).exists()

    today = timezone.now().date()
    has_live_subscription = any(
        (sub.status or "").strip().lower() in ("active", "trial")
        and (sub.end_date is None or sub.end_date >= today)
        for sub in active_subscriptions
    )
    renewal_likely_passed = (
        not has_cancel_request
        and has_live_subscription
        and on_time_payments_passed
    )
    renewal_points = 15 if renewal_likely_passed else 0

    score = max(0, min(100, adoption_points + ticket_points + payment_points + renewal_points))
    if score >= 80:
        health_status, health_color = "Healthy", "emerald"
    elif score >= 60:
        health_status, health_color = "Attention", "amber"
    else:
        health_status, health_color = "At Risk", "rose"

    return {
        "score": score,
        "status": health_status,
        "color": health_color,
        "open_critical_tickets": open_critical_tickets,
        "checklist": [
            {"key": "high_adoption", "label": "High Adoption", "passed": high_adoption_passed},
            {
                "key": "no_open_critical_tickets",
                "label": "No Open Critical Tickets",
                "passed": no_critical_tickets_passed,
            },
            {"key": "on_time_payments", "label": "On-time Payments", "passed": on_time_payments_passed},
            {"key": "renewal_likely", "label": "Renewal Likely", "passed": renewal_likely_passed},
        ],
    }


def _to_aware_datetime(dt):
    """Ensure datetime matches Django's USE_TZ configuration."""
    if getattr(settings, "USE_TZ", True) and timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


def _compute_usage_trend(instances, licensed_seats, days=DEFAULT_PERIOD_DAYS, months=DEFAULT_TREND_MONTHS, year=None):
    """Compute monthly active user trend series and period-over-period growth."""
    now_dt = timezone.now()

    if year is not None:
        month_slots = [(year, m) for m in range(1, 13)]
        range_start = _to_aware_datetime(datetime(year, 1, 1))
        range_end = _to_aware_datetime(datetime(year + 1, 1, 1))
    else:
        month_slots = [
            _subtract_months(now_dt.year, now_dt.month, offset)
            for offset in range(months - 1, -1, -1)
        ]
        first_y, first_m = month_slots[0]
        range_start = _to_aware_datetime(datetime(first_y, first_m, 1))
        range_end = now_dt

    counts_by_month = {}
    if instances:
        rows = (
            UserActivity.objects.filter(
                instance__in=instances,
                created_at__gte=range_start,
                created_at__lte=range_end,
            )
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(active_users=Count("external_user_id", distinct=True))
            .order_by("month")
        )
        for row in rows:
            month_dt = row.get("month")
            if month_dt:
                counts_by_month[(month_dt.year, month_dt.month)] = row.get("active_users", 0)

    monthly_data = []
    for yr, mo in month_slots:
        label = datetime(yr, mo, 1).strftime("%b")
        monthly_data.append(
            {
                "month": label,
                "year_month": f"{yr:04d}-{mo:02d}",
                "active_users": counts_by_month.get((yr, mo), 0),
                "target_users": licensed_seats,
            }
        )

    # Period-over-period active user growth: current `days` vs preceding `days`.
    cur_start = now_dt - timedelta(days=days)
    prev_start = cur_start - timedelta(days=days)
    if instances:
        cur_users = (
            UserActivity.objects.filter(instance__in=instances, created_at__gte=cur_start, created_at__lte=now_dt)
            .values("external_user_id")
            .distinct()
            .count()
        )
        prev_users = (
            UserActivity.objects.filter(instance__in=instances, created_at__gte=prev_start, created_at__lt=cur_start)
            .values("external_user_id")
            .distinct()
            .count()
        )
    else:
        cur_users = 0
        prev_users = 0

    if prev_users > 0:
        growth_pct = round(((cur_users - prev_users) / prev_users) * 100)
    elif cur_users > 0:
        growth_pct = 100
    else:
        growth_pct = 0

    if growth_pct > 0:
        direction = "up"
        growth_label = f"+{growth_pct}% vs. previous period"
    elif growth_pct < 0:
        direction = "down"
        growth_label = f"{growth_pct}% vs. previous period"
    else:
        direction = "flat"
        growth_label = "0% vs. previous period"

    max_monthly = max((pt["active_users"] for pt in monthly_data), default=0)
    return {
        "title": "Usage Trend – Active Users",
        "growth_pct": growth_pct,
        "direction": direction,
        "growth_label": growth_label,
        "max_val": max(licensed_seats, max_monthly),
        "monthly_data": monthly_data,
    }


def build_customer_usage_health_overview(account, product_pk=None, days=DEFAULT_PERIOD_DAYS, months=DEFAULT_TREND_MONTHS, year=None):
    """Aggregate Usage & Adoption, Customer Health, and Usage Trend for a given Account."""
    scope = _get_customer_scope(account, product_pk=product_pk)
    usage_and_adoption = _compute_usage_and_adoption(
        account=account,
        subscriptions=scope["active_subscriptions"],
        instances=scope["instances"],
        licensed_seats=scope["licensed_seats"],
        days=days,
    )
    customer_health = _compute_customer_health(
        account=account,
        all_subscriptions=scope["all_subscriptions"],
        active_subscriptions=scope["active_subscriptions"],
        instances=scope["instances"],
        usage_data=usage_and_adoption,
    )
    usage_trend = _compute_usage_trend(
        instances=scope["instances"],
        licensed_seats=scope["licensed_seats"],
        days=days,
        months=months,
        year=year,
    )

    customer_name = (
        account.Organization_Name
        or (account.Organization_Id.Organization_Name if account.Organization_Id else None)
        or account.Contact_Name
        or f"Customer #{account.id}"
    )

    return {
        "customer_id": account.id,
        "account_code": account.Account_Id,
        "customer_name": customer_name,
        "product_id": product_pk,
        "period_days": days,
        "usage_and_adoption": usage_and_adoption,
        "customer_health": customer_health,
        "usage_trend": usage_trend,
    }
