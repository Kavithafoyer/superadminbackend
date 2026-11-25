
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.core.cache import cache
from ..models import Subscriptions


# 3.1 Active Subscriptions
def get_active_subscriptions():
    return Subscriptions.objects.filter(status="active", Is_Deleted=False).count()


# 3.2 Trial Users
def get_trial_users():
    return Subscriptions.objects.filter(status="trial", Is_Deleted=False).count()


# 3.3 Expired Subscriptions
def get_expired_subscriptions():
    return Subscriptions.objects.filter(status="expired", Is_Deleted=False).count()


# 3.4 Cancelled Subscriptions
# def get_cancelled_subscriptions():
#     return Subscriptions.objects.filter(status="cancelled", Is_Deleted=False).count()


# 3.5 Churn Rate — Cancelled / Total × 100
# def get_churn_rate():
#     total = Subscriptions.objects.filter(Is_Deleted=False).count()
#     cancelled = Subscriptions.objects.filter(status="cancelled", Is_Deleted=False).count()

#     if total == 0:
#         return 0

#     return round((cancelled / total) * 100, 2)


# 3.6 Renewal Rate — previous_subscription field tracks renewals
def get_renewal_rate():
    renewed = Subscriptions.objects.filter(
        previous_subscription__isnull=False, Is_Deleted=False
    ).count()
    expired = Subscriptions.objects.filter(status="expired", Is_Deleted=False).count()

    if expired == 0:
        return 0

    return round((renewed / expired) * 100, 2)


# 3.7 Monthly Subscription Growth
def get_subscription_growth():
    return list(
        Subscriptions.objects.filter(Is_Deleted=False)
        .annotate(month=TruncMonth("Created_Date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )


# Cached Dashboard
def get_cached_subscription_analytics():
    data = cache.get("subscription_dashboard")

    if not data:
        data = {
            "active": get_active_subscriptions(),
            "trial": get_trial_users(),
            "expired": get_expired_subscriptions(),
            # "cancelled": get_cancelled_subscriptions(),
            # "churn_rate": get_churn_rate(),
            "renewal_rate": get_renewal_rate(),
            "subscription_growth": get_subscription_growth(),
        }
        cache.set("subscription_dashboard", data, timeout=300)

    return data