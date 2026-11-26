"""Service layer for the System Health & Alerts dashboard screen."""

from datetime import timedelta
import shutil
import socket
import time as time_mod
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django_celery_results.models import TaskResult

from CRMSuperAdmin.DashboardService.superadmin_dashboard_service import (
    CLOSED_TICKET_STATUSES,
    parse_dashboard_filters,
)
from CRMSuperAdmin.models import (
    AccountMailMaster,
    AuditHistory,
    ProductConfiguration,
    TicketManagement,
    UserActivity,
)
from CRMUserAdmin.models import UserSession
from partner.models import TenantProvisioningJob

User = get_user_model()


def parse_system_health_filters(query_params):
    """Parse date window (defaulting to last_30_days) plus icontains service/status/severity filters."""
    mutable = query_params.copy() if hasattr(query_params, "copy") else dict(query_params)
    if not mutable.get("date_range") and not mutable.get("from_date") and not mutable.get("to_date"):
        mutable["date_range"] = "last_30_days"

    filters = parse_dashboard_filters(mutable)
    service_name = (query_params.get("service_name") or "").strip()
    status_filter = (query_params.get("status") or "").strip()
    severity_filter = (query_params.get("severity") or "").strip()

    filters["service_name"] = None if service_name.lower() in ("", "all") else service_name
    filters["status"] = None if status_filter.lower() in ("", "all") else status_filter
    filters["severity"] = None if severity_filter.lower() in ("", "all") else severity_filter
    return filters


def _tcp_ping_ms(host, port, timeout=1.0):
    """Measure TCP connect round-trip latency in ms, or return None on failure."""
    if not host or not port:
        return None
    t0 = time_mod.perf_counter()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return round((time_mod.perf_counter() - t0) * 1000, 1)
    except Exception:
        return None


def _probe_redis_metrics():
    """Probe Redis broker for ping latency, queue backlog, and memory utilization."""
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")
    if not broker_url or "redis" not in broker_url:
        return {"reachable": False, "latency_ms": None, "queue_backlog": None, "memory_pct": None}
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
        t0 = time_mod.perf_counter()
        client.ping()
        latency_ms = round((time_mod.perf_counter() - t0) * 1000, 1)
        queue_backlog = int(client.llen("celery"))
        info = client.info("memory")
        used_mem = float(info.get("used_memory") or 0)
        max_mem = float(info.get("maxmemory") or info.get("total_system_memory") or 0)
        memory_pct = round((used_mem / max_mem) * 100) if max_mem > 0 else None
        return {
            "reachable": True,
            "latency_ms": latency_ms,
            "queue_backlog": queue_backlog,
            "memory_pct": memory_pct,
        }
    except Exception:
        return {"reachable": False, "latency_ms": None, "queue_backlog": None, "memory_pct": None}


def _get_disk_storage_summary():
    """Inspect real host disk utilization for storage KPI and donut chart."""
    try:
        usage = shutil.disk_usage(settings.BASE_DIR)
        total = float(usage.total or 0)
        used = float(usage.used or 0)
        free = float(usage.free or 0)
        used_pct = round((used / total) * 100, 1) if total > 0 else 0.0
        free_pct = round(100.0 - used_pct, 1) if total > 0 else 0.0
        gb = 1024 ** 3
        tb = 1024 ** 4
        return {
            "used_pct": round(used_pct),
            "free_pct": round(free_pct),
            "used_gb": round(used / gb, 2),
            "free_gb": round(free / gb, 2),
            "total_gb": round(total / gb, 2),
            "used_tb": round(used / tb, 2),
            "free_tb": round(free / tb, 2),
            "total_tb": round(total / tb, 2),
        }
    except Exception:
        return {
            "used_pct": 0,
            "free_pct": 100,
            "used_gb": 0.0,
            "free_gb": 0.0,
            "total_gb": 0.0,
            "used_tb": 0.0,
            "free_tb": 0.0,
            "total_tb": 0.0,
        }


def _build_services_health(filters):
    """Evaluate all 9 platform services from live probes and ORM models."""
    now_dt = timezone.now()
    start_dt = filters["start_dt"]
    end_dt = filters["end_dt"]
    storage = _get_disk_storage_summary()
    redis_info = _probe_redis_metrics()

    # 1. Web Application (Portal) — UserActivity & AuditHistory ORM
    latest_ua = UserActivity.objects.order_by("-created_at").values_list("created_at", flat=True).first()
    audit_qs = AuditHistory.objects.filter(
        Is_Deleted=False, Created_Date__gte=start_dt, Created_Date__lte=end_dt
    )
    audit_total = audit_qs.count()
    audit_errors = audit_qs.filter(
        Q(Action_Status__icontains="fail") | Q(Action_Status__icontains="error")
    ).count()
    portal_err_pct = round((audit_errors / audit_total) * 100, 2) if audit_total > 0 else 0.0
    portal_status = "Degraded" if portal_err_pct >= 2.0 else "Healthy"
    portal_severity = "Medium" if portal_status == "Degraded" else "Low"

    # 2. API Gateway (Uninstrumented unless gateway metrics are pushed)
    gateway_status = "Uninstrumented"

    # 3. Database (PostgreSQL) — Live connection & pg_stat_activity
    db_status = "Healthy"
    db_latency_ms = None
    db_connections_str = None
    db_active = 0
    db_max = 0
    db_severity = "Low"
    try:
        t0 = time_mod.perf_counter()
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();")
            db_active = int(cursor.fetchone()[0])
            cursor.execute("SHOW max_connections;")
            db_max = int(cursor.fetchone()[0])
            db_connections_str = f"{db_active} / {db_max}"
        db_latency_ms = round((time_mod.perf_counter() - t0) * 1000, 1)
        conn_ratio = (db_active / db_max) if db_max > 0 else 0.0
        if conn_ratio >= 0.9:
            db_status, db_severity = "Critical", "High"
        elif conn_ratio >= 0.75 or db_latency_ms > 250:
            db_status, db_severity = "Degraded", "Medium"
    except Exception:
        db_status, db_severity = "Critical", "High"

    # 4. Background Jobs (Celery) — TaskResult ORM + Redis queue
    task_qs = TaskResult.objects.filter(date_done__gte=start_dt, date_done__lte=end_dt)
    task_total = task_qs.count()
    task_failed = task_qs.filter(
        Q(status__icontains="fail") | Q(status__icontains="revok") | Q(status__icontains="error")
    ).count()
    task_err_pct = round((task_failed / task_total) * 100, 2) if task_total > 0 else 0.0
    latest_task_dt = task_qs.order_by("-date_done").values_list("date_done", flat=True).first()
    avg_dur = (
        task_qs.filter(date_started__isnull=False, date_done__isnull=False)
        .annotate(dur=ExpressionWrapper(F("date_done") - F("date_started"), output_field=DurationField()))
        .aggregate(avg=Avg("dur"))["avg"]
    )
    celery_latency_ms = round(avg_dur.total_seconds() * 1000, 1) if avg_dur else None
    backlog = redis_info["queue_backlog"]
    if task_err_pct >= 5.0 or (backlog is not None and backlog > 500):
        celery_status, celery_severity = "Critical", "High"
    elif task_err_pct >= 1.0 or (backlog is not None and backlog > 50):
        celery_status, celery_severity = "Degraded", "Medium"
    elif task_total > 0 or redis_info["reachable"]:
        celery_status, celery_severity = "Healthy", "Low"
    else:
        celery_status, celery_severity = "Uninstrumented", "Low"

    # 5. Cache (Redis)
    if redis_info["reachable"]:
        redis_status = "Degraded" if (redis_info["memory_pct"] or 0) >= 85 else "Healthy"
        redis_severity = "Medium" if redis_status == "Degraded" else "Low"
    else:
        redis_status = "Critical" if getattr(settings, "CELERY_BROKER_URL", "") else "Uninstrumented"
        redis_severity = "High" if redis_status == "Critical" else "Low"

    # 6. File Storage (S3 / Cloudflare R2)
    r2_endpoint = getattr(settings, "R2_ENDPOINT_URL", None) or ""
    r2_host = urlparse(r2_endpoint).hostname if r2_endpoint else None
    storage_latency = _tcp_ping_ms(r2_host, 443) if r2_host else None
    if storage["used_pct"] >= 90:
        storage_status, storage_severity = "Critical", "High"
    elif storage["used_pct"] >= 80:
        storage_status, storage_severity = "Degraded", "Medium"
    else:
        storage_status, storage_severity = "Healthy", "Low"

    # 7. Email / Notification Service — AccountMailMaster ORM + SMTP reachability
    mail_qs = AccountMailMaster.objects.filter(Created_Date__gte=start_dt, Created_Date__lte=end_dt)
    mail_total = mail_qs.count()
    mail_bounced = mail_qs.filter(MailBouned=True).count()
    mail_err_pct = round((mail_bounced / mail_total) * 100, 2) if mail_total > 0 else 0.0
    latest_mail_dt = mail_qs.order_by("-Created_Date").values_list("Created_Date", flat=True).first()
    smtp_latency = _tcp_ping_ms(getattr(settings, "EMAIL_HOST", None), getattr(settings, "EMAIL_PORT", 587))
    if mail_err_pct >= 5.0:
        mail_status, mail_severity = "Critical", "High"
    elif mail_err_pct >= 1.5 or (getattr(settings, "EMAIL_HOST", None) and smtp_latency is None):
        mail_status, mail_severity = "Degraded", "Medium"
    else:
        mail_status, mail_severity = "Healthy", "Low"

    # 8. WhatsApp / Communication API — ProductConfiguration ORM check
    has_wa_config = ProductConfiguration.objects.filter(
        Is_Deleted=False, Is_Active=True, Integrations__icontains="whatsapp"
    ).exists()
    wa_status = "Healthy" if has_wa_config else "Uninstrumented"

    # 9. Identity & Access (SSO / JWT Auth) — User & UserSession ORM
    latest_login = User.objects.filter(is_active=True, last_login__isnull=False).order_by("-last_login").values_list("last_login", flat=True).first()
    active_sessions = UserSession.objects.filter(is_logged_in=True).count()
    auth_status = "Healthy" if (latest_login or active_sessions >= 0) else "Uninstrumented"

    services = [
        {
            "id": 1,
            "service_name": "Web Application (Portal)",
            "status": portal_status,
            "last_heartbeat": (latest_ua or now_dt).isoformat(),
            "api_error_rate_pct": portal_err_pct,
            "avg_latency_ms": None,
            "db_connections": db_connections_str,
            "queue_backlog": None,
            "storage_utilization_pct": storage["used_pct"],
            "alert_severity": portal_severity,
            "instrumented": True,
        },
        {
            "id": 2,
            "service_name": "API Gateway",
            "status": gateway_status,
            "last_heartbeat": now_dt.isoformat(),
            "api_error_rate_pct": None,
            "avg_latency_ms": None,
            "db_connections": None,
            "queue_backlog": None,
            "storage_utilization_pct": None,
            "alert_severity": "Low",
            "instrumented": False,
        },
        {
            "id": 3,
            "service_name": "Database (PostgreSQL)",
            "status": db_status,
            "last_heartbeat": now_dt.isoformat(),
            "api_error_rate_pct": 0.0 if db_status == "Healthy" else None,
            "avg_latency_ms": db_latency_ms,
            "db_connections": db_connections_str,
            "queue_backlog": 0 if db_status == "Healthy" else None,
            "storage_utilization_pct": storage["used_pct"],
            "alert_severity": db_severity,
            "instrumented": True,
        },
        {
            "id": 4,
            "service_name": "Background Jobs (Celery)",
            "status": celery_status,
            "last_heartbeat": (latest_task_dt or now_dt).isoformat(),
            "api_error_rate_pct": task_err_pct,
            "avg_latency_ms": celery_latency_ms,
            "db_connections": None,
            "queue_backlog": backlog,
            "storage_utilization_pct": None,
            "alert_severity": celery_severity,
            "instrumented": True,
        },
        {
            "id": 5,
            "service_name": "Cache (Redis)",
            "status": redis_status,
            "last_heartbeat": now_dt.isoformat(),
            "api_error_rate_pct": 0.0 if redis_info["reachable"] else None,
            "avg_latency_ms": redis_info["latency_ms"],
            "db_connections": None,
            "queue_backlog": backlog,
            "storage_utilization_pct": redis_info["memory_pct"],
            "alert_severity": redis_severity,
            "instrumented": redis_info["reachable"],
        },
        {
            "id": 6,
            "service_name": "File Storage (S3)",
            "status": storage_status,
            "last_heartbeat": now_dt.isoformat(),
            "api_error_rate_pct": 0.0 if storage_status == "Healthy" else None,
            "avg_latency_ms": storage_latency,
            "db_connections": None,
            "queue_backlog": None,
            "storage_utilization_pct": storage["used_pct"],
            "alert_severity": storage_severity,
            "instrumented": True,
        },
        {
            "id": 7,
            "service_name": "Email / Notification Service",
            "status": mail_status,
            "last_heartbeat": (latest_mail_dt or now_dt).isoformat(),
            "api_error_rate_pct": mail_err_pct,
            "avg_latency_ms": smtp_latency,
            "db_connections": None,
            "queue_backlog": None,
            "storage_utilization_pct": None,
            "alert_severity": mail_severity,
            "instrumented": True,
        },
        {
            "id": 8,
            "service_name": "WhatsApp / Communication API",
            "status": wa_status,
            "last_heartbeat": now_dt.isoformat(),
            "api_error_rate_pct": None,
            "avg_latency_ms": None,
            "db_connections": None,
            "queue_backlog": None,
            "storage_utilization_pct": None,
            "alert_severity": "Low",
            "instrumented": has_wa_config,
        },
        {
            "id": 9,
            "service_name": "Identity & Access (SSO/OAuth)",
            "status": auth_status,
            "last_heartbeat": (latest_login or now_dt).isoformat(),
            "api_error_rate_pct": 0.0,
            "avg_latency_ms": None,
            "db_connections": None,
            "queue_backlog": active_sessions,
            "storage_utilization_pct": None,
            "alert_severity": "Low",
            "instrumented": True,
        },
    ]

    return services, storage, db_connections_str


def _build_active_alerts(services, filters):
    """Generate dynamic alerts from degraded/critical services, failed Celery tasks, critical tickets, and provisioning failures."""
    alerts = []
    now_dt = timezone.now()

    for svc in services:
        st_lower = svc["status"].lower()
        if "critical" in st_lower or "degraded" in st_lower:
            sev = "Critical" if "critical" in st_lower else "Medium"
            alerts.append(
                {
                    "id": f"svc-{svc['id']}",
                    "service_name": svc["service_name"],
                    "title": f"{svc['service_name']} {svc['status']}",
                    "description": f"Error rate: {svc['api_error_rate_pct'] or 0}%, Latency: {svc['avg_latency_ms'] or 'N/A'} ms",
                    "severity": sev,
                    "timestamp": svc["last_heartbeat"],
                    "source": "service_probe",
                }
            )
        if svc.get("queue_backlog") and svc["service_name"] == "Background Jobs (Celery)" and svc["queue_backlog"] > 50:
            alerts.append(
                {
                    "id": "celery-backlog",
                    "service_name": svc["service_name"],
                    "title": "Job Queue Backlog High",
                    "description": f"{svc['queue_backlog']} pending jobs in background queue (Celery).",
                    "severity": "Medium",
                    "timestamp": svc["last_heartbeat"],
                    "source": "redis_queue",
                }
            )

    # Open P0-Critical support tickets via icontains
    crit_tickets = TicketManagement.objects.filter(
        Is_Deleted=False, Priority__icontains="critical"
    )
    for closed in CLOSED_TICKET_STATUSES:
        crit_tickets = crit_tickets.exclude(Ticket_Status__icontains=closed)
    for ticket in crit_tickets.order_by("-Created_Date")[:5]:
        alerts.append(
            {
                "id": f"ticket-{ticket.id}",
                "service_name": "Web Application (Portal)",
                "title": f"Critical Ticket: {ticket.TicketManagement_Id}",
                "description": ticket.Related_Module or ticket.Ticket_Description[:120],
                "severity": "Critical",
                "timestamp": (ticket.Created_Date or now_dt).isoformat(),
                "source": "ticket_management",
            }
        )

    # Failed tenant provisioning jobs via icontains
    failed_jobs = TenantProvisioningJob.objects.filter(
        Is_Deleted=False, status__icontains="fail"
    ).order_by("-created_at")[:5]
    for job in failed_jobs:
        alerts.append(
            {
                "id": f"prov-{job.id}",
                "service_name": "Background Jobs (Celery)",
                "title": f"Provisioning Failed: {job.customer_name or job.job_code}",
                "description": f"Product {job.product} ({job.subdomain or 'no subdomain'}) failed provisioning.",
                "severity": "High",
                "timestamp": (job.created_at or now_dt).isoformat(),
                "source": "tenant_provisioning",
            }
        )

    if filters.get("service_name"):
        s_term = filters["service_name"].lower()
        alerts = [a for a in alerts if s_term in a["service_name"].lower()]
    if filters.get("severity"):
        sev_term = filters["severity"].lower()
        alerts = [a for a in alerts if sev_term in a["severity"].lower()]

    return alerts


def _build_daily_health_trends(filters):
    """Build daily uptime %, error rate %, and average latency ms trends from TaskResult & AuditHistory."""
    start_d = filters["start_date"]
    end_d = filters["end_date"]
    start_dt = filters["start_dt"]
    end_dt = filters["end_dt"]

    # Daily TaskResult stats
    task_rows = (
        TaskResult.objects.filter(date_done__gte=start_dt, date_done__lte=end_dt)
        .annotate(day=TruncDate("date_done"))
        .values("day")
        .annotate(
            total=Count("id"),
            failed=Count("id", filter=Q(status__icontains="fail") | Q(status__icontains="error")),
            avg_dur=Avg(
                ExpressionWrapper(F("date_done") - F("date_started"), output_field=DurationField())
            ),
        )
        .order_by("day")
    )
    tasks_by_day = {r["day"]: r for r in task_rows if r.get("day")}

    audit_rows = (
        AuditHistory.objects.filter(Is_Deleted=False, Created_Date__gte=start_dt, Created_Date__lte=end_dt)
        .annotate(day=TruncDate("Created_Date"))
        .values("day")
        .annotate(
            total=Count("id"),
            failed=Count("id", filter=Q(Action_Status__icontains="fail") | Q(Action_Status__icontains="error")),
        )
        .order_by("day")
    )
    audits_by_day = {r["day"]: r for r in audit_rows if r.get("day")}

    uptime_series = []
    error_series = []
    latency_series = []

    cur = start_d
    while cur <= end_d:
        t_row = tasks_by_day.get(cur) or {}
        a_row = audits_by_day.get(cur) or {}
        total_ops = (t_row.get("total") or 0) + (a_row.get("total") or 0)
        failed_ops = (t_row.get("failed") or 0) + (a_row.get("failed") or 0)

        err_pct = round((failed_ops / total_ops) * 100, 2) if total_ops > 0 else 0.0
        uptime_pct = round(100.0 - err_pct, 2) if total_ops > 0 else 100.0
        avg_dur = t_row.get("avg_dur")
        latency_ms = round(avg_dur.total_seconds() * 1000, 1) if avg_dur else 0.0

        day_label = cur.strftime("%b %d")
        day_iso = str(cur)
        uptime_series.append({"date": day_iso, "label": day_label, "uptime_pct": uptime_pct})
        error_series.append({"date": day_iso, "label": day_label, "error_rate_pct": err_pct})
        latency_series.append({"date": day_iso, "label": day_label, "avg_latency_ms": latency_ms})
        cur += timedelta(days=1)

    return uptime_series, error_series, latency_series


def build_system_health_alerts_dashboard(filters):
    """Build full payload for the System Health & Alerts dashboard screen."""
    all_services, storage, db_connections_str = _build_services_health(filters)

    # Apply icontains filters onto service rows
    filtered_services = list(all_services)
    if filters.get("service_name"):
        term = filters["service_name"].lower()
        filtered_services = [s for s in filtered_services if term in s["service_name"].lower()]
    if filters.get("status"):
        st_term = filters["status"].lower()
        filtered_services = [s for s in filtered_services if st_term in s["status"].lower()]
    if filters.get("severity"):
        sev_term = filters["severity"].lower()
        filtered_services = [s for s in filtered_services if sev_term in s["alert_severity"].lower()]

    total_services = len(all_services)
    healthy_count = sum(1 for s in all_services if "healthy" in s["status"].lower())
    warning_count = sum(1 for s in all_services if "degraded" in s["status"].lower() or "warning" in s["status"].lower())
    critical_count = sum(1 for s in all_services if "critical" in s["status"].lower() or "down" in s["status"].lower())

    if critical_count > 0:
        overall_health = "Critical"
    elif warning_count > 0:
        overall_health = "Warning"
    else:
        overall_health = "Healthy"

    latencies = [s["avg_latency_ms"] for s in all_services if s["avg_latency_ms"] is not None]
    avg_api_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0

    alerts = _build_active_alerts(all_services, filters)
    uptime_series, error_series, latency_series = _build_daily_health_trends(filters)

    latest_uptime = (
        round(sum(pt["uptime_pct"] for pt in uptime_series) / len(uptime_series), 2)
        if uptime_series
        else 100.0
    )
    latest_error = error_series[-1]["error_rate_pct"] if error_series else 0.0
    latest_latency = latency_series[-1]["avg_latency_ms"] if latency_series else avg_api_latency

    return {
        "filters_applied": {
            "date_range": filters["date_range"],
            "from_date": str(filters["start_date"]),
            "to_date": str(filters["end_date"]),
            "service_name": filters.get("service_name"),
            "status": filters.get("status"),
            "severity": filters.get("severity"),
        },
        "last_updated": timezone.now().isoformat(),
        "kpis": {
            "overall_system_health": overall_health,
            "total_services": total_services,
            "healthy_services": healthy_count,
            "warning_services": warning_count,
            "critical_services": critical_count,
            "system_uptime_30d_pct": latest_uptime,
            "avg_api_latency_ms": avg_api_latency,
            "db_connections": db_connections_str or "N/A",
        },
        "service_health_overview": filtered_services,
        "active_alerts": {
            "total_alerts": len(alerts),
            "alerts": alerts,
        },
        "charts": {
            "service_uptime_trend": {
                "latest_uptime_pct": latest_uptime,
                "daily_data": uptime_series,
            },
            "api_error_rate_trend": {
                "latest_error_rate_pct": latest_error,
                "daily_data": error_series,
            },
            "average_latency_trend": {
                "latest_latency_ms": latest_latency,
                "daily_data": latency_series,
            },
            "storage_utilization_overall": storage,
        },
    }
