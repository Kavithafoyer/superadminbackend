from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, DurationField
from django.db.models.functions import Coalesce,TruncMonth
from datetime import timedelta
from CRMSuperAdmin.models import *
from django.db.models import FloatField
from django.utils.timezone import now

##PaymentDashboardAnalytics
def payment_dashboard_service():
    # =========================
    # TOTAL INVOICED
    # =========================
    total_invoiced = Invoice.objects.filter(Is_Deleted=False,Is_Archived=False).aggregate(total=Coalesce(Sum('NetAmount'), 0.0,output_field=FloatField()))['total']

    # =========================
    # OUTSTANDING AMOUNT
    # =========================
    outstanding_amount = Invoice.objects.filter(Is_Deleted=False,Is_Archived=False).exclude(
        Payment_Status="Paid"
    ).aggregate(total=Coalesce(Sum('NetAmount'), 0.0,output_field=FloatField()))['total']
    # =========================
    # TOTAL PAYMENTS
    # =========================
    total_payments = Payments.objects.filter(Is_Deleted=False,Is_Archived=False).count()
    # =========================
    # SUCCESS PAYMENTS
    # =========================
    success_payments = Payments.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        status="success"
    ).count()


    # =========================
    # FAILED PAYMENTS
    # =========================

    failed_payments = Payments.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        status="failed"
    ).count()


    # =========================
    # SUCCESS RATE
    # =========================

    success_rate = 0

    if total_payments > 0:
        success_rate = round(
            (success_payments / total_payments) * 100,
            2
        )


    # =========================
    # AVG PAYMENT DELAY
    # =========================

    avg_delay_queryset = Payments.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        Payment_Date__isnull=False,
        Invoice_Date__isnull=False
    ).annotate(
        payment_delay=ExpressionWrapper(
            F('Payment_Date') - F('Invoice_Date'),
            output_field=DurationField()
        )
    ).aggregate(
        avg_delay=Avg('payment_delay')
    )

    avg_delay = avg_delay_queryset['avg_delay']

    avg_payment_delay_days = 0

    if avg_delay:
        avg_payment_delay_days = round(
            avg_delay.total_seconds() / 86400,
            2
        )


    # =========================
    # FINAL RESPONSE
    # =========================

    return {
    "total_invoiced": round(total_invoiced or 0, 2),
    "outstanding_amount": round(outstanding_amount or 0, 2),
    "payment_success_rate": round(success_rate or 0, 2),
    "failed_payments": failed_payments or 0,
    "avg_payment_delay_days": round(avg_payment_delay_days or 0)
}
#-------------------------------------------------------#
####RenewalDashboardAnalytics

def renewal_dashboard_service():

    current_month = now().month
    current_year = now().year


    # =====================================
    # RENEWALS DUE THIS MONTH
    # =====================================

    renewals_this_month = Renewal.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        RenewaldueDate__month=current_month,
        RenewaldueDate__year=current_year
    ).count()


    # =====================================
    # AUTO RENEWAL ENABLED
    # =====================================

    total_active_subscriptions = Subscriptions.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        status="active"
    ).exclude(
        status="trial"
    ).count()


    auto_renewal_enabled = Subscriptions.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        status="active",
        Auto_Renewal_Flag=True
    ).exclude(
        status="trial"
    ).count()


    auto_renewal_percentage = 0

    if total_active_subscriptions > 0:

        auto_renewal_percentage = round(
            (
                auto_renewal_enabled /
                total_active_subscriptions
            ) * 100,
            2
        )


    # =====================================
    # RENEWALS COMPLETED
    # =====================================

    renewals_completed = Renewal.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        InvoicegenFlag=True,
        status="Active"
    ).count()


    # =====================================
    # CANCEL REQUESTS
    # =====================================

    cancel_requests = Cancelplans.objects.filter(
        Is_Deleted=False,
        status=False
    ).count()


    # =====================================
    # FINAL RESPONSE
    # =====================================

    return {

        "renewals_this_month": renewals_this_month,

        "auto_renewal_enabled": auto_renewal_enabled,

        "auto_renewal_percentage": round(
            auto_renewal_percentage or 0,
            2
        ),

        "renewals_completed": renewals_completed,

        "cancel_requests": cancel_requests}

