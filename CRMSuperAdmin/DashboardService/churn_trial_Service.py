from django.db.models import Count, Q
from django.core.cache import cache
from datetime import date, timedelta
from ..models import Subscriptions


# 1. Churn by Plan
def get_churn_by_product():
    data = (
        Subscriptions.objects.filter(Is_Deleted=False)
        .values("Plan_Name")
        .annotate(
            total=Count("id"),
            cancelled=Count("id", filter=Q(status="cancelled"))
        )
    )

    result = []
    for item in data:
        total = item["total"]
        cancelled = item["cancelled"]
        churn = (cancelled / total * 100) if total > 0 else 0
        result.append({
            "product": item["Plan_Name"],
            "total": total,
            # "cancelled": cancelled,
            # "churn_rate": round(churn, 2)
        })

    return result


# 2. Trial → Paid Conversion
def get_trial_to_paid_conversion():
    trials = Subscriptions.objects.filter(status="trial", Is_Deleted=False).count()

    converted = Subscriptions.objects.filter(
        status="active",
        is_trial=False,
        Is_Deleted=False
    ).count()

    if trials == 0:
        return 0

    return round((converted / trials) * 100, 2)


# 3. Expiring Soon
def get_expiring_soon_list(days=7):
    return list(
        Subscriptions.objects.filter(
            status="active",
            Is_Deleted=False,
            end_date__lte=date.today() + timedelta(days=days)
        ).values("id", "Subscription_Name", "Customer_Name", "end_date")
    )