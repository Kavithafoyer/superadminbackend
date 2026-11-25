
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncYear
from django.core.cache import cache
from ..models import Payments, Subscriptions


# 2.1 Total Revenue (All Time)
def get_total_revenue():
    return (
        Payments.objects.filter(status="success", Is_Deleted=False)
        .aggregate(total=Sum("grossAmount"))["total"]
        or 0
    )


# 2.2 Monthly Revenue
def get_monthly_revenue():
    return list(
        Payments.objects.filter(status="success", Is_Deleted=False)
        .annotate(month=TruncMonth("Payment_Date"))
        .values("month")
        .annotate(total=Sum("grossAmount"))
        .order_by("month")
    )


# 2.3 Yearly Revenue
def get_yearly_revenue():
    return list(
        Payments.objects.filter(status="success", Is_Deleted=False)
        .annotate(year=TruncYear("Payment_Date"))
        .values("year")
        .annotate(total=Sum("grossAmount"))
        .order_by("year")
    )


# 3. MRR — Monthly Recurring Revenue
def get_mrr():
    return (
        Subscriptions.objects.filter(
            status="active",
            Is_Deleted=False,
            SubscriptionPeriod__icontains="month",
        )
        .aggregate(total=Sum("SuscriptionAmount"))["total"]
        or 0
    )


# 4. ARR — Annual Recurring Revenue
def get_arr():
    return (
        Subscriptions.objects.filter(
            status="active",
            Is_Deleted=False,
            SubscriptionPeriod__icontains="year",
        )
        .aggregate(total=Sum("SuscriptionAmount"))["total"]
        or 0
    )


# 5. Revenue Per Product
def get_revenue_per_product():
    return list(
        Payments.objects.filter(status="success", Is_Deleted=False)
        .values("InvoiceFor")
        .annotate(total=Sum("grossAmount"))
    )


# 6. Revenue Per Plan
def get_revenue_per_plan():
    return list(
        Payments.objects.filter(status="success", Is_Deleted=False)
        .values("Subscription_Id__Plan_Name")
        .annotate(total=Sum("grossAmount"))
    )


# 7. Cached Dashboard
def get_cached_dashboard():
    data = cache.get("revenue_dashboard")

    if not data:
        data = {
            "total_revenue": get_total_revenue(),
            "mrr": get_mrr(),
            "arr": get_arr(),
            "monthly_revenue": get_monthly_revenue(),
            "yearly_revenue": get_yearly_revenue(),
            "revenue_per_product": get_revenue_per_product(),
            "revenue_per_plan": get_revenue_per_plan(),
        }
        cache.set("revenue_dashboard", data, timeout=300)

    return data