#----------------------------------------------------------------#
##RenewalFunnelAnalytics

def renewal_funnel_service():

    current_month = now().month
    current_year = now().year


    # =====================================
    # DUE THIS MONTH
    # =====================================

    due_this_month = Renewal.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        RenewaldueDate__month=current_month,
        RenewaldueDate__year=current_year
    )


    due_count = due_this_month.count()


    # =====================================
    # INVOICE GENERATED
    # =====================================

    invoice_generated = due_this_month.filter(
        InvoicegenFlag=True
    ).count()


    # =====================================
    # PAYMENT RECEIVED
    # =====================================

    invoice_ids = due_this_month.filter(
        Invoice_Id__isnull=False
    ).values_list(
        'Invoice_Id',
        flat=True
    )

    payment_received = Payments.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        Invoice_Id__in=invoice_ids,
        status="success"
    ).count()


    # =====================================
    # LAPSED / FAILED
    # =====================================

    failed = due_this_month.exclude(
        status="Active"
    ).count()


    # =====================================
    # FINAL RESPONSE
    # =====================================

    return {

        "due_this_month": due_count,

        "invoice_generated": invoice_generated,

        "payment_received": payment_received,

        "failed": failed}

#------------------------------------------------------#

#CancellationOverviewAnalytics
def cancellation_overview_service():

    today = now().date()

    upcoming_expiry_date = today + timedelta(days=30)


    # =====================================
    # TOTAL CANCEL REQUESTS
    # =====================================

    total_cancel_requests = Cancelplans.objects.filter(
        Is_Deleted=False
    ).count()


    # =====================================
    # PENDING CANCELLATIONS
    # =====================================

    pending_cancellations = Cancelplans.objects.filter(
        Is_Deleted=False,
        status=False
    ).count()


    # =====================================
    # TOTAL PENDING PAYMENT
    # =====================================

    total_pending_payment = Cancelplans.objects.filter(
        Is_Deleted=False
    ).aggregate(
        total=Coalesce(
            Sum('Pending_Payment'),
            0.0,
            output_field=FloatField()
        )
    )['total']


    # =====================================
    # UPCOMING EXPIRIES
    # =====================================

    upcoming_expiries = Cancelplans.objects.filter(
        Is_Deleted=False,
        Expiry_Date__gte=today,
        Expiry_Date__lte=upcoming_expiry_date
    ).count()


    # =====================================
    # FINAL RESPONSE
    # =====================================

    return {

        "total_cancel_requests": total_cancel_requests,

        "pending_cancellations": pending_cancellations,

        "total_pending_payment": round(
            total_pending_payment or 0,
            2
        ),

        "upcoming_expiries": upcoming_expiries

    }


#---------------------------------------------------------------------------#

