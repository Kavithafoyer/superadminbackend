"""Service layer for SuperAdmin Business Overview and Product-wise Performance dashboards."""

from datetime import date, datetime, time, timedelta
import shutil
import time as time_mod
from urllib.parse import urlparse

from django.conf import settings
from django.db import connections
from django.db.models import Count, FloatField, Q, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone

from CRMSuperAdmin.models import (
    Account,
    Additionallicenserequest,
    Additionalstoragerequest,
    Addsubscriptionrequest,
    Cancelplans,
    InstanceRequest,
    Instance_Creation,
    InvoiceLineItem,
    ProductMaster,
    Renewal,
    Subscriptions,
    TicketManagement,
    UserActivity,
)
from CRMSuperAdmin.services.customer_overview_service import parse_positive_int
from partner.models import KycRecord, Partner, PartnerApplication
from partneracademy.models import Certificate

CLOSED_TICKET_STATUSES = ("fixed", "closed", "resolved")


def _to_aware_datetime(dt):
    """Align naive datetime with Django USE_TZ setting."""
    if getattr(settings, "USE_TZ", True) and timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


def _subtract_months(year, month, offset):
    """Return (year, month) offset months earlier."""
    total_months = year * 12 + (month - 1) - offset
    return total_months // 12, (total_months % 12) + 1


def _build_month_slots(start_date, end_date):
    """Build ordered list of (year, month) tuples from start_date to end_date inclusive."""
    slots = []
    yr, mo = start_date.year, start_date.month
    while (yr, mo) <= (end_date.year, end_date.month):
        slots.append((yr, mo))
        if mo == 12:
            yr += 1
            mo = 1
        else:
            mo += 1
    return slots


def _format_inr(amount):
    """Format INR currency into human-readable Cr / L / standard comma string."""
    val = float(amount or 0)
    if val >= 10_000_000:
        return f"₹ {val / 10_000_000:.2f} Cr"
    if val >= 100_000:
        return f"₹ {val / 100_000:.1f} L"
    return f"₹ {round(val):,}"


def _calc_growth(current, previous):
    """Compute growth percentage and direction between current and previous values."""
    cur = float(current or 0)
    prev = float(previous or 0)
    if prev > 0:
        pct = round(((cur - prev) / prev) * 100, 1)
    elif cur > 0:
        pct = 100.0
    else:
        pct = 0.0
    direction = "up" if pct > 0 else ("down" if pct < 0 else "flat")
    sign = "+" if pct > 0 else ""
    display_pct = int(pct) if pct == int(pct) else pct
    return {
        "growth_pct": display_pct,
        "direction": direction,
        "growth_label": f"{sign}{display_pct}%",
    }


def parse_dashboard_filters(query_params):
    """Parse and validate global dashboard filter bar parameters using integer PKs."""
    now_dt = timezone.now()
    today = now_dt.date()

    raw_from = (query_params.get("from_date") or "").strip()
    raw_to = (query_params.get("to_date") or "").strip()
    raw_range = (query_params.get("date_range") or "").strip().lower()

    if raw_range == "custom" or raw_from or raw_to:
        if not raw_from and not raw_to:
            raise ValueError("from_date and to_date are required when date_range is 'custom'.")
        try:
            end_date = datetime.strptime(raw_to, "%Y-%m-%d").date() if raw_to else today
            start_date = (
                datetime.strptime(raw_from, "%Y-%m-%d").date()
                if raw_from
                else date(end_date.year, end_date.month, 1)
            )
        except ValueError as exc:
            raise ValueError("from_date and to_date must be in YYYY-MM-DD format.") from exc
        if start_date > end_date:
            raise ValueError("from_date cannot be after to_date.")
        normalized_range = "custom"
    elif raw_range in ("last_30_days", "30d"):
        start_date = today - timedelta(days=30)
        end_date = today
        normalized_range = "last_30_days"
    elif raw_range in ("last_90_days", "90d"):
        start_date = today - timedelta(days=90)
        end_date = today
        normalized_range = "last_90_days"
    elif raw_range in ("this_year", "ytd"):
        start_date = date(today.year, 1, 1)
        end_date = today
        normalized_range = "this_year"
    else:
        first_y, first_m = _subtract_months(today.year, today.month, 11)
        start_date = date(first_y, first_m, 1)
        end_date = today
        normalized_range = "last_12_months"

    raw_product_id = query_params.get("product_id")
    product_id = None
    if raw_product_id not in (None, "") and str(raw_product_id).strip().lower() not in ("all", "0"):
        product_id = parse_positive_int(raw_product_id, "product_id")

    raw_partner_id = query_params.get("partner_id")
    partner_id = None
    if raw_partner_id not in (None, "") and str(raw_partner_id).strip().lower() not in ("all", "0"):
        partner_id = parse_positive_int(raw_partner_id, "partner_id")

    raw_country = (query_params.get("country") or "").strip()
    country = None if raw_country.lower() in ("", "all", "all regions", "all countries") else raw_country

    raw_cust_type = (query_params.get("customer_type") or "all").strip().lower()
    if raw_cust_type not in ("all", "direct", "partner", "free", "paying", "trial"):
        raise ValueError("customer_type must be one of: all, direct, partner, free, paying, trial.")

    raw_partner_type = (query_params.get("partner_type") or "").strip()
    partner_type = None if raw_partner_type.lower() in ("", "all", "all partners", "all partner types") else raw_partner_type

    span_days = max(1, (end_date - start_date).days)
    prev_end_date = start_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=span_days)

    return {
        "date_range": normalized_range,
        "start_date": start_date,
        "end_date": end_date,
        "start_dt": _to_aware_datetime(datetime.combine(start_date, time.min)),
        "end_dt": _to_aware_datetime(datetime.combine(end_date, time.max)),
        "prev_start_date": prev_start_date,
        "prev_end_date": prev_end_date,
        "prev_start_dt": _to_aware_datetime(datetime.combine(prev_start_date, time.min)),
        "prev_end_dt": _to_aware_datetime(datetime.combine(prev_end_date, time.max)),
        "product_id": product_id,
        "partner_id": partner_id,
        "partner_type": partner_type,
        "country": country,
        "customer_type": raw_cust_type,
    }


def _apply_account_scope(qs, filters, prefix=""):
    """Apply product_id, partner_id, partner_type, country, and customer_type filters via icontains onto Account."""
    if filters["product_id"] is not None:
        qs = qs.filter(**{f"{prefix}Product_Id_id": filters["product_id"]})
    if filters["partner_id"] is not None:
        qs = qs.filter(**{f"{prefix}Partner_Id_id": filters["partner_id"]})
    if filters.get("partner_type"):
        pt = filters["partner_type"]
        qs = qs.filter(
            Q(**{f"{prefix}Partner_Id__Tier__icontains": pt})
            | Q(**{f"{prefix}Partner_Id__Partner_Type__icontains": pt})
        )
    if filters["country"]:
        qs = qs.filter(**{f"{prefix}Country__icontains": filters["country"]})
    if filters["customer_type"] == "direct":
        qs = qs.filter(**{f"{prefix}Partner_Id__isnull": True})
    elif filters["customer_type"] == "partner":
        qs = qs.filter(**{f"{prefix}Partner_Id__isnull": False})
    return qs


def _free_subscription_q():
    """Match free non-trial subscriptions using icontains on Plantype or zero amount."""
    return Q(is_trial=False) & (Q(SuscriptionAmount__lte=0) | Q(Plan_Id__Plantype__icontains="free"))


def _paying_subscription_q():
    """Match active paying subscriptions."""
    return Q(is_trial=False, SuscriptionAmount__gt=0)


def _trial_subscription_q():
    """Match trial subscriptions using icontains."""
    return Q(status__icontains="trial") | Q(is_trial=True)


def _active_subscription_qs(filters):
    """Build filtered Subscriptions queryset with active/trial/customer_type scoping."""
    qs = Subscriptions.objects.select_related("Product_Id", "Plan_Id", "Customer_Id").filter(
        Is_Deleted=False
    ).exclude(Is_Archived=True)
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
    if filters["customer_type"] == "direct":
        qs = qs.filter(Customer_Id__Partner_Id__isnull=True)
    elif filters["customer_type"] == "partner":
        qs = qs.filter(Customer_Id__Partner_Id__isnull=False)
    elif filters["customer_type"] == "free":
        qs = qs.filter(_free_subscription_q())
    elif filters["customer_type"] == "paying":
        qs = qs.filter(_paying_subscription_q())
    elif filters["customer_type"] == "trial":
        qs = qs.filter(_trial_subscription_q())
    return qs


def _filtered_accounts_qs(filters):
    """Build filtered Account queryset."""
    qs = Account.objects.filter(Is_Deleted=False)
    qs = _apply_account_scope(qs, filters)
    if filters["customer_type"] in ("free", "paying", "trial"):
        sub_ids = _active_subscription_qs(filters).values_list("Customer_Id_id", flat=True).distinct()
        qs = qs.filter(id__in=sub_ids)
    return qs


def _filtered_instances_qs(filters):
    """Build filtered Instance_Creation queryset."""
    qs = Instance_Creation.objects.select_related("Product_Id", "Customer_Id", "Subscription_Id").filter(
        Is_Deleted=False
    )
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
    if filters["customer_type"] == "direct":
        qs = qs.filter(Customer_Id__Partner_Id__isnull=True)
    elif filters["customer_type"] == "partner":
        qs = qs.filter(Customer_Id__Partner_Id__isnull=False)
    elif filters["customer_type"] in ("free", "paying", "trial"):
        sub_ids = _active_subscription_qs(filters).values_list("id", flat=True)
        qs = qs.filter(Subscription_Id_id__in=sub_ids)
    return qs


def _filtered_partners_qs(filters):
    """Build filtered Partner queryset using icontains."""
    qs = Partner.objects.filter(Is_Deleted=False)
    if filters["partner_id"] is not None:
        qs = qs.filter(id=filters["partner_id"])
    if filters.get("partner_type"):
        pt = filters["partner_type"]
        qs = qs.filter(Q(Tier__icontains=pt) | Q(Partner_Type__icontains=pt))
    if filters["country"]:
        qs = qs.filter(Country__icontains=filters["country"])
    if filters["product_id"] is not None:
        prod = ProductMaster.objects.filter(pk=filters["product_id"]).first()
        if prod:
            prod_q = Q(Products__icontains=str(prod.id))
            if prod.Product_Code:
                prod_q |= Q(Products__icontains=prod.Product_Code)
            if prod.Product_Name:
                prod_q |= Q(Products__icontains=prod.Product_Name)
            qs = qs.filter(prod_q)
    return qs


def _sub_monthly_amount(sub):
    """Normalize a subscription's recurring amount into monthly value (MRR)."""
    amount = float(sub.SuscriptionAmount or 0)
    if amount <= 0:
        return 0.0
    period = (sub.SubscriptionPeriod or "").strip().lower()
    cycle = (sub.Plan_Id.billing_cycle if sub.Plan_Id and sub.Plan_Id.billing_cycle else "").strip().lower()
    if "year" in period or "annual" in period or "year" in cycle:
        return amount / 12.0
    return amount


def _compute_mrr_arr_from_subs(subs_iterable):
    """Return (mrr, arr) from an iterable of active paying Subscriptions."""
    mrr = sum(_sub_monthly_amount(s) for s in subs_iterable)
    return round(mrr, 2), round(mrr * 12.0, 2)


def _filtered_addon_line_items_qs(filters, start_dt, end_dt, product_id=None):
    """Build filtered InvoiceLineItem queryset for paid add-ons using icontains."""
    line_qs = InvoiceLineItem.objects.filter(
        Is_Deleted=False,
        Invoice_Id__Is_Deleted=False,
        Item_Type__icontains="addon",
        Invoice_Id__Payment_Status__icontains="paid",
        Invoice_Id__Invoice_Date__gte=start_dt,
        Invoice_Id__Invoice_Date__lte=end_dt,
    )
    effective_product = product_id if product_id is not None else filters["product_id"]
    if effective_product is not None:
        line_qs = line_qs.filter(Product_Id_id=effective_product)
    if filters["partner_id"] is not None:
        line_qs = line_qs.filter(Invoice_Id__Customer_Id__Partner_Id_id=filters["partner_id"])
    if filters["country"]:
        line_qs = line_qs.filter(Invoice_Id__Customer_Id__Country__icontains=filters["country"])
    return line_qs


def _compute_addon_revenue(filters, start_dt, end_dt, product_id=None):
    """Compute paid add-on revenue from InvoiceLineItem with Addsubscriptionrequest fallback."""
    line_qs = _filtered_addon_line_items_qs(filters, start_dt, end_dt, product_id=product_id)
    effective_product = product_id if product_id is not None else filters["product_id"]

    total = float(
        line_qs.aggregate(total=Coalesce(Sum("TotalAmount"), 0.0, output_field=FloatField()))["total"]
        or 0.0
    )
    if total > 0:
        return round(total, 2)

    req_qs = Addsubscriptionrequest.objects.filter(
        Paymentsflg=True,
        RequestDate__gte=start_dt.date(),
        RequestDate__lte=end_dt.date(),
    )
    if effective_product is not None:
        req_qs = req_qs.filter(Product_Id_id=effective_product)
    if filters["partner_id"] is not None:
        req_qs = req_qs.filter(Customer_Id__Partner_Id_id=filters["partner_id"])
    if filters["country"]:
        req_qs = req_qs.filter(Customer_Id__Country__icontains=filters["country"])
    fallback = float(
        req_qs.aggregate(total=Coalesce(Sum("addonTotalAmount"), 0.0, output_field=FloatField()))["total"]
        or 0.0
    )
    return round(fallback, 2)


def _compute_pending_approvals(filters):
    """Aggregate pending approvals across onboarding, KYC, instances, renewals, and add-ons."""
    partner_apps = PartnerApplication.objects.filter(Is_Deleted=False).filter(
        Q(status__icontains="submitted") | Q(status__icontains="pending") | Q(status__icontains="under_review")
    )
    kyc_pending = KycRecord.objects.filter(Is_Deleted=False).filter(
        Q(status__icontains="pending") | Q(status__icontains="submitted")
    )
    inst_pending = InstanceRequest.objects.filter(Is_Deleted=False, InstanceCreatedFlag=False)
    renewals_pending = Renewal.objects.filter(Is_Deleted=False, Renewal_Status__icontains="pending")
    cancels_pending = Cancelplans.objects.filter(Is_Deleted=False, status=False)
    addon_reqs = Addsubscriptionrequest.objects.filter(Paymentsflg=False)
    license_reqs = Additionallicenserequest.objects.filter(Paymentsflg=False)
    storage_reqs = Additionalstoragerequest.objects.filter(Paymentsflg=False)

    if filters["product_id"] is not None:
        pid = filters["product_id"]
        inst_pending = inst_pending.filter(Product_Id_id=pid)
        renewals_pending = renewals_pending.filter(Product_Id_id=pid)
        cancels_pending = cancels_pending.filter(Product_Id_id=pid)
        addon_reqs = addon_reqs.filter(Product_Id_id=pid)
        license_reqs = license_reqs.filter(Product_Id_id=pid)
        storage_reqs = storage_reqs.filter(Product_Id_id=pid)

    if filters["country"]:
        partner_apps = partner_apps.filter(country__icontains=filters["country"])
        renewals_pending = renewals_pending.filter(Customer_Id__Country__icontains=filters["country"])
        addon_reqs = addon_reqs.filter(Country__icontains=filters["country"])
        license_reqs = license_reqs.filter(Country__icontains=filters["country"])
        storage_reqs = storage_reqs.filter(Country__icontains=filters["country"])

    breakdown = {
        "partner_applications": partner_apps.count(),
        "kyc_records": kyc_pending.count(),
        "instance_requests": inst_pending.count(),
        "renewals": renewals_pending.count(),
        "cancellations": cancels_pending.count(),
        "addon_requests": addon_reqs.count(),
        "license_requests": license_reqs.count(),
        "storage_requests": storage_reqs.count(),
    }
    return sum(breakdown.values()), breakdown


def _compute_open_tickets(filters):
    """Count open support tickets excluding closed/fixed/resolved using icontains."""
    qs = TicketManagement.objects.filter(Is_Deleted=False)
    for closed in CLOSED_TICKET_STATUSES:
        qs = qs.exclude(Ticket_Status__icontains=closed)
    if filters["partner_id"] is not None:
        qs = qs.filter(Partner_Id_id=filters["partner_id"])
    return qs.count()


def get_system_health():
    """Inspect live PostgreSQL, application storage, and Redis/Celery queue health."""
    now_dt = timezone.now()
    services = []

    # 1. Web Application (Portal)
    disk_pct = None
    try:
        usage = shutil.disk_usage(settings.BASE_DIR)
        disk_pct = round((usage.used / usage.total) * 100) if usage.total else None
    except Exception:
        disk_pct = None

    latest_activity = UserActivity.objects.order_by("-created_at").values_list("created_at", flat=True).first()
    services.append(
        {
            "service_name": "Web Application (Portal)",
            "status": "Healthy",
            "last_heartbeat": (latest_activity or now_dt).isoformat(),
            "api_error_rate": None,
            "avg_latency_ms": None,
            "db_connections": None,
            "queue_backlog": None,
            "storage_utilization_pct": disk_pct,
            "alert_severity": "Low",
            "instrumented": False,
        }
    )

    # 2. API Gateway (Uninstrumented until gateway/middleware telemetry is added)
    services.append(
        {
            "service_name": "API Gateway",
            "status": "Uninstrumented",
            "last_heartbeat": now_dt.isoformat(),
            "api_error_rate": None,
            "avg_latency_ms": None,
            "db_connections": None,
            "queue_backlog": None,
            "storage_utilization_pct": None,
            "alert_severity": "Low",
            "instrumented": False,
        }
    )

    # 3. Database (PostgreSQL) — live connection check, latency, active connections & DB size
    db_status = "Healthy"
    db_latency_ms = None
    db_connections_str = None
    db_storage_pct = disk_pct
    db_severity = "Low"
    try:
        t0 = time_mod.perf_counter()
        conn = connections["default"]
        with conn.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();")
            active_conns = int(cursor.fetchone()[0])
            cursor.execute("SHOW max_connections;")
            max_conns = int(cursor.fetchone()[0])
            db_connections_str = f"{active_conns} / {max_conns}"
        db_latency_ms = round((time_mod.perf_counter() - t0) * 1000, 1)
        if active_conns > max_conns * 0.85:
            db_severity = "High"
            db_status = "Degraded"
    except Exception:
        db_status = "Down"
        db_severity = "High"

    # Optional Celery / Redis queue check
    queue_backlog = None
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")
    if broker_url and "redis" in broker_url:
        try:
            import redis

            parsed = urlparse(broker_url)
            client = redis.Redis(
                host=parsed.hostname or "127.0.0.1",
                port=parsed.port or 6379,
                db=int((parsed.path or "/0").lstrip("/") or 0),
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            queue_backlog = int(client.llen("celery"))
        except Exception:
            queue_backlog = None

    services.append(
        {
            "service_name": "Database (PostgreSQL)",
            "status": db_status,
            "last_heartbeat": timezone.now().isoformat(),
            "api_error_rate": None,
            "avg_latency_ms": db_latency_ms,
            "db_connections": db_connections_str,
            "queue_backlog": queue_backlog,
            "storage_utilization_pct": db_storage_pct,
            "alert_severity": db_severity,
            "instrumented": True,
        }
    )

    return {
        "last_updated": timezone.now().isoformat(),
        "services": services,
    }


def _compute_core_metrics(filters):
    """Compute core tenant, partner, and revenue counts shared across dashboards."""
    accounts_qs = _filtered_accounts_qs(filters)
    instances_qs = _filtered_instances_qs(filters)
    subs_qs = _active_subscription_qs(filters)
    partners_qs = _filtered_partners_qs(filters)

    end_dt = filters["end_dt"]
    prev_end_dt = filters["prev_end_dt"]

    total_tenants = accounts_qs.filter(Created_Date__lte=filters["end_date"]).count()
    prev_total_tenants = accounts_qs.filter(Created_Date__lte=filters["prev_end_date"]).count()

    active_instances_qs = instances_qs.filter(status__icontains="active").exclude(status__icontains="inactive")
    active_tenants = (
        active_instances_qs.filter(Created_Date__lte=end_dt)
        .values("Customer_Id_id")
        .distinct()
        .count()
    )
    prev_active_tenants = (
        active_instances_qs.filter(Created_Date__lte=prev_end_dt)
        .values("Customer_Id_id")
        .distinct()
        .count()
    )

    active_sub_records = (
        subs_qs.filter(Q(status__icontains="active") | Q(status__icontains="trial"))
        .exclude(status__icontains="inactive")
    )

    free_core_tenants = (
        active_sub_records.filter(_free_subscription_q(), Created_Date__lte=end_dt)
        .values("Customer_Id_id")
        .distinct()
        .count()
    )
    prev_free_core_tenants = (
        active_sub_records.filter(_free_subscription_q(), Created_Date__lte=prev_end_dt)
        .values("Customer_Id_id")
        .distinct()
        .count()
    )

    paying_sub_qs = active_sub_records.filter(status__icontains="active").exclude(
        status__icontains="inactive"
    ).filter(_paying_subscription_q())
    paying_tenants = paying_sub_qs.filter(Created_Date__lte=end_dt).values("Customer_Id_id").distinct().count()
    prev_paying_tenants = (
        paying_sub_qs.filter(Created_Date__lte=prev_end_dt).values("Customer_Id_id").distinct().count()
    )

    trial_sub_qs = active_sub_records.filter(_trial_subscription_q())
    trial_tenants = trial_sub_qs.filter(Created_Date__lte=end_dt).values("Customer_Id_id").distinct().count()
    prev_trial_tenants = (
        trial_sub_qs.filter(Created_Date__lte=prev_end_dt).values("Customer_Id_id").distinct().count()
    )

    active_partners_qs = partners_qs.filter(
        Q(Status__icontains="active") | Q(Status__icontains="approved")
    ).exclude(Status__icontains="inactive")
    active_partners = active_partners_qs.filter(Created_Date__lte=end_dt).count()
    prev_active_partners = active_partners_qs.filter(Created_Date__lte=prev_end_dt).count()

    cert_qs = Certificate.objects.filter(Is_Deleted=False, Status__icontains="issued").filter(
        Q(Expiry_Date__isnull=True) | Q(Expiry_Date__gte=timezone.now())
    )
    if filters["partner_id"] is not None:
        cert_qs = cert_qs.filter(Partner_id=filters["partner_id"])
    if filters["country"]:
        cert_qs = cert_qs.filter(Partner__Country__icontains=filters["country"])
    certified_partners = cert_qs.filter(Created_Date__lte=end_dt).values("Partner_id").distinct().count()
    prev_certified_partners = cert_qs.filter(Created_Date__lte=prev_end_dt).values("Partner_id").distinct().count()

    current_paying_subs = list(paying_sub_qs.filter(Created_Date__lte=end_dt))
    prev_paying_subs = list(paying_sub_qs.filter(Created_Date__lte=prev_end_dt))
    mrr, arr = _compute_mrr_arr_from_subs(current_paying_subs)
    prev_mrr, prev_arr = _compute_mrr_arr_from_subs(prev_paying_subs)

    addon_rev = _compute_addon_revenue(filters, filters["start_dt"], end_dt)
    prev_addon_rev = _compute_addon_revenue(filters, filters["prev_start_dt"], prev_end_dt)

    return {
        "accounts_qs": accounts_qs,
        "instances_qs": instances_qs,
        "active_instances_qs": active_instances_qs,
        "subs_qs": subs_qs,
        "partners_qs": partners_qs,
        "active_partners_qs": active_partners_qs,
        "total_tenants": total_tenants,
        "prev_total_tenants": prev_total_tenants,
        "active_tenants": active_tenants,
        "prev_active_tenants": prev_active_tenants,
        "free_core_tenants": free_core_tenants,
        "prev_free_core_tenants": prev_free_core_tenants,
        "paying_tenants": paying_tenants,
        "prev_paying_tenants": prev_paying_tenants,
        "trial_tenants": trial_tenants,
        "prev_trial_tenants": prev_trial_tenants,
        "active_partners": active_partners,
        "prev_active_partners": prev_active_partners,
        "certified_partners": certified_partners,
        "prev_certified_partners": prev_certified_partners,
        "mrr": mrr,
        "prev_mrr": prev_mrr,
        "arr": arr,
        "prev_arr": prev_arr,
        "addon_rev": addon_rev,
        "prev_addon_rev": prev_addon_rev,
    }


def _build_monthly_customer_growth(accounts_qs, filters):
    """Build cumulative monthly registered tenant series."""
    slots = _build_month_slots(filters["start_date"], filters["end_date"])
    baseline = accounts_qs.filter(Created_Date__lt=filters["start_date"]).count()
    rows = (
        accounts_qs.filter(Created_Date__gte=filters["start_date"], Created_Date__lte=filters["end_date"])
        .annotate(month=TruncMonth("Created_Date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    by_ym = {(r["month"].year, r["month"].month): r["total"] for r in rows if r.get("month")}

    running = baseline
    series = []
    for yr, mo in slots:
        running += by_ym.get((yr, mo), 0)
        series.append(
            {
                "month": date(yr, mo, 1).strftime("%b"),
                "year_month": f"{yr:04d}-{mo:02d}",
                "total_tenants": running,
            }
        )
    return series


def _build_product_adoption_donut(active_instances_qs, total_active_tenants):
    """Group active tenants by ProductMaster PK for donut chart without duplicate rows."""
    instances = list(
        active_instances_qs.filter(Customer_Id_id__isnull=False).select_related("Product_Id")
    )
    by_product = {}
    for inst in instances:
        pid = inst.Product_Id_id
        pname = (
            (inst.Product_Id.Product_Name or inst.Product_Id.Product_Code)
            if inst.Product_Id
            else (inst.product_type or "Unassigned")
        )
        if pid not in by_product:
            by_product[pid] = {"product_id": pid, "product_name": pname, "customers": set()}
        by_product[pid]["customers"].add(inst.Customer_Id_id)

    segments = []
    for item in sorted(by_product.values(), key=lambda x: len(x["customers"]), reverse=True):
        cnt = len(item["customers"])
        pct = round((cnt / total_active_tenants) * 100, 1) if total_active_tenants > 0 else 0.0
        segments.append(
            {
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "active_tenants": cnt,
                "pct": pct,
            }
        )
    return {
        "total_active_tenants": total_active_tenants,
        "segments": segments,
    }


def _build_free_to_paid_conversion(core):
    """Build Free -> Engaged -> Converted to Paid funnel metrics."""
    free_core = core["free_core_tenants"]
    free_cust_ids = list(
        core["subs_qs"]
        .filter(Q(status__icontains="active") | Q(status__icontains="trial"))
        .exclude(status__icontains="inactive")
        .filter(_free_subscription_q())
        .values_list("Customer_Id_id", flat=True)
        .distinct()
    )
    engaged_tenants = 0
    if free_cust_ids:
        cutoff = timezone.now() - timedelta(days=30)
        engaged_tenants = (
            UserActivity.objects.filter(
                instance__Customer_Id_id__in=free_cust_ids,
                created_at__gte=cutoff,
            )
            .values("instance__Customer_Id_id")
            .distinct()
            .count()
        )

    converted = (
        core["subs_qs"]
        .filter(status__icontains="active")
        .exclude(status__icontains="inactive")
        .filter(_paying_subscription_q(), previous_subscription__isnull=False)
        .values("Customer_Id_id")
        .distinct()
        .count()
    )
    denominator = free_core + converted
    conversion_rate = round((converted / denominator) * 100, 1) if denominator > 0 else 0.0
    engaged_pct = round((engaged_tenants / free_core) * 100, 1) if free_core > 0 else 0.0
    converted_pct = round((converted / free_core) * 100, 1) if free_core > 0 else conversion_rate

    prev_denom = core["prev_free_core_tenants"] + core["prev_paying_tenants"]
    prev_rate = round((core["prev_paying_tenants"] / prev_denom) * 100, 1) if prev_denom > 0 else 0.0
    pp_change = round(conversion_rate - prev_rate, 1)

    return {
        "free_core_tenants": free_core,
        "engaged_tenants": engaged_tenants,
        "engaged_pct": engaged_pct,
        "converted_to_paid": converted,
        "converted_pct": converted_pct,
        "conversion_rate": conversion_rate,
        "pp_change": pp_change,
    }


def _build_revenue_and_churn_trends(core, filters):
    """Build monthly MRR/ARR trend, partner acquisition, add-on sales, and churn trend."""
    slots = _build_month_slots(filters["start_date"], filters["end_date"])
    paying_subs = list(
        core["subs_qs"]
        .filter(status__icontains="active")
        .exclude(status__icontains="inactive")
        .filter(_paying_subscription_q())
    )

    rev_series = []
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
        rev_series.append(
            {
                "month": date(yr, mo, 1).strftime("%b"),
                "year_month": f"{yr:04d}-{mo:02d}",
                "mrr_cr": round(month_mrr / 10_000_000, 2),
                "arr_cr": round((month_mrr * 12.0) / 10_000_000, 2),
            }
        )

    # Partner acquisition trend (cumulative active partners)
    partner_baseline = core["active_partners_qs"].filter(Created_Date__lt=filters["start_dt"]).count()
    partner_rows = (
        core["active_partners_qs"]
        .filter(Created_Date__gte=filters["start_dt"], Created_Date__lte=filters["end_dt"])
        .annotate(month=TruncMonth("Created_Date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    partner_by_ym = {(r["month"].year, r["month"].month): r["total"] for r in partner_rows if r.get("month")}
    partner_running = partner_baseline
    partner_series = []
    for yr, mo in slots:
        partner_running += partner_by_ym.get((yr, mo), 0)
        partner_series.append(
            {
                "month": date(yr, mo, 1).strftime("%b"),
                "year_month": f"{yr:04d}-{mo:02d}",
                "active_partners": partner_running,
            }
        )

    # Add-on sales monthly bar series (respects product, partner, and country filters)
    addon_rows = (
        _filtered_addon_line_items_qs(filters, filters["start_dt"], filters["end_dt"])
        .annotate(month=TruncMonth("Invoice_Id__Invoice_Date"))
        .values("month")
        .annotate(total=Coalesce(Sum("TotalAmount"), 0.0, output_field=FloatField()))
        .order_by("month")
    )
    addon_by_ym = {(r["month"].year, r["month"].month): float(r["total"] or 0.0) for r in addon_rows if r.get("month")}
    addon_series = [
        {
            "month": date(yr, mo, 1).strftime("%b"),
            "year_month": f"{yr:04d}-{mo:02d}",
            "addon_revenue_cr": round(addon_by_ym.get((yr, mo), 0.0) / 10_000_000, 2),
        }
        for yr, mo in slots
    ]

    # Customer churn trend (%)
    churned_rows = (
        core["subs_qs"]
        .filter(Q(status__icontains="cancel") | Q(status__icontains="expir"))
        .filter(Updated_Date__gte=filters["start_dt"], Updated_Date__lte=filters["end_dt"])
        .annotate(month=TruncMonth("Updated_Date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    churn_by_ym = {(r["month"].year, r["month"].month): r["total"] for r in churned_rows if r.get("month")}
    total_subs_base = max(1, core["subs_qs"].count())
    churn_series = [
        {
            "month": date(yr, mo, 1).strftime("%b"),
            "year_month": f"{yr:04d}-{mo:02d}",
            "churn_pct": round((churn_by_ym.get((yr, mo), 0) / total_subs_base) * 100, 2),
        }
        for yr, mo in slots
    ]
    latest_churn = churn_series[-1]["churn_pct"] if churn_series else 0.0
    prev_churn = churn_series[-2]["churn_pct"] if len(churn_series) >= 2 else latest_churn
    churn_pp_change = round(latest_churn - prev_churn, 1)

    return {
        "subscription_revenue_trend": {
            "latest_mrr_cr": rev_series[-1]["mrr_cr"] if rev_series else 0.0,
            "latest_arr_cr": rev_series[-1]["arr_cr"] if rev_series else 0.0,
            "monthly_data": rev_series,
        },
        "partner_acquisition_trend": {
            **_calc_growth(core["active_partners"], core["prev_active_partners"]),
            "monthly_data": partner_series,
        },
        "addon_sales": {
            **_calc_growth(core["addon_rev"], core["prev_addon_rev"]),
            "latest_addon_cr": round(core["addon_rev"] / 10_000_000, 2),
            "monthly_data": addon_series,
        },
        "customer_churn": {
            "latest_churn_pct": latest_churn,
            "pp_change": churn_pp_change,
            "monthly_data": churn_series,
        },
    }


def build_business_overview_dashboard(filters):
    """Build complete payload for the Business Overview (/dashboard) screen."""
    core = _compute_core_metrics(filters)
    pending_count, pending_breakdown = _compute_pending_approvals(filters)
    open_tickets = _compute_open_tickets(filters)

    kpis = {
        "total_registered_tenants": {
            "value": core["total_tenants"],
            **_calc_growth(core["total_tenants"], core["prev_total_tenants"]),
        },
        "active_tenants": {
            "value": core["active_tenants"],
            **_calc_growth(core["active_tenants"], core["prev_active_tenants"]),
        },
        "free_core_tenants": {
            "value": core["free_core_tenants"],
            **_calc_growth(core["free_core_tenants"], core["prev_free_core_tenants"]),
        },
        "paying_tenants": {
            "value": core["paying_tenants"],
            **_calc_growth(core["paying_tenants"], core["prev_paying_tenants"]),
        },
        "trial_tenants": {
            "value": core["trial_tenants"],
            **_calc_growth(core["trial_tenants"], core["prev_trial_tenants"]),
        },
        "active_partners": {
            "value": core["active_partners"],
            **_calc_growth(core["active_partners"], core["prev_active_partners"]),
        },
        "certified_partners": {
            "value": core["certified_partners"],
            **_calc_growth(core["certified_partners"], core["prev_certified_partners"]),
        },
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
        "addon_revenue": {
            "value": core["addon_rev"],
            "formatted": _format_inr(core["addon_rev"]),
            **_calc_growth(core["addon_rev"], core["prev_addon_rev"]),
        },
        "pending_approvals": {
            "value": pending_count,
            "breakdown": pending_breakdown,
        },
        "open_support_tickets": {
            "value": open_tickets,
        },
    }

    trends = _build_revenue_and_churn_trends(core, filters)
    return {
        "filters_applied": {
            "date_range": filters["date_range"],
            "from_date": str(filters["start_date"]),
            "to_date": str(filters["end_date"]),
            "product_id": filters["product_id"],
            "country": filters["country"],
            "customer_type": filters["customer_type"],
            "partner_id": filters["partner_id"],
        },
        "kpis": kpis,
        "monthly_customer_growth": {
            **_calc_growth(core["total_tenants"], core["prev_total_tenants"]),
            "monthly_data": _build_monthly_customer_growth(core["accounts_qs"], filters),
        },
        "product_wise_adoption": _build_product_adoption_donut(
            core["active_instances_qs"], core["active_tenants"]
        ),
        "free_to_paid_conversion": _build_free_to_paid_conversion(core),
        **trends,
        "system_health": get_system_health(),
    }


def build_product_performance_dashboard(filters):
    """Build complete payload for the Product-wise Performance screen."""
    core = _compute_core_metrics(filters)
    products_qs = ProductMaster.objects.filter(Is_Deleted=False, Is_Active=True).order_by("id")
    if filters["product_id"] is not None:
        products_qs = products_qs.filter(pk=filters["product_id"])

    summary_rows = []
    cutoff_30d = timezone.now() - timedelta(days=30)

    for prod in products_qs:
        p_accounts = core["accounts_qs"].filter(Product_Id_id=prod.id)
        p_instances = core["instances_qs"].filter(Product_Id_id=prod.id)
        p_active_instances = core["active_instances_qs"].filter(Product_Id_id=prod.id)
        p_subs = core["subs_qs"].filter(Product_Id_id=prod.id)

        p_total_tenants = max(
            p_accounts.filter(Created_Date__lte=filters["end_date"]).count(),
            p_instances.filter(Created_Date__lte=filters["end_dt"]).values("Customer_Id_id").distinct().count(),
        )
        p_prev_tenants = max(
            p_accounts.filter(Created_Date__lte=filters["prev_end_date"]).count(),
            p_instances.filter(Created_Date__lte=filters["prev_end_dt"]).values("Customer_Id_id").distinct().count(),
        )

        p_active = p_active_instances.filter(Created_Date__lte=filters["end_dt"]).values("Customer_Id_id").distinct().count()
        p_active_subs = p_subs.filter(Q(status__icontains="active") | Q(status__icontains="trial")).exclude(
            status__icontains="inactive"
        ).filter(Created_Date__lte=filters["end_dt"])
        p_paying_qs = (
            p_active_subs.filter(status__icontains="active")
            .exclude(status__icontains="inactive")
            .filter(_paying_subscription_q())
        )
        p_paying = p_paying_qs.values("Customer_Id_id").distinct().count()
        p_trial = p_active_subs.filter(_trial_subscription_q()).values("Customer_Id_id").distinct().count()
        p_free = p_active_subs.filter(_free_subscription_q()).values("Customer_Id_id").distinct().count()

        p_mrr, p_arr = _compute_mrr_arr_from_subs(list(p_paying_qs))
        p_addon_rev = _compute_addon_revenue(filters, filters["start_dt"], filters["end_dt"], product_id=prod.id)

        p_converted = p_paying_qs.filter(previous_subscription__isnull=False).values("Customer_Id_id").distinct().count()
        conv_denom = p_free + p_trial + p_converted
        p_conversion_pct = round((p_converted / conv_denom) * 100, 1) if conv_denom > 0 else 0.0

        p_total_subs = max(1, p_subs.count())
        p_churned_subs = p_subs.filter(Q(status__icontains="cancel") | Q(status__icontains="expir")).count()
        p_churn_pct = round((p_churned_subs / p_total_subs) * 100, 1)

        p_growth = _calc_growth(p_total_tenants, p_prev_tenants)["growth_pct"]

        licensed_seats = sum(
            (s.Base_Users or (s.Plan_Id.No_Of_Users if s.Plan_Id and s.Plan_Id.No_Of_Users else 0))
            + (s.Additional_users or 0)
            for s in p_active_subs
        )
        active_users_30d = 0
        inst_ids = list(p_active_instances.values_list("id", flat=True))
        if inst_ids:
            active_users_30d = (
                UserActivity.objects.filter(instance_id__in=inst_ids, created_at__gte=cutoff_30d)
                .values("external_user_id")
                .distinct()
                .count()
            )
        p_usage_health = min(100, round((active_users_30d / licensed_seats) * 100)) if licensed_seats > 0 else 0

        summary_rows.append(
            {
                "product_id": prod.id,
                "product_name": prod.Product_Name or prod.Product_Code or f"Product #{prod.id}",
                "product_code": prod.Product_Code,
                "total_tenants": p_total_tenants,
                "active_tenants": p_active,
                "paying_tenants": p_paying,
                "trial_tenants": p_trial,
                "mrr": p_mrr,
                "mrr_lakhs": round(p_mrr / 100_000, 1),
                "arr": p_arr,
                "arr_crores": round(p_arr / 10_000_000, 2),
                "addon_revenue": p_addon_rev,
                "addon_revenue_lakhs": round(p_addon_rev / 100_000, 1),
                "free_to_paid_conversion_pct": p_conversion_pct,
                "churn_pct": p_churn_pct,
                "growth_yoy_pct": p_growth,
                "usage_health_pct": p_usage_health,
            }
        )

    total_row_count = len(summary_rows)
    totals = {
        "total_tenants": sum(r["total_tenants"] for r in summary_rows),
        "active_tenants": sum(r["active_tenants"] for r in summary_rows),
        "paying_tenants": sum(r["paying_tenants"] for r in summary_rows),
        "trial_tenants": sum(r["trial_tenants"] for r in summary_rows),
        "mrr_lakhs": round(sum(r["mrr"] for r in summary_rows) / 100_000, 1),
        "arr_crores": round(sum(r["arr"] for r in summary_rows) / 10_000_000, 2),
        "addon_revenue_lakhs": round(sum(r["addon_revenue"] for r in summary_rows) / 100_000, 1),
        "free_to_paid_conversion_pct": round(
            sum(r["free_to_paid_conversion_pct"] for r in summary_rows) / total_row_count, 1
        )
        if total_row_count
        else 0.0,
        "churn_pct": round(sum(r["churn_pct"] for r in summary_rows) / total_row_count, 1)
        if total_row_count
        else 0.0,
        "growth_yoy_pct": round(sum(r["growth_yoy_pct"] for r in summary_rows) / total_row_count, 1)
        if total_row_count
        else 0.0,
        "usage_health_pct": round(sum(r["usage_health_pct"] for r in summary_rows) / total_row_count)
        if total_row_count
        else 0,
    }

    # Monthly active tenants stacked series by product
    slots = _build_month_slots(filters["start_date"], filters["end_date"])
    monthly_rows = (
        core["active_instances_qs"]
        .filter(Created_Date__gte=filters["start_dt"], Created_Date__lte=filters["end_dt"])
        .annotate(month=TruncMonth("Created_Date"))
        .values("month", "Product_Id_id", "Product_Id__Product_Name")
        .annotate(total=Count("Customer_Id_id", distinct=True))
        .order_by("month")
    )
    by_month_prod = {}
    for row in monthly_rows:
        if row.get("month"):
            by_month_prod[(row["month"].year, row["month"].month, row["Product_Id_id"])] = row["total"]

    running_by_prod = {
        r["product_id"]: core["active_instances_qs"]
        .filter(Product_Id_id=r["product_id"], Created_Date__lt=filters["start_dt"])
        .values("Customer_Id_id")
        .distinct()
        .count()
        for r in summary_rows
    }
    monthly_active_by_product = []
    for yr, mo in slots:
        entry = {"month": date(yr, mo, 1).strftime("%b"), "year_month": f"{yr:04d}-{mo:02d}", "products": []}
        for r in summary_rows:
            pid = r["product_id"]
            running_by_prod[pid] += by_month_prod.get((yr, mo, pid), 0)
            entry["products"].append(
                {
                    "product_id": pid,
                    "product_name": r["product_name"],
                    "active_tenants": running_by_prod[pid],
                }
            )
        monthly_active_by_product.append(entry)

    total_active_for_donut = sum(r["active_tenants"] for r in summary_rows)
    return {
        "filters_applied": {
            "date_range": filters["date_range"],
            "from_date": str(filters["start_date"]),
            "to_date": str(filters["end_date"]),
            "product_id": filters["product_id"],
            "country": filters["country"],
            "customer_type": filters["customer_type"],
            "partner_id": filters["partner_id"],
        },
        "kpis": {
            "total_tenants": {
                "value": core["total_tenants"],
                **_calc_growth(core["total_tenants"], core["prev_total_tenants"]),
            },
            "active_tenants": {
                "value": core["active_tenants"],
                **_calc_growth(core["active_tenants"], core["prev_active_tenants"]),
            },
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
            "addon_revenue": {
                "value": core["addon_rev"],
                "formatted": _format_inr(core["addon_rev"]),
                **_calc_growth(core["addon_rev"], core["prev_addon_rev"]),
            },
        },
        "product_summary_table": {
            "rows": summary_rows,
            "totals": totals,
        },
        "charts": {
            "product_adoption": {
                "total_active_tenants": total_active_for_donut,
                "segments": [
                    {
                        "product_id": r["product_id"],
                        "product_name": r["product_name"],
                        "active_tenants": r["active_tenants"],
                        "pct": round((r["active_tenants"] / total_active_for_donut) * 100, 1)
                        if total_active_for_donut > 0
                        else 0.0,
                    }
                    for r in summary_rows
                ],
            },
            "revenue_by_product_arr": sorted(
                [
                    {
                        "product_id": r["product_id"],
                        "product_name": r["product_name"],
                        "arr_crores": r["arr_crores"],
                    }
                    for r in summary_rows
                ],
                key=lambda x: x["arr_crores"],
                reverse=True,
            ),
            "free_to_paid_conversion_by_product": [
                {
                    "product_id": r["product_id"],
                    "product_name": r["product_name"],
                    "conversion_pct": r["free_to_paid_conversion_pct"],
                }
                for r in summary_rows
            ],
            "monthly_active_tenants_by_product": monthly_active_by_product,
            "product_growth_yoy": [
                {
                    "product_id": r["product_id"],
                    "product_name": r["product_name"],
                    "growth_yoy_pct": r["growth_yoy_pct"],
                }
                for r in summary_rows
            ],
            "customer_churn_by_product": [
                {
                    "product_id": r["product_id"],
                    "product_name": r["product_name"],
                    "churn_pct": r["churn_pct"],
                }
                for r in summary_rows
            ],
        },
    }
