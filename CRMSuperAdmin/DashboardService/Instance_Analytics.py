# # Total Instances
# def get_total_instances():
#     return Instance.objects.filter(is_deleted=False).count()
# # Instances by Product
# from django.db.models import Count

# def get_instances_by_product():
#     return (
#         Instance.objects.filter(is_deleted=False)
#         .values("product_type")
#         .annotate(total=Count("id"))
#     )

# # output like
# # [
# #   {"product_type": "education", "total": 120},
# #   {"product_type": "retail", "total": 80}
# # ]

# # Active vs Inactive Instances
# def get_instance_status_distribution():
#     return (
#         Instance.objects.filter(is_deleted=False)
#         .values("status")
#         .annotate(total=Count("id"))
#     )
# # [
# #   {"status": "active", "total": 150},
# #   {"status": "inactive", "total": 30}
# # ]
# # Instance Growth Over Time
# from django.db.models.functions import TruncMonth

# def get_instance_growth():
#     return (
#         Instance.objects.filter(is_deleted=False)
#         .annotate(month=TruncMonth("created_at"))
#         .values("month")
#         .annotate(total=Count("id"))
#         .order_by("month")
#     )

# # Active Instances Count (KPI Card)
# def get_active_instances():
#     return Instance.objects.filter(status="active").count()

# # Combine All Analytics
# def get_instance_analytics():
#     return {
#         "total_instances": get_total_instances(),
#         "active_instances": get_active_instances(),
#         "instances_by_product": list(get_instances_by_product()),
#         "status_distribution": list(get_instance_status_distribution()),
#         "growth": list(get_instance_growth()),
#     }

# # Add Caching
# from django.core.cache import cache

# def get_cached_instance_analytics():
#     data = cache.get("instance_analytics")

#     if not data:
#         data = get_instance_analytics()
#         cache.set("instance_analytics", data, timeout=300)

#     return data

# # 1. Instance Churn
# def get_instance_churn():
#     return Instance.objects.filter(status="inactive").count()

# # 2. Top Growing Product
# def top_product():
#     return (
#         Instance.objects.values("product_type")
#         .annotate(total=Count("id"))
#         .order_by("-total")
#         .first()
#     )

# # 3. New Instances (Last 7 Days)
# from datetime import timedelta
# from django.utils.timezone import now

# def new_instances_last_7_days():
#     return Instance.objects.filter(
#         created_at__gte=now() - timedelta(days=7)
#     ).count()

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.core.cache import cache
from datetime import timedelta
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Instance_Creation
 # adjust import path as needed


# Total Instances
def get_total_instances():
    return Instance_Creation.objects.filter(Is_Deleted=False).count()


# Instances by Product
def get_instances_by_product():
    return (
        Instance_Creation.objects.filter(Is_Deleted=False)
        .values("product_type")
        .annotate(total=Count("id"))
    )


# Active vs Inactive Instances
def get_instance_status_distribution():
    return (
        Instance_Creation.objects.filter(Is_Deleted=False)
        .values("status")
        .annotate(total=Count("id"))
    )


# Instance Growth Over Time
def get_instance_growth():
    return (
        Instance_Creation.objects.filter(Is_Deleted=False)
        .annotate(month=TruncMonth("Created_Date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )


# Active Instances Count (KPI Card)
def get_active_instances():
    return Instance_Creation.objects.filter(status="active", Is_Deleted=False).count()


# Instance Churn
def get_instance_churn():
    return Instance_Creation.objects.filter(status="inactive", Is_Deleted=False).count()


# Top Growing Product
def top_product():
    return (
        Instance_Creation.objects.filter(Is_Deleted=False)
        .values("product_type")
        .annotate(total=Count("id"))
        .order_by("-total")
        .first()
    )


# New Instances (Last 7 Days)
def new_instances_last_7_days():
    return Instance_Creation.objects.filter(
        Created_Date__gte=now() - timedelta(days=7),
        Is_Deleted=False
    ).count()


# Combine All Analytics
def get_instance_analytics():
    return {
        "total_instances": get_total_instances(),
        "active_instances": get_active_instances(),
        "instances_by_product": list(get_instances_by_product()),
        "status_distribution": list(get_instance_status_distribution()),
        "growth": list(get_instance_growth()),
    }


# Add Caching
def get_cached_instance_analytics():
    data = cache.get("instance_analytics")

    if not data:
        data = get_instance_analytics()
        cache.set("instance_analytics", data, timeout=300)

    return data