# PlanAdoptionDashboardAnalytics
def plan_adoption_dashboard_service():

    # =====================================
    # BASE SUBSCRIPTIONS QUERY
    # =====================================

    valid_subscriptions = Subscriptions.objects.filter(
        Is_Deleted=False,
        Is_Archived=False
    )


    # =====================================
    # TOTAL ACTIVE SUBSCRIPTIONS
    # =====================================

    total_active_subscriptions = valid_subscriptions.filter(
        status="active"
    ).count()


    # =====================================
    # TRIAL SUBSCRIPTIONS
    # =====================================

    total_trial_subscriptions = valid_subscriptions.filter(
        status="trial"
    ).count()


    # =====================================
    # MOST SUBSCRIBED PLAN
    # =====================================

    most_subscribed_plan_queryset = valid_subscriptions.values(
        'Plan_Id__Plan_Name'
    ).annotate(
        total=Count('id')
    ).order_by('-total')


    most_subscribed_plan = None
    most_subscribed_plan_count = 0

    if most_subscribed_plan_queryset.exists():

        most_subscribed_plan = (
            most_subscribed_plan_queryset.first()
            ['Plan_Id__Plan_Name']
        )

        most_subscribed_plan_count = (
            most_subscribed_plan_queryset.first()
            ['total']
        )


    # =====================================
    # ACTIVE PLANS
    # =====================================

    active_plans = Plan.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        Is_Active_Flg=True
    ).count()


    # =====================================
    # MONTHLY BILLING SUBSCRIPTIONS
    # =====================================

    monthly_subscriptions = valid_subscriptions.filter(
        Plan_Id__billing_cycle="monthly"
    ).count()


    # =====================================
    # YEARLY BILLING SUBSCRIPTIONS
    # =====================================

    yearly_subscriptions = valid_subscriptions.filter(
        Plan_Id__billing_cycle="yearly"
    ).count()


    # =====================================
    # FINAL RESPONSE
    # =====================================

    return {

        "total_active_subscriptions":
            total_active_subscriptions,

        "trial_subscriptions":
            total_trial_subscriptions,

        "most_subscribed_plan":
            most_subscribed_plan,

        "most_subscribed_plan_count":
            most_subscribed_plan_count,

        "active_plans":
            active_plans,

        "monthly_subscriptions":
            monthly_subscriptions,

        "yearly_subscriptions":
            yearly_subscriptions

    }

#----------------------------------------------------#

#TopPlansDistributionAnalytics

def top_plans_distribution_service():

    # =====================================
    # ACTIVE SUBSCRIPTIONS ONLY
    # =====================================

    active_subscriptions = Subscriptions.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        status="active"
    )


    # =====================================
    # PLAN DISTRIBUTION
    # =====================================

    top_plans_queryset = active_subscriptions.values(
        'Plan_Id__Plan_Name'
    ).annotate(
        total=Count('id')
    ).order_by('-total')


    # =====================================
    # CHART FORMATTING
    # =====================================

    labels = []
    counts = []


    for item in top_plans_queryset:

        labels.append(
            item['Plan_Id__Plan_Name']
        )

        counts.append(
            item['total']
        )


    # =====================================
    # FINAL RESPONSE
    # =====================================

    return {

        "labels": labels,

        "counts": counts

    }


#------------------------------------------------------------------------------#


def revenue_forecast_dashboard_service():

    # =====================================
    # BASE PAYMENTS
    # =====================================

    successful_payments = Payments.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        status="success"
    )


    # =====================================
    # CURRENT MRR
    # =====================================

    current_mrr = successful_payments.filter(
        Subscription_Id__Plan_Id__billing_cycle="monthly"
    ).aggregate(
        total=Coalesce(
            Sum('NetAmount'),
            0.0,
            output_field=FloatField()
        )
    )['total']


    # =====================================
    # CURRENT ARR
    # =====================================

    current_arr = successful_payments.filter(
        Subscription_Id__Plan_Id__billing_cycle="yearly"
    ).aggregate(
        total=Coalesce(
            Sum('NetAmount'),
            0.0,
            output_field=FloatField()
        )
    )['total']


    # =====================================
    # MRR TREND
    # =====================================

    mrr_trend_queryset = successful_payments.annotate(
        month=TruncMonth('Payment_Date')
    ).values(
        'month'
    ).annotate(
        total=Coalesce(
            Sum('NetAmount'),
            0.0,
            output_field=FloatField()
        )
    ).order_by('month')


    mrr_trend = []


    for item in mrr_trend_queryset:

        mrr_trend.append({

            "month": item['month'].strftime('%Y-%m'),

            "mrr": round(
                item['total'] or 0,
                2
            )

        })


    # =====================================
    # ARR TREND
    # =====================================

    arr_trend = []


    for item in mrr_trend_queryset:

        arr_trend.append({

            "month": item['month'].strftime('%Y-%m'),

            "arr": round(
                (item['total'] or 0) * 12,
                2
            )

        })


    # =====================================
    # EXPIRY FORECAST
    # =====================================

    today = now().date()

    next_6_months = today + timedelta(days=180)


    expiry_queryset = Renewal.objects.filter(
        Is_Deleted=False,
        Is_Archived=False,
        RenewaldueDate__gte=today,
        RenewaldueDate__lte=next_6_months
    ).annotate(
        month=TruncMonth('RenewaldueDate')
    ).values(
        'month'
    ).annotate(
        total=Sum('id')
    ).order_by('month')


    expiry_forecast = []
    for item in expiry_queryset:
        expiry_forecast.append({
            "month": item['month'].strftime('%Y-%m'),
            "expiring_subscriptions":
                item['total']
        })
    # =====================================
    # FINAL RESPONSE
    # =====================================

    return {
        "current_mrr":
            round(current_mrr or 0, 2),
        "current_arr":
            round(current_arr or 0, 2),
        "mrr_trend":
            mrr_trend,
        "arr_trend":
            arr_trend,
        "expiry_forecast":
            expiry_forecast}

#---------------------------------#



def request_operations_dashboard_service():

    # =====================================
    # ADDON REQUESTS
    # =====================================

    addon_requests_queryset = (
        Addsubscriptionrequest.objects.filter(
            Is_Deleted=False
        )
    )

    addon_requests = (
        addon_requests_queryset.count()
    )


    # =====================================
    # STORAGE REQUESTS
    # =====================================

    storage_requests_queryset = (
        Additionalstoragerequest.objects.filter(
            Is_Deleted=False,
            Is_Archived=False
        )
    )

    storage_requests = (
        storage_requests_queryset.count()
    )


    # =====================================
    # INSTANCE REQUESTS
    # =====================================

    instance_requests_queryset = (
        InstanceRequest.objects.filter(
            Is_Deleted=False
        )
    )

    instance_requests = (
        instance_requests_queryset.count()
    )


    # =====================================
    # TOTAL REQUESTS
    # =====================================

    total_requests = (

        addon_requests +

        storage_requests +

        instance_requests

    )


    # =====================================
    # INVOICE GENERATED
    # =====================================

    addon_invoice_generated = (
        addon_requests_queryset.filter(
            Invoicegenflg=True
        ).count()
    )

    storage_invoice_generated = (
        storage_requests_queryset.filter(
            InvoicegenFlag=True
        ).count()
    )

    invoice_generated_requests = (

        addon_invoice_generated +

        storage_invoice_generated

    )


    # =====================================
    # PENDING INVOICE
    # =====================================

    pending_invoice_requests = (

        total_requests -

        invoice_generated_requests

    )


    # =====================================
    # INSTANCE CREATED
    # =====================================

    instance_created = (
        instance_requests_queryset.filter(
            InstanceCreatedFlag=True
        ).count()
    )


    # =====================================
    # INSTANCE PENDING
    # =====================================

    instance_pending = (
        instance_requests_queryset.filter(
            InstanceCreatedFlag=False
        ).count()
    )


    # =====================================
    # REQUEST DISTRIBUTION
    # =====================================

    request_distribution = [

        {
            "module":
                "Addon Requests",

            "count":
                addon_requests
        },

        {
            "module":
                "Storage Requests",

            "count":
                storage_requests
        },

        {
            "module":
                "Instance Requests",

            "count":
                instance_requests
        }

    ]


    # =====================================
    # FINAL RESPONSE
    # =====================================

    return {

        "total_requests":
            total_requests,

        "addon_requests":
            addon_requests,

        "storage_requests":
            storage_requests,

        "instance_requests":
            instance_requests,

        "invoice_generated_requests":
            invoice_generated_requests,

        "pending_invoice_requests":
            pending_invoice_requests,

        "instance_created":
            instance_created,

        "instance_pending":
            instance_pending,

        "request_distribution":
            request_distribution

    }