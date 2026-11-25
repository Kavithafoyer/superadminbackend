
from django.utils.timezone import now
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth
from django.core.cache import cache
from ..models import UserActivity


# 2.1 Login Tracking
def login_success(external_user_id, instance):
    UserActivity.objects.create(
        external_user_id=external_user_id,
        instance=instance,
        action="login"
    )


# 2.2 Feature Tracking
def track_create_lead(external_user_id, instance):
    UserActivity.objects.create(
        external_user_id=external_user_id,
        instance=instance,
        action="create_lead"
    )


# 3.1 Daily Active Users (DAU)
def get_dau():
    today = now().date()
    return (
        UserActivity.objects.filter(created_at__date=today)
        .values("external_user_id")
        .distinct()
        .count()
    )


# 3.2 Monthly Active Users (MAU)
def get_mau():
    today = now()
    return (
        UserActivity.objects.filter(
            created_at__year=today.year,
            created_at__month=today.month
        )
        .values("external_user_id")
        .distinct()
        .count()
    )


# 3.3 DAU Trend (Daily Chart)
def get_dau_trend():
    return (
        UserActivity.objects.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(active_users=Count("external_user_id", distinct=True))
        .order_by("day")
    )


# 3.4 MAU Trend (Monthly Chart)
def get_mau_trend():
    return (
        UserActivity.objects.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(active_users=Count("external_user_id", distinct=True))
        .order_by("month")
    )


# 3.5 Feature Usage
def get_feature_usage():
    return (
        UserActivity.objects.values("action")
        .annotate(count=Count("id"))
        .order_by("-count")
    )


# 3.6 Top Active Users
def get_top_users():
    return (
        UserActivity.objects.values("external_user_id")
        .annotate(total_actions=Count("id"))
        .order_by("-total_actions")[:10]
    )


# 3.7 Instance Usage (Product-wise)
def get_usage_by_product():
    return (
        UserActivity.objects.values("instance__product_type")
        .annotate(total=Count("id"))
    )


# Cached Analytics
def get_cached_usage_analytics():
    data = cache.get("usage_analytics")

    if not data:
        data = {
            "dau": get_dau(),
            "mau": get_mau(),
            "dau_trend": list(get_dau_trend()),
            "mau_trend": list(get_mau_trend()),
            "feature_usage": list(get_feature_usage()),
            "top_users": list(get_top_users()),
            "usage_by_product": list(get_usage_by_product()),
        }
        cache.set("usage_analytics", data, timeout=300)

    return data