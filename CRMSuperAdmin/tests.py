from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.urls import resolve, reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from CRMSuperAdmin.DashboardService.customer_partner_kpi_service import (
    _build_customer_segmentation,
    _build_top_customers_by_arr,
    _build_top_partners_by_revenue,
)
from CRMSuperAdmin.DashboardService.revenue_subscription_analytics_service import (
    _build_plan_customer_distribution,
    _build_revenue_by_plan,
    _compute_subscription_revenue,
    _filtered_renewals_qs,
)
from CRMSuperAdmin.DashboardService.superadmin_dashboard_service import (
    _apply_account_scope,
    _compute_mrr_arr_from_subs,
    _compute_open_tickets,
    _format_inr,
    parse_dashboard_filters,
)
from CRMSuperAdmin.DashboardService.system_health_service import (
    _build_active_alerts,
    parse_system_health_filters,
)
from CRMSuperAdmin.services.customer_overview_service import (
    _compute_customer_health,
    _compute_usage_and_adoption,
    _compute_usage_trend,
    _count_open_critical_tickets,
    _get_customer_scope,
    parse_positive_int,
)
from CRMSuperAdmin.views import (
    BusinessOverviewDashboardAPI,
    CustomerKpiDashboardAPI,
    CustomerUsageHealthAnalyticsAPI,
    PartnerKpiDashboardAPI,
    Planlistwithoutpaginaton,
    ProductMasterLookupsAPIView,
    ProductPerformanceDashboardAPI,
    RevenueSubscriptionAnalyticsDashboardAPI,
    SystemHealthAlertsDashboardAPI,
    SystemHealthAPI,
)


class CustomerUsageHealthAnalyticsTests(SimpleTestCase):
    """Tests for CustomerUsageHealthAnalyticsAPI and customer_overview_service."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = CustomerUsageHealthAnalyticsAPI.as_view()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_url_resolves(self):
        url = reverse("customer-usage-health-analytics", kwargs={"tenant_name": "default"})
        self.assertEqual(url, "/default/superadmin/CustomerUsageHealthAnalytics/")
        match = resolve(url)
        self.assertEqual(match.func.view_class, CustomerUsageHealthAnalyticsAPI)

    def test_parse_positive_int_rejects_auto_generated_code_and_missing(self):
        with self.assertRaises(ValueError):
            parse_positive_int(None, "customer_id")
        with self.assertRaises(ValueError):
            parse_positive_int("", "customer_id")
        with self.assertRaises(ValueError):
            parse_positive_int("ACC000000001", "customer_id")
        with self.assertRaises(ValueError):
            parse_positive_int("0", "customer_id")
        self.assertEqual(parse_positive_int("42", "customer_id"), 42)

    def test_missing_customer_id_returns_400(self):
        request = self.factory.get("/default/superadmin/CustomerUsageHealthAnalytics/")
        force_authenticate(request, user=self.user)
        response = self.view(request, tenant_name="default")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["status"])

    def test_auto_generated_customer_code_rejected_with_400(self):
        request = self.factory.get(
            "/default/superadmin/CustomerUsageHealthAnalytics/",
            {"customer_id": "ACC000000001"},
        )
        force_authenticate(request, user=self.user)
        response = self.view(request, tenant_name="default")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["status"])
        self.assertIn("integer primary key", response.data["message"])

    @patch("CRMSuperAdmin.views.resolve_customer_account", return_value=None)
    def test_nonexistent_customer_pk_returns_404(self, mock_resolve):
        request = self.factory.get(
            "/default/superadmin/CustomerUsageHealthAnalytics/",
            {"customer_id": 999},
        )
        force_authenticate(request, user=self.user)
        response = self.view(request, tenant_name="default")
        mock_resolve.assert_called_once_with(999)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["status"])

    @patch("CRMSuperAdmin.views.build_customer_usage_health_overview")
    @patch("CRMSuperAdmin.views.resolve_customer_account")
    def test_valid_customer_pk_returns_200_payload(self, mock_resolve, mock_build):
        mock_resolve.return_value = SimpleNamespace(id=12, Account_Id="ACC000000012")
        expected_payload = {
            "customer_id": 12,
            "account_code": "ACC000000012",
            "customer_name": "Acme Academy",
            "product_id": None,
            "period_days": 30,
            "usage_and_adoption": {
                "active_users": {"label": "Active Users", "current": 142, "total": 150, "pct": 95},
                "logins": {"label": "Student Logins", "current": 2436, "total": 2800, "pct": 87},
                "key_modules_used": {"label": "Key Modules Used", "current": 6, "total": 10, "pct": 60},
            },
            "customer_health": {
                "score": 92,
                "status": "Healthy",
                "color": "emerald",
                "open_critical_tickets": 0,
                "checklist": [
                    {"key": "high_adoption", "label": "High Adoption", "passed": True},
                    {"key": "no_open_critical_tickets", "label": "No Open Critical Tickets", "passed": True},
                    {"key": "on_time_payments", "label": "On-time Payments", "passed": True},
                    {"key": "renewal_likely", "label": "Renewal Likely", "passed": True},
                ],
            },
            "usage_trend": {
                "title": "Usage Trend – Active Users",
                "growth_pct": 18,
                "direction": "up",
                "growth_label": "+18% vs. previous period",
                "max_val": 150,
                "monthly_data": [],
            },
        }
        mock_build.return_value = expected_payload

        request = self.factory.get(
            "/default/superadmin/CustomerUsageHealthAnalytics/",
            {"customer_id": 12},
        )
        force_authenticate(request, user=self.user)
        response = self.view(request, tenant_name="default")

        mock_resolve.assert_called_once_with(12)
        mock_build.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["status"])
        self.assertEqual(response.data["data"]["customer_id"], 12)
        self.assertEqual(response.data["data"]["customer_health"]["score"], 92)

    @patch("CRMSuperAdmin.services.customer_overview_service.ModuleMaster")
    @patch("CRMSuperAdmin.services.customer_overview_service.PlanLimit")
    @patch("CRMSuperAdmin.services.customer_overview_service.UserActivity")
    def test_usage_and_adoption_calculations(self, mock_ua, mock_plan_limit, mock_module_master):
        account = SimpleNamespace(
            id=12,
            Product_Id=SimpleNamespace(Product_Code="EDUCATION", Product_Name="Pegatto Education"),
        )
        sub = SimpleNamespace(
            Plan_Id_id=5,
            Product_Id=SimpleNamespace(Product_Code="EDUCATION", Product_Name="Pegatto Education"),
        )
        inst = SimpleNamespace(id=3, product_type="education", Product_Id=sub.Product_Id)

        activity_qs = MagicMock()
        activity_qs.values.return_value.distinct.return_value.count.return_value = 120
        activity_qs.filter.return_value.count.return_value = 2400
        activity_qs.values_list.return_value = [
            ("login", {"module": "attendance"}),
            ("view_dashboard", {"module": "fees"}),
            ("export_report", {"module": "exams"}),
        ]
        mock_ua.objects.filter.return_value = activity_qs

        mock_plan_limit.objects.filter.return_value.filter.return_value.order_by.return_value.first.return_value = SimpleNamespace(
            Limit_Value=2800
        )

        mod_qs = MagicMock()
        matched_qs = MagicMock()
        matched_qs.exists.return_value = True
        matched_qs.count.return_value = 6
        mod_qs.filter.return_value = matched_qs
        mock_module_master.objects.filter.return_value = mod_qs

        result = _compute_usage_and_adoption(
            account=account,
            subscriptions=[sub],
            instances=[inst],
            licensed_seats=150,
            days=30,
        )

        self.assertEqual(result["active_users"], {"label": "Active Users", "current": 120, "total": 150, "pct": 80})
        self.assertEqual(result["logins"], {"label": "Student Logins", "current": 2400, "total": 2800, "pct": 86})
        self.assertEqual(result["key_modules_used"], {"label": "Key Modules Used", "current": 3, "total": 6, "pct": 50})

    @patch("CRMSuperAdmin.services.customer_overview_service.Cancelplans")
    @patch("CRMSuperAdmin.services.customer_overview_service.Payments")
    @patch("CRMSuperAdmin.services.customer_overview_service.Renewal")
    @patch("CRMSuperAdmin.services.customer_overview_service.Invoice")
    @patch("CRMSuperAdmin.services.customer_overview_service._count_open_critical_tickets")
    def test_customer_health_reflects_open_tickets_and_overdue_payments(
        self,
        mock_critical_tickets,
        mock_invoice,
        mock_renewal,
        mock_payments,
        mock_cancel,
    ):
        account = SimpleNamespace(id=12, Organization_Id_id=4)
        all_subs = MagicMock()
        all_subs.filter.return_value.exists.return_value = False
        active_subs = [SimpleNamespace(status="active", end_date=None)]
        usage_data = {"active_users": {"pct": 80}}

        # Case 1: All healthy
        mock_critical_tickets.return_value = 0
        mock_invoice.objects.filter.return_value.filter.return_value.exists.return_value = False
        mock_renewal.objects.filter.return_value.filter.return_value.exists.return_value = False
        mock_payments.objects.filter.return_value.order_by.return_value.first.return_value = SimpleNamespace(status="success")
        mock_cancel.objects.filter.return_value.exists.return_value = False

        healthy = _compute_customer_health(account, all_subs, active_subs, [], usage_data)
        self.assertEqual(healthy["score"], 93)
        self.assertEqual(healthy["status"], "Healthy")
        self.assertTrue(all(item["passed"] for item in healthy["checklist"]))

        # Case 2: Open critical ticket & overdue invoice
        mock_critical_tickets.return_value = 2
        mock_invoice.objects.filter.return_value.filter.return_value.exists.return_value = True

        at_risk = _compute_customer_health(account, all_subs, active_subs, [], usage_data)
        self.assertEqual(at_risk["score"], 28)
        self.assertEqual(at_risk["status"], "At Risk")
        checklist_map = {item["key"]: item["passed"] for item in at_risk["checklist"]}
        self.assertFalse(checklist_map["no_open_critical_tickets"])
        self.assertFalse(checklist_map["on_time_payments"])
        self.assertFalse(checklist_map["renewal_likely"])

    @patch("CRMSuperAdmin.services.customer_overview_service.UserActivity")
    def test_usage_trend_returns_12_months_and_growth(self, mock_ua):
        inst = SimpleNamespace(id=3)
        trend_qs = MagicMock()
        trend_qs.annotate.return_value.values.return_value.annotate.return_value.order_by.return_value = []
        cur_qs = MagicMock()
        cur_qs.values.return_value.distinct.return_value.count.return_value = 118
        prev_qs = MagicMock()
        prev_qs.values.return_value.distinct.return_value.count.return_value = 100
        mock_ua.objects.filter.side_effect = [trend_qs, cur_qs, prev_qs]

        trend = _compute_usage_trend(instances=[inst], licensed_seats=150, days=30, months=12)
        self.assertEqual(len(trend["monthly_data"]), 12)
        self.assertEqual(trend["growth_pct"], 18)
        self.assertEqual(trend["growth_label"], "+18% vs. previous period")
        self.assertEqual(trend["max_val"], 150)

    @patch("CRMSuperAdmin.services.customer_overview_service.TicketManagement")
    def test_open_critical_tickets_uses_icontains_filters(self, mock_ticket_mgmt):
        account = SimpleNamespace(id=12, Organization_Id_id=4)
        inst = SimpleNamespace(id=3, Instance_Request_No="INS-001", Domain_Name="acme.pegatto.com", Database_Name="acme_db")

        ticket_qs = MagicMock()
        ticket_qs.exclude.return_value = ticket_qs
        ticket_qs.count.return_value = 1
        mock_ticket_mgmt.objects.filter.return_value = ticket_qs

        count = _count_open_critical_tickets(account, [inst])
        self.assertEqual(count, 1)
        filter_kwargs = mock_ticket_mgmt.objects.filter.call_args.kwargs
        self.assertEqual(filter_kwargs["Priority__icontains"], "critical")
        exclude_calls = [c.kwargs for c in ticket_qs.exclude.call_args_list]
        self.assertIn({"Ticket_Status__icontains": "fixed"}, exclude_calls)
        self.assertIn({"Ticket_Status__icontains": "closed"}, exclude_calls)
        self.assertIn({"Ticket_Status__icontains": "resolved"}, exclude_calls)

    @patch("CRMSuperAdmin.services.customer_overview_service.Instance_Creation")
    @patch("CRMSuperAdmin.services.customer_overview_service.Subscriptions")
    def test_customer_scope_uses_icontains_and_excludes_inactive(self, mock_subs, mock_inst):
        account = SimpleNamespace(id=12)
        subs_qs = MagicMock()
        active_chain = MagicMock()
        active_chain.exclude.return_value = []
        subs_qs.filter.return_value = active_chain
        subs_qs.__iter__.return_value = iter([])
        mock_subs.objects.select_related.return_value.prefetch_related.return_value.filter.return_value.exclude.return_value = subs_qs
        mock_inst.objects.select_related.return_value.filter.return_value = []

        _get_customer_scope(account)
        active_chain.exclude.assert_called_once_with(status__icontains="inactive")


class SuperAdminDashboardAPITests(SimpleTestCase):
    """Tests for BusinessOverviewDashboardAPI, SystemHealthAPI, and ProductPerformanceDashboardAPI."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_dashboard_urls_resolve(self):
        cases = [
            ("business-overview-dashboard", "/default/superadmin/BusinessOverviewDashboardAPI/", BusinessOverviewDashboardAPI),
            ("system-health-api", "/default/superadmin/SystemHealthAPI/", SystemHealthAPI),
            ("product-performance-dashboard", "/default/superadmin/ProductPerformanceDashboardAPI/", ProductPerformanceDashboardAPI),
        ]
        for name, expected_path, view_cls in cases:
            url = reverse(name, kwargs={"tenant_name": "default"})
            self.assertEqual(url, expected_path)
            self.assertEqual(resolve(url).func.view_class, view_cls)

    def test_parse_dashboard_filters_enforces_pk_ids_and_validates_params(self):
        filters = parse_dashboard_filters(
            {
                "date_range": "last_30_days",
                "product_id": "5",
                "partner_id": "9",
                "country": "India",
                "customer_type": "partner",
            }
        )
        self.assertEqual(filters["product_id"], 5)
        self.assertEqual(filters["partner_id"], 9)
        self.assertEqual(filters["country"], "India")
        self.assertEqual(filters["customer_type"], "partner")

        with self.assertRaises(ValueError):
            parse_dashboard_filters({"product_id": "EDU-001"})
        with self.assertRaises(ValueError):
            parse_dashboard_filters({"partner_id": "PAR000000001"})
        with self.assertRaises(ValueError):
            parse_dashboard_filters({"customer_type": "invalid_type"})

    def test_apply_account_scope_uses_icontains_for_country(self):
        qs = MagicMock()
        qs.filter.return_value = qs
        filters = parse_dashboard_filters({"country": "India", "product_id": "2", "partner_id": "7", "customer_type": "partner"})
        _apply_account_scope(qs, filters)
        filter_calls = [c.kwargs for c in qs.filter.call_args_list]
        self.assertIn({"Product_Id_id": 2}, filter_calls)
        self.assertIn({"Partner_Id_id": 7}, filter_calls)
        self.assertIn({"Country__icontains": "India"}, filter_calls)
        self.assertIn({"Partner_Id__isnull": False}, filter_calls)

    @patch("CRMSuperAdmin.DashboardService.superadmin_dashboard_service.TicketManagement")
    def test_open_tickets_excludes_closed_via_icontains(self, mock_ticket):
        qs = MagicMock()
        qs.exclude.return_value = qs
        qs.count.return_value = 14
        mock_ticket.objects.filter.return_value = qs

        filters = parse_dashboard_filters({})
        self.assertEqual(_compute_open_tickets(filters), 14)
        exclude_calls = [c.kwargs for c in qs.exclude.call_args_list]
        self.assertIn({"Ticket_Status__icontains": "fixed"}, exclude_calls)
        self.assertIn({"Ticket_Status__icontains": "closed"}, exclude_calls)
        self.assertIn({"Ticket_Status__icontains": "resolved"}, exclude_calls)

    def test_mrr_arr_normalizes_monthly_and_yearly_subscriptions(self):
        monthly_sub = SimpleNamespace(SuscriptionAmount=100000, SubscriptionPeriod="monthly", Plan_Id=None)
        yearly_sub = SimpleNamespace(SuscriptionAmount=1200000, SubscriptionPeriod="yearly", Plan_Id=None)
        mrr, arr = _compute_mrr_arr_from_subs([monthly_sub, yearly_sub])
        self.assertEqual(mrr, 200000.0)
        self.assertEqual(arr, 2400000.0)
        self.assertEqual(_format_inr(6680000), "₹ 66.8 L")
        self.assertEqual(_format_inr(80200000), "₹ 8.02 Cr")

    @patch("CRMSuperAdmin.views.build_business_overview_dashboard")
    def test_business_overview_api_returns_200_and_rejects_bad_pk(self, mock_build):
        view = BusinessOverviewDashboardAPI.as_view()
        mock_build.return_value = {"kpis": {"total_registered_tenants": {"value": 10}}}

        bad_req = self.factory.get("/default/superadmin/BusinessOverviewDashboardAPI/", {"product_id": "CRM-01"})
        force_authenticate(bad_req, user=self.user)
        bad_resp = view(bad_req, tenant_name="default")
        self.assertEqual(bad_resp.status_code, 400)
        self.assertFalse(bad_resp.data["status"])

        ok_req = self.factory.get("/default/superadmin/BusinessOverviewDashboardAPI/", {"product_id": 3, "partner_id": 4})
        force_authenticate(ok_req, user=self.user)
        ok_resp = view(ok_req, tenant_name="default")
        self.assertEqual(ok_resp.status_code, 200)
        self.assertTrue(ok_resp.data["status"])
        self.assertEqual(mock_build.call_args[0][0]["product_id"], 3)
        self.assertEqual(mock_build.call_args[0][0]["partner_id"], 4)

    @patch("CRMSuperAdmin.views.build_product_performance_dashboard")
    def test_product_performance_api_returns_200(self, mock_build):
        view = ProductPerformanceDashboardAPI.as_view()
        mock_build.return_value = {"product_summary_table": {"rows": [], "totals": {}}}

        req = self.factory.get("/default/superadmin/ProductPerformanceDashboardAPI/", {"date_range": "last_90_days"})
        force_authenticate(req, user=self.user)
        resp = view(req, tenant_name="default")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["status"])

    @patch("CRMSuperAdmin.views.get_system_health")
    def test_system_health_api_returns_200(self, mock_health):
        view = SystemHealthAPI.as_view()
        mock_health.return_value = {"last_updated": "2026-11-25T16:00:00Z", "services": []}

        req = self.factory.get("/default/superadmin/SystemHealthAPI/")
        force_authenticate(req, user=self.user)
        resp = view(req, tenant_name="default")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["status"])


class CustomerAndPartnerKpiAPITests(SimpleTestCase):
    """Tests for CustomerKpiDashboardAPI and PartnerKpiDashboardAPI."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_customer_and_partner_kpi_urls_resolve(self):
        c_url = reverse("customer-kpi-dashboard", kwargs={"tenant_name": "default"})
        p_url = reverse("partner-kpi-dashboard", kwargs={"tenant_name": "default"})
        self.assertEqual(c_url, "/default/superadmin/CustomerKpiDashboardAPI/")
        self.assertEqual(p_url, "/default/superadmin/PartnerKpiDashboardAPI/")
        self.assertEqual(resolve(c_url).func.view_class, CustomerKpiDashboardAPI)
        self.assertEqual(resolve(p_url).func.view_class, PartnerKpiDashboardAPI)

    def test_partner_type_filter_parsed_and_applied_with_icontains(self):
        qs = MagicMock()
        qs.filter.return_value = qs
        filters = parse_dashboard_filters({"partner_type": "Gold", "product_id": 2})
        self.assertEqual(filters["partner_type"], "Gold")
        _apply_account_scope(qs, filters)
        self.assertTrue(qs.filter.called)

    def test_customer_segmentation_percentages_sum_correctly(self):
        core = {
            "total_tenants": 100,
            "free_core_tenants": 60,
            "paying_tenants": 10,
            "trial_tenants": 5,
        }
        seg = _build_customer_segmentation(core)
        self.assertEqual(seg["total_customers"], 100)
        by_key = {s["key"]: s for s in seg["segments"]}
        self.assertEqual(by_key["free_core"]["pct"], 60.0)
        self.assertEqual(by_key["paying"]["pct"], 10.0)
        self.assertEqual(by_key["trial"]["pct"], 5.0)
        self.assertEqual(by_key["inactive"]["count"], 25)
        self.assertEqual(by_key["inactive"]["pct"], 25.0)

    def test_top_customers_by_arr_orders_and_returns_pk(self):
        filters = parse_dashboard_filters({})
        acc1 = SimpleNamespace(id=101, Organization_Name="Euro Textiles", Organization_Id=None, Contact_Name="A", Product_Id=SimpleNamespace(id=1, Product_Name="CRM", Product_Code="CRM"))
        acc2 = SimpleNamespace(id=102, Organization_Name="Knowledge School", Organization_Id=None, Contact_Name="B", Product_Id=SimpleNamespace(id=2, Product_Name="Education", Product_Code="EDU"))
        sub1 = SimpleNamespace(Customer_Id_id=101, Customer_Id=acc1, Product_Id=acc1.Product_Id, Plan_Id=None, SuscriptionAmount=300000, SubscriptionPeriod="monthly", Created_Date=filters["prev_end_dt"])
        sub2 = SimpleNamespace(Customer_Id_id=102, Customer_Id=acc2, Product_Id=acc2.Product_Id, Plan_Id=None, SuscriptionAmount=2800000, SubscriptionPeriod="yearly", Created_Date=filters["end_dt"])

        subs_qs = MagicMock()
        subs_qs.filter.return_value.exclude.return_value.filter.return_value.select_related.return_value = [sub1, sub2]
        rows = _build_top_customers_by_arr({"subs_qs": subs_qs}, filters, limit=5)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["customer_id"], 101)
        self.assertEqual(rows[0]["arr"], 3600000.0)
        self.assertEqual(rows[0]["arr_formatted"], "₹ 36.0 L")
        self.assertEqual(rows[1]["customer_id"], 102)
        self.assertEqual(rows[1]["growth_yoy_pct"], 100)

    @patch("CRMSuperAdmin.DashboardService.customer_partner_kpi_service.Account")
    def test_top_partners_by_revenue_contribution(self, mock_account):
        filters = parse_dashboard_filters({})
        p1 = SimpleNamespace(id=11, Trade_Name="Vyabi Solutions", Legal_Name="Vyabi", Tier="Gold", Partner_Type="Reseller")
        p2 = SimpleNamespace(id=12, Trade_Name="Calsoft Systems", Legal_Name="Calsoft", Tier="Silver", Partner_Type="Reseller")

        mock_account.objects.filter.return_value.values.return_value.annotate.return_value.values_list.return_value = [
            (11, 46),
            (12, 24),
        ]
        sub1 = SimpleNamespace(Customer_Id=SimpleNamespace(Partner_Id_id=11), SuscriptionAmount=3000000, SubscriptionPeriod="yearly", Plan_Id=None)
        sub2 = SimpleNamespace(Customer_Id=SimpleNamespace(Partner_Id_id=12), SuscriptionAmount=1000000, SubscriptionPeriod="yearly", Plan_Id=None)

        subs_qs = MagicMock()
        subs_qs.filter.return_value.exclude.return_value.filter.return_value.select_related.return_value = [sub1, sub2]

        rows = _build_top_partners_by_revenue([p1, p2], {"subs_qs": subs_qs}, filters, limit=5)
        self.assertEqual(rows[0]["partner_id"], 11)
        self.assertEqual(rows[0]["partner_type"], "Gold")
        self.assertEqual(rows[0]["contribution_pct"], 75.0)
        self.assertEqual(rows[1]["partner_id"], 12)
        self.assertEqual(rows[1]["contribution_pct"], 25.0)

    @patch("CRMSuperAdmin.views.build_partner_kpi_dashboard")
    @patch("CRMSuperAdmin.views.build_customer_kpi_dashboard")
    def test_customer_and_partner_kpi_views_return_200(self, mock_cust, mock_part):
        mock_cust.return_value = {"customer_kpis": {"total_customers": {"value": 100}}}
        mock_part.return_value = {"partner_kpis": {"total_partners": {"value": 25}}}

        c_req = self.factory.get("/default/superadmin/CustomerKpiDashboardAPI/", {"product_id": 1, "partner_type": "Gold"})
        force_authenticate(c_req, user=self.user)
        c_resp = CustomerKpiDashboardAPI.as_view()(c_req, tenant_name="default")
        self.assertEqual(c_resp.status_code, 200)
        self.assertTrue(c_resp.data["status"])

        p_req = self.factory.get("/default/superadmin/PartnerKpiDashboardAPI/", {"partner_type": "Silver"})
        force_authenticate(p_req, user=self.user)
        p_resp = PartnerKpiDashboardAPI.as_view()(p_req, tenant_name="default")
        self.assertEqual(p_resp.status_code, 200)
        self.assertTrue(p_resp.data["status"])


class RevenueSubscriptionAnalyticsAPITests(SimpleTestCase):
    """Tests for RevenueSubscriptionAnalyticsDashboardAPI."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_revenue_subscription_url_resolves(self):
        url = reverse("revenue-subscription-analytics-dashboard", kwargs={"tenant_name": "default"})
        self.assertEqual(url, "/default/superadmin/RevenueSubscriptionAnalyticsDashboardAPI/")
        self.assertEqual(resolve(url).func.view_class, RevenueSubscriptionAnalyticsDashboardAPI)

    @patch("CRMSuperAdmin.DashboardService.revenue_subscription_analytics_service.InvoiceLineItem")
    def test_subscription_revenue_uses_icontains_and_excludes_addon(self, mock_line_item):
        filters = parse_dashboard_filters({"country": "India", "product_id": 2})
        chain = MagicMock()
        chain.exclude.return_value = chain
        chain.filter.return_value = chain
        chain.aggregate.return_value = {"total": 67800000.0}
        mock_line_item.objects.filter.return_value = chain

        total = _compute_subscription_revenue(filters, filters["start_dt"], filters["end_dt"])
        self.assertEqual(total, 67800000.0)
        self.assertEqual(mock_line_item.objects.filter.call_args.kwargs["Invoice_Id__Payment_Status__icontains"], "paid")
        chain.exclude.assert_called_once_with(Item_Type__icontains="addon")

    @patch("CRMSuperAdmin.DashboardService.revenue_subscription_analytics_service.Renewal")
    def test_filtered_renewals_uses_icontains(self, mock_renewal):
        qs = MagicMock()
        qs.filter.return_value = qs
        mock_renewal.objects.filter.return_value = qs
        filters = parse_dashboard_filters({"country": "India", "partner_type": "Gold", "product_id": 4})

        _filtered_renewals_qs(filters)
        calls = [c.kwargs for c in qs.filter.call_args_list]
        self.assertIn({"Product_Id_id": 4}, calls)
        self.assertIn({"Customer_Id__Country__icontains": "India"}, calls)

    def test_revenue_by_subscription_plan_groups_and_calculates_pct(self):
        filters = parse_dashboard_filters({})
        sub_pro = SimpleNamespace(Plan_Id_id=1, Plan_Id=SimpleNamespace(Plan_Name="Professional", billing_cycle="yearly"), Plan_Name="Professional", is_trial=False, SuscriptionAmount=600000, SubscriptionPeriod="yearly")
        sub_basic = SimpleNamespace(Plan_Id_id=2, Plan_Id=SimpleNamespace(Plan_Name="Basic", billing_cycle="yearly"), Plan_Name="Basic", is_trial=False, SuscriptionAmount=400000, SubscriptionPeriod="yearly")
        sub_free = SimpleNamespace(Plan_Id_id=3, Plan_Id=SimpleNamespace(Plan_Name="Free Core (Non-paid)", billing_cycle="monthly"), Plan_Name="Free Core (Non-paid)", is_trial=False, SuscriptionAmount=0, SubscriptionPeriod="monthly")

        subs_qs = MagicMock()
        subs_qs.filter.return_value.exclude.return_value.filter.return_value.select_related.return_value = [sub_pro, sub_basic, sub_free]

        result = _build_revenue_by_plan(subs_qs, filters["end_dt"])
        self.assertEqual(result["total_revenue"], 1000000.0)
        by_name = {s["plan_name"]: s for s in result["segments"]}
        self.assertEqual(by_name["Professional"]["pct"], 60.0)
        self.assertEqual(by_name["Basic"]["pct"], 40.0)
        self.assertEqual(by_name["Free Core (Non-paid)"]["pct"], 0.0)

    @patch("CRMSuperAdmin.views.build_revenue_subscription_analytics_dashboard")
    def test_revenue_subscription_api_view_returns_200_and_validates_pk(self, mock_build):
        view = RevenueSubscriptionAnalyticsDashboardAPI.as_view()
        mock_build.return_value = {"kpis": {"total_revenue": {"value": 80200000.0}}}

        bad_req = self.factory.get("/default/superadmin/RevenueSubscriptionAnalyticsDashboardAPI/", {"product_id": "PRO-01"})
        force_authenticate(bad_req, user=self.user)
        self.assertEqual(view(bad_req, tenant_name="default").status_code, 400)

        ok_req = self.factory.get("/default/superadmin/RevenueSubscriptionAnalyticsDashboardAPI/", {"product_id": 1, "partner_id": 2})
        force_authenticate(ok_req, user=self.user)
        ok_resp = view(ok_req, tenant_name="default")
        self.assertEqual(ok_resp.status_code, 200)
        self.assertTrue(ok_resp.data["status"])

    def test_from_and_to_date_without_date_range_switches_to_custom(self):
        filters = parse_dashboard_filters({"from_date": "2026-11-01", "to_date": "2026-11-26"})
        self.assertEqual(filters["date_range"], "custom")
        self.assertEqual(str(filters["start_date"]), "2026-11-01")
        self.assertEqual(str(filters["end_date"]), "2026-11-26")

    def test_plan_customer_distribution_deduplicates_plan_id(self):
        filters = parse_dashboard_filters({})
        plan_obj = SimpleNamespace(Plan_Name="Premiumlan")
        s1 = SimpleNamespace(Plan_Id_id=2, Plan_Id=plan_obj, Plan_Name="Premiumlan", Customer_Id_id=10)
        s2 = SimpleNamespace(Plan_Id_id=2, Plan_Id=plan_obj, Plan_Name="", Customer_Id_id=11)
        s3 = SimpleNamespace(Plan_Id_id=2, Plan_Id=plan_obj, Plan_Name=None, Customer_Id_id=10)

        subs_qs = MagicMock()
        subs_qs.filter.return_value.exclude.return_value.filter.return_value.select_related.return_value = [s1, s2, s3]

        dist = _build_plan_customer_distribution(subs_qs, filters["end_dt"])
        self.assertEqual(dist["total_active_tenants"], 2)
        self.assertEqual(len(dist["segments"]), 1)
        self.assertEqual(dist["segments"][0]["plan_id"], 2)
        self.assertEqual(dist["segments"][0]["customers_count"], 2)

    @patch("CRMSuperAdmin.views.build_partner_kpi_dashboard")
    @patch("CRMSuperAdmin.views.build_customer_kpi_dashboard")
    @patch("CRMSuperAdmin.views.build_product_performance_dashboard")
    @patch("CRMSuperAdmin.views.build_business_overview_dashboard")
    def test_custom_from_to_date_works_across_all_four_dashboard_apis(
        self, mock_biz, mock_prod, mock_cust, mock_part
    ):
        mock_biz.return_value = {}
        mock_prod.return_value = {}
        mock_cust.return_value = {}
        mock_part.return_value = {}

        params = {
            "date_range": "last_12_months",
            "from_date": "2026-11-01",
            "to_date": "2026-11-26",
        }
        endpoints = [
            ("/default/superadmin/BusinessOverviewDashboardAPI/", BusinessOverviewDashboardAPI.as_view(), mock_biz),
            ("/default/superadmin/ProductPerformanceDashboardAPI/", ProductPerformanceDashboardAPI.as_view(), mock_prod),
            ("/default/superadmin/CustomerKpiDashboardAPI/", CustomerKpiDashboardAPI.as_view(), mock_cust),
            ("/default/superadmin/PartnerKpiDashboardAPI/", PartnerKpiDashboardAPI.as_view(), mock_part),
        ]
        for path, view_fn, mock_builder in endpoints:
            req = self.factory.get(path, params)
            force_authenticate(req, user=self.user)
            resp = view_fn(req, tenant_name="default")
            self.assertEqual(resp.status_code, 200)
            passed_filters = mock_builder.call_args[0][0]
            self.assertEqual(passed_filters["date_range"], "custom")
            self.assertEqual(str(passed_filters["start_date"]), "2026-11-01")
            self.assertEqual(str(passed_filters["end_date"]), "2026-11-26")


class SystemHealthAlertsDashboardAPITests(SimpleTestCase):
    """Tests for SystemHealthAlertsDashboardAPI."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_system_health_alerts_url_resolves(self):
        url = reverse("system-health-alerts-dashboard", kwargs={"tenant_name": "default"})
        self.assertEqual(url, "/default/superadmin/SystemHealthAlertsDashboardAPI/")
        self.assertEqual(resolve(url).func.view_class, SystemHealthAlertsDashboardAPI)

    def test_parse_system_health_filters_defaults_30d_and_accepts_custom_dates(self):
        default_f = parse_system_health_filters({})
        self.assertEqual(default_f["date_range"], "last_30_days")

        custom_f = parse_system_health_filters(
            {"from_date": "2026-11-01", "to_date": "2026-11-26", "service_name": "postgres", "status": "healthy", "severity": "low"}
        )
        self.assertEqual(custom_f["date_range"], "custom")
        self.assertEqual(custom_f["service_name"], "postgres")
        self.assertEqual(custom_f["status"], "healthy")
        self.assertEqual(custom_f["severity"], "low")

    @patch("CRMSuperAdmin.DashboardService.system_health_service.TenantProvisioningJob")
    @patch("CRMSuperAdmin.DashboardService.system_health_service.TicketManagement")
    def test_active_alerts_uses_icontains_and_includes_degraded_services(self, mock_ticket, mock_prov):
        ticket_qs = MagicMock()
        ticket_qs.exclude.return_value = ticket_qs
        ticket_qs.order_by.return_value = []
        mock_ticket.objects.filter.return_value = ticket_qs

        mock_prov.objects.filter.return_value.order_by.return_value = []

        filters = parse_system_health_filters({"service_name": "Email", "severity": "Medium"})
        services = [
            {
                "id": 7,
                "service_name": "Email / Notification Service",
                "status": "Degraded",
                "api_error_rate_pct": 2.4,
                "avg_latency_ms": 415,
                "last_heartbeat": "2026-11-26T10:00:00Z",
                "queue_backlog": None,
            },
            {
                "id": 3,
                "service_name": "Database (PostgreSQL)",
                "status": "Healthy",
                "api_error_rate_pct": 0.0,
                "avg_latency_ms": 12,
                "last_heartbeat": "2026-11-26T10:00:00Z",
                "queue_backlog": 0,
            },
        ]
        alerts = _build_active_alerts(services, filters)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["service_name"], "Email / Notification Service")
        self.assertEqual(alerts[0]["severity"], "Medium")
        self.assertEqual(mock_ticket.objects.filter.call_args.kwargs["Priority__icontains"], "critical")
        self.assertEqual(mock_prov.objects.filter.call_args.kwargs["status__icontains"], "fail")

    @patch("CRMSuperAdmin.views.build_system_health_alerts_dashboard")
    def test_system_health_alerts_view_returns_200(self, mock_build):
        view = SystemHealthAlertsDashboardAPI.as_view()
        mock_build.return_value = {"kpis": {"total_services": 9}}

        req = self.factory.get(
            "/default/superadmin/SystemHealthAlertsDashboardAPI/",
            {"from_date": "2026-11-01", "to_date": "2026-11-26", "service_name": "Celery"},
        )
        force_authenticate(req, user=self.user)
        resp = view(req, tenant_name="default")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["status"])
        self.assertEqual(mock_build.call_args[0][0]["date_range"], "custom")
        self.assertEqual(mock_build.call_args[0][0]["service_name"], "Celery")


class PlanByEditionListAPITests(SimpleTestCase):
    """Tests for Planlistwithoutpaginaton API filtering by ProductEdition_id."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_plan_list_without_pagination_url_resolves(self):
        url = reverse("plan-list-without-pagination", kwargs={"tenant_name": "default"})
        self.assertEqual(url, "/default/superadmin/Planlistwithoutpaginaton/")
        self.assertEqual(resolve(url).func.view_class, Planlistwithoutpaginaton)

    @patch("CRMSuperAdmin.views.Planserializer")
    @patch("CRMSuperAdmin.views.filter_by_product", side_effect=lambda qs, req: qs)
    @patch("CRMSuperAdmin.views.Plan")
    def test_filters_by_edition_pk_id_and_icontains_string(self, mock_plan, mock_filter_prod, mock_ser):
        view = Planlistwithoutpaginaton.as_view()
        base_qs = MagicMock()
        base_qs.filter.return_value = base_qs
        base_qs.order_by.return_value = []
        mock_plan.objects.filter.return_value = base_qs
        mock_ser.return_value.data = [{"id": 1, "Plan_Name": "Starter", "ProductEdition_id": 5}]

        # 1. Numeric PK id
        req_pk = self.factory.get("/default/superadmin/Planlistwithoutpaginaton/", {"ProductEdition_id": "5"})
        force_authenticate(req_pk, user=self.user)
        resp_pk = view(req_pk, tenant_name="default")
        self.assertEqual(resp_pk.status_code, 200)
        base_qs.filter.assert_called_with(ProductEdition_id_id=5)

        # 2. String fallback via icontains
        base_qs.filter.reset_mock()
        req_str = self.factory.get("/default/superadmin/Planlistwithoutpaginaton/", {"edition": "Enterprise"})
        force_authenticate(req_str, user=self.user)
        resp_str = view(req_str, tenant_name="default")
        self.assertEqual(resp_str.status_code, 200)
        self.assertTrue(base_qs.filter.called)


class ProductMasterLookupsAPITests(SimpleTestCase):
    """Tests for ProductMasterLookupsAPIView returning ProductCategory name."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    @patch("CRMSuperAdmin.views.ProductMaster")
    def test_lookups_include_category_name_from_product_category(self, mock_pm):
        import json

        cat = SimpleNamespace(id=3, Category_Name="Business Suite")
        p1 = SimpleNamespace(
            id=1,
            Product_Code="CRM",
            Product_Name="Pegatto CRM",
            Category_id_id=3,
            Category_id=cat,
            Category="Legacy",
        )
        p2 = SimpleNamespace(
            id=2,
            Product_Code="EDU",
            Product_Name="Pegatto Education",
            Category_id_id=None,
            Category_id=None,
            Category="Education",
        )
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = [p1, p2]
        mock_pm.objects.select_related.return_value = qs

        req = self.factory.get("/default/superadmin/ProductMasterLookups/")
        force_authenticate(req, user=self.user)
        resp = ProductMasterLookupsAPIView.as_view()(req, tenant_name="default")

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["status"])
        self.assertEqual(body["count"], 2)
        self.assertEqual(body["results"][0]["Category_id"], 3)
        self.assertEqual(body["results"][0]["Category_Name"], "Business Suite")
        self.assertEqual(body["results"][0]["Category"], "Business Suite")
        self.assertEqual(body["results"][1]["Category_id"], None)
        self.assertEqual(body["results"][1]["Category_Name"], "Education")


class LicenseEntitlementManagementTests(SimpleTestCase):
    """Tests for LicenseMaster, LicenseEntitlement, LicenseAssignment, LicenseRenewal CRUD, Filter, Action & KPI APIs."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_license_urls_resolve(self):
        from CRMSuperAdmin.views import (
            LicenseActionAPI,
            LicenseAssignmentCRUD,
            LicenseEntitlementCRUD,
            LicenseEntitlementKPIAPI,
            LicenseLookupsAPI,
            LicenseMasterCRUD,
            LicenseMasterExportAPI,
            LicenseMasterFilter,
            LicenseMasterKPIAPI,
            LicenseMasterListwithPagination,
            LicenseMasterSearch,
            LicenseMasterlistwithoutpaginaton,
            LicenseRenewalCRUD,
            LicenseUsageComplianceAPI,
        )

        cases = [
            ("license-master-crud", LicenseMasterCRUD),
            ("license-master-list-paginated", LicenseMasterListwithPagination),
            ("license-master-search", LicenseMasterSearch),
            ("license-master-list-without-pagination", LicenseMasterlistwithoutpaginaton),
            ("license-master-filter", LicenseMasterFilter),
            ("license-master-kpi", LicenseMasterKPIAPI),
            ("license-action", LicenseActionAPI),
            ("license-usage-compliance", LicenseUsageComplianceAPI),
            ("license-lookups", LicenseLookupsAPI),
            ("license-master-export", LicenseMasterExportAPI),
            ("license-entitlement-crud", LicenseEntitlementCRUD),
            ("license-entitlement-kpi", LicenseEntitlementKPIAPI),
            ("license-assignment-crud", LicenseAssignmentCRUD),
            ("license-renewal-crud", LicenseRenewalCRUD),
        ]
        for name, view_cls in cases:
            url = reverse(name, kwargs={"tenant_name": "default"})
            self.assertEqual(resolve(url).func.view_class, view_cls)

    def test_apply_license_scope_uses_icontains_not_iexact(self):
        from CRMSuperAdmin.views import _apply_license_scope

        qs = MagicMock()
        qs.filter.return_value = qs

        _apply_license_scope(
            qs,
            {
                "Product": "CRM",
                "Plan_Edition": "Professional",
                "Status": "Active",
                "Customer_Id": "Euro Textiles",
                "License_Type": "Subscription",
                "License_Key": "PGT-CRM",
                "search": "Euro",
            },
        )
        filter_text = " ".join(str(c) for c in qs.filter.call_args_list)
        self.assertIn("icontains", filter_text)
        self.assertNotIn("iexact", filter_text)

    @patch("CRMSuperAdmin.views.LicenseRenewal")
    @patch("CRMSuperAdmin.views.LicenseAssignment")
    @patch("CRMSuperAdmin.views.LicenseEntitlement")
    @patch("CRMSuperAdmin.views.LicenseMaster")
    def test_license_kpi_api_returns_4_cards_and_metrics(
        self, mock_lic, mock_ent, mock_assign, mock_ren
    ):
        import json
        from CRMSuperAdmin.views import LicenseMasterKPIAPI

        base_qs = MagicMock()
        base_qs.filter.return_value = base_qs
        base_qs.distinct.return_value = base_qs
        base_qs.count.side_effect = [10, 1, 1, 2, 1, 7, 3]
        base_qs.aggregate.return_value = {"entitled": 250, "assigned": 180}
        ann_qs = MagicMock()
        ann_qs.__iter__.return_value = iter([])
        ann_qs.order_by.return_value = []
        base_qs.values.return_value.annotate.return_value = ann_qs

        mock_lic.objects.filter.return_value = base_qs
        mock_ent.objects.filter.return_value.count.return_value = 12
        mock_assign.objects.filter.return_value.count.return_value = 5
        mock_ren.objects.filter.return_value.count.return_value = 2

        req = self.factory.get("/default/superadmin/LicenseMasterKPI/")
        force_authenticate(req, user=self.user)
        resp = LicenseMasterKPIAPI.as_view()(req, tenant_name="default")

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["status"])
        self.assertEqual(body["total_licenses"], 10)
        self.assertEqual(body["active_licenses"], 7)
        self.assertEqual(body["expiring_30_days"], 3)
        self.assertEqual(body["suspended_revoked"], 2)
        self.assertEqual(len(body["cards"]), 4)
        self.assertEqual(body["seat_utilization_pct"], 72.0)

    def test_license_serializer_resolves_fks_with_icontains(self):
        from CRMSuperAdmin.serializer import _LicenseAuditSerializerMixin

        model_cls = MagicMock()
        model_cls.objects.filter.return_value.order_by.return_value.first.return_value = SimpleNamespace(id=42)

        resolved = _LicenseAuditSerializerMixin._resolve_fk_pk(
            model_cls, "Euro", "Organization_Name", "Contact_Name"
        )
        self.assertEqual(resolved, 42)
        filter_text = str(model_cls.objects.filter.call_args)
        self.assertIn("icontains", filter_text)
        self.assertNotIn("iexact", filter_text)


class TrialConfigurationTests(SimpleTestCase):
    """Tests for single-table TrialConfiguration CRUD, Filter, Search & KPI APIs."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_trial_configuration_urls_resolve(self):
        from CRMSuperAdmin.views import (
            TrialConfigurationCRUD,
            TrialConfigurationFilter,
            TrialConfigurationKPIAPI,
            TrialConfigurationListwithPagination,
            TrialConfigurationSearch,
            TrialConfigurationlistwithoutpaginaton,
        )

        cases = [
            ("trial-configuration-crud", TrialConfigurationCRUD),
            ("trial-configuration-list-paginated", TrialConfigurationListwithPagination),
            ("trial-configuration-search", TrialConfigurationSearch),
            ("trial-configuration-list-without-pagination", TrialConfigurationlistwithoutpaginaton),
            ("trial-configuration-filter", TrialConfigurationFilter),
            ("trial-configuration-kpi", TrialConfigurationKPIAPI),
        ]
        for name, view_cls in cases:
            url = reverse(name, kwargs={"tenant_name": "default"})
            self.assertEqual(resolve(url).func.view_class, view_cls)

    def test_apply_trial_configuration_scope_uses_icontains(self):
        from CRMSuperAdmin.views import _apply_trial_configuration_scope

        qs = MagicMock()
        qs.filter.return_value = qs

        _apply_trial_configuration_scope(
            qs,
            {
                "Trial_Plan_Name": "Custom Product Trial",
                "Product": "CRM",
                "Edition": "Standard",
                "Plan": "Standard",
                "Category": "Business",
                "Status": "Draft",
                "Feature_Scope": "Select Features",
                "search": "Custom",
            },
        )
        filter_text = " ".join(str(c) for c in qs.filter.call_args_list)
        self.assertIn("icontains", filter_text)
        self.assertNotIn("iexact", filter_text)

    @patch("CRMSuperAdmin.views.Subscriptions")
    @patch("CRMSuperAdmin.views.TrialConfiguration")
    def test_trial_configuration_kpi_returns_4_cards(self, mock_tc, mock_subs):
        import json
        from CRMSuperAdmin.views import TrialConfigurationKPIAPI

        tc_qs = MagicMock()
        tc_qs.filter.return_value = tc_qs
        tc_qs.count.side_effect = [7, 6, 1, 0]
        tc_qs.aggregate.return_value = {"avg_days": 14.0}
        ann_qs = MagicMock()
        ann_qs.__iter__.return_value = iter([])
        ann_qs.order_by.return_value = []
        tc_qs.values.return_value.annotate.return_value = ann_qs
        mock_tc.objects.filter.return_value = tc_qs

        sub_qs = MagicMock()
        sub_qs.filter.return_value = sub_qs
        sub_qs.exclude.return_value = sub_qs
        sub_qs.count.side_effect = [1284, 1000, 680]
        mock_subs.objects.filter.return_value = sub_qs

        req = self.factory.get("/default/superadmin/TrialConfigurationKPI/")
        force_authenticate(req, user=self.user)
        resp = TrialConfigurationKPIAPI.as_view()(req, tenant_name="default")

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["status"])
        self.assertEqual(body["active_trial_plans"], 6)
        self.assertEqual(body["trials_in_progress"], 1284)
        self.assertEqual(body["trial_conversions_pct"], 68.0)
        self.assertEqual(body["trial_conversions_label"], "68%")
        self.assertEqual(body["average_trial_duration_days"], 14.0)
        self.assertEqual(body["average_trial_duration_label"], "14 Days")
        self.assertEqual(len(body["cards"]), 4)


class ModuleMasterLookupsAPITests(SimpleTestCase):
    """Tests for ModuleMasterLookupsAPIView filtering by Category & Product without pagination."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_module_master_lookups_url_resolves(self):
        from CRMSuperAdmin.views import ModuleMasterLookupsAPIView

        url = reverse("module-master-lookups", kwargs={"tenant_name": "default"})
        self.assertEqual(url, "/default/superadmin/ModuleMasterLookups/")
        self.assertEqual(resolve(url).func.view_class, ModuleMasterLookupsAPIView)

    @patch("CRMSuperAdmin.views.ModuleMaster")
    def test_filters_by_category_and_product_using_icontains_without_pagination(self, mock_mm):
        import json
        from CRMSuperAdmin.views import ModuleMasterLookupsAPIView

        cat = SimpleNamespace(id=3, Category_Name="Business Suite")
        prod = SimpleNamespace(id=5, Product_Code="CRM", Product_Name="Pegatto CRM", Category_id_id=3, Category_id=cat, Category="Business Suite")
        mod = SimpleNamespace(
            id=11,
            ModuleMasterId="MOD000000011",
            Module_Code="LEADS",
            Module_name="Leads Management",
            Module_Type="Core",
            Module_key="leads",
            Description="Lead tracking",
            Status="Active",
            Product_Id_id=5,
            Product_Id=prod,
            ProductCategory_id_id=3,
            ProductCategory_id=cat,
            ProductCategory="Business Suite",
        )
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.distinct.return_value = qs
        qs.order_by.return_value = qs
        qs.__iter__.return_value = iter([mod])
        mock_mm.objects.select_related.return_value = qs

        req = self.factory.get(
            "/default/superadmin/ModuleMasterLookups/",
            {"Category_id": "3", "Category_Name": "Business", "Product_Id": "CRM"},
        )
        force_authenticate(req, user=self.user)
        resp = ModuleMasterLookupsAPIView.as_view()(req, tenant_name="default")

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["status"])
        self.assertEqual(body["count"], 1)
        self.assertNotIn("next", body)
        self.assertNotIn("previous", body)
        self.assertEqual(body["results"][0]["Module_Name"], "Leads Management")
        self.assertEqual(body["results"][0]["Product_id"], 5)
        self.assertEqual(body["results"][0]["Category_id"], 3)
        self.assertEqual(body["results"][0]["Category_Name"], "Business Suite")

        filter_text = " ".join(str(c) for c in qs.filter.call_args_list)
        self.assertIn("icontains", filter_text)
        self.assertNotIn("iexact", filter_text)


class EditionAndPlanLookupsAPITests(SimpleTestCase):
    """Tests for ProductEditionLookupsAPIView and PlanLookupsAPIView."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_edition_and_plan_lookup_urls_resolve(self):
        from CRMSuperAdmin.views import PlanLookupsAPIView, ProductEditionLookupsAPIView

        ed_url = reverse("product-edition-lookups", kwargs={"tenant_name": "default"})
        pl_url = reverse("plan-lookups", kwargs={"tenant_name": "default"})
        self.assertEqual(ed_url, "/default/superadmin/ProductEditionLookups/")
        self.assertEqual(pl_url, "/default/superadmin/PlanLookups/")
        self.assertEqual(resolve(ed_url).func.view_class, ProductEditionLookupsAPIView)
        self.assertEqual(resolve(pl_url).func.view_class, PlanLookupsAPIView)

    @patch("CRMSuperAdmin.views.ProductEdition")
    def test_product_edition_lookups_filters_by_product_using_icontains(self, mock_ed):
        import json
        from CRMSuperAdmin.views import ProductEditionLookupsAPIView

        prod = SimpleNamespace(id=5, Product_Code="CRM", Product_Name="Pegatto CRM")
        ed = SimpleNamespace(
            id=10,
            Edition_Id="PED000000010",
            Edition_Code="PRO",
            Edition_Name="Professional",
            Description="Pro edition",
            Product_Id_id=5,
            Product_Id=prod,
        )
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        qs.__iter__.return_value = iter([ed])
        mock_ed.objects.select_related.return_value = qs

        req = self.factory.get("/default/superadmin/ProductEditionLookups/", {"Product_Id": "CRM"})
        force_authenticate(req, user=self.user)
        resp = ProductEditionLookupsAPIView.as_view()(req, tenant_name="default")

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["status"])
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["Edition_Name"], "Professional")
        self.assertEqual(body["results"][0]["Product_id"], 5)
        filter_text = " ".join(str(c) for c in qs.filter.call_args_list)
        self.assertIn("icontains", filter_text)
        self.assertNotIn("iexact", filter_text)

    @patch("CRMSuperAdmin.views.Plan")
    def test_plan_lookups_filters_by_edition_using_icontains(self, mock_plan):
        import json
        from CRMSuperAdmin.views import PlanLookupsAPIView

        prod = SimpleNamespace(id=5, Product_Code="CRM", Product_Name="Pegatto CRM")
        ed = SimpleNamespace(
            id=10,
            Edition_Id="PED000000010",
            Edition_Code="PRO",
            Edition_Name="Professional",
            Product_Id_id=5,
            Product_Id=prod,
        )
        plan = SimpleNamespace(
            id=22,
            Plan_Id="PLN000022",
            Plan_Name="CRM Pro Monthly",
            Description="Pro plan",
            Plantype="Paid",
            billing_cycle="monthly",
            Currency_Type="INR",
            UnitPrice=1999.0,
            TotalAmount=2358.82,
            ProductEdition_id_id=10,
            ProductEdition_id=ed,
            ProductEdition_Name="Professional",
            Product_id=5,
            Product=prod,
        )
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        qs.__iter__.return_value = iter([plan])
        mock_plan.objects.select_related.return_value = qs

        req = self.factory.get("/default/superadmin/PlanLookups/", {"ProductEdition_id": "Professional"})
        force_authenticate(req, user=self.user)
        resp = PlanLookupsAPIView.as_view()(req, tenant_name="default")

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["status"])
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["Plan_Name"], "CRM Pro Monthly")
        self.assertEqual(body["results"][0]["Edition_Name"], "Professional")
        self.assertEqual(body["results"][0]["ProductEdition_id"], 10)
        filter_text = " ".join(str(c) for c in qs.filter.call_args_list)
        self.assertIn("icontains", filter_text)
        self.assertNotIn("iexact", filter_text)


class PurchaseActivationTests(SimpleTestCase):
    """Tests for PurchaseActivation models, serializer, CRUD/Filter/Action/Tab/KPI APIs."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_purchase_activation_urls_resolve(self):
        from CRMSuperAdmin.views import (
            PurchaseActivationActionAPI,
            PurchaseActivationCRUD,
            PurchaseActivationExportAPI,
            PurchaseActivationFilter,
            PurchaseActivationKPIAPI,
            PurchaseActivationListwithPagination,
            PurchaseActivationLookupsAPI,
            PurchaseActivationSearch,
            PurchaseActivationTabAPI,
            PurchaseActivationlistwithoutpaginaton,
        )

        cases = [
            ("purchase-activation-crud", PurchaseActivationCRUD),
            ("purchase-activation-list-paginated", PurchaseActivationListwithPagination),
            ("purchase-activation-search", PurchaseActivationSearch),
            ("purchase-activation-list-without-pagination", PurchaseActivationlistwithoutpaginaton),
            ("purchase-activation-filter", PurchaseActivationFilter),
            ("purchase-activation-kpi", PurchaseActivationKPIAPI),
            ("purchase-activation-action", PurchaseActivationActionAPI),
            ("purchase-activation-tabs", PurchaseActivationTabAPI),
            ("purchase-activation-lookups", PurchaseActivationLookupsAPI),
            ("purchase-activation-export", PurchaseActivationExportAPI),
        ]
        for name, view_cls in cases:
            url = reverse(name, kwargs={"tenant_name": "default"})
            self.assertEqual(resolve(url).func.view_class, view_cls)

    def test_apply_purchase_activation_scope_uses_icontains(self):
        from CRMSuperAdmin.views import _apply_purchase_activation_scope

        qs = MagicMock()
        qs.filter.return_value = qs

        _apply_purchase_activation_scope(
            qs,
            {
                "Purchase_Id": "PUR-100458",
                "Product": "CRM",
                "Plan_Edition": "Professional",
                "Purchase_Channel": "Direct",
                "Activation_Status": "Activated",
                "Payment_Status": "Paid",
                "Tenant": "Euro",
                "From_Date": "2026-10-01",
                "To_Date": "2026-11-19",
                "search": "Euro",
            },
        )
        filter_text = " ".join(str(c) for c in qs.filter.call_args_list)
        self.assertIn("icontains", filter_text)
        self.assertNotIn("iexact", filter_text)

    @patch("CRMSuperAdmin.views.PurchaseActivation")
    def test_purchase_activation_kpi_returns_5_cards_and_inr(self, mock_pa):
        import json
        from CRMSuperAdmin.views import PurchaseActivationKPIAPI

        base_qs = MagicMock()
        base_qs.filter.return_value = base_qs
        base_qs.count.side_effect = [1248, 1156, 42, 14]
        base_qs.filter.return_value.aggregate.return_value = {"total": 486400}
        ann_qs = MagicMock()
        ann_qs.__iter__.return_value = iter([])
        ann_qs.order_by.return_value = []
        base_qs.values.return_value.annotate.return_value = ann_qs
        mock_pa.objects.filter.return_value = base_qs

        req = self.factory.get("/default/superadmin/PurchaseActivationKPI/")
        force_authenticate(req, user=self.user)
        resp = PurchaseActivationKPIAPI.as_view()(req, tenant_name="default")

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["status"])
        self.assertEqual(body["total_purchases"], 1248)
        self.assertEqual(body["activated_count"], 1156)
        self.assertEqual(body["pending_activation_count"], 42)
        self.assertEqual(body["failed_count"], 14)
        self.assertEqual(body["total_revenue"], 486400.0)
        self.assertEqual(body["total_revenue_formatted"], "₹4,86,400")
        self.assertEqual(len(body["cards"]), 5)


class ActivationAndQueueTests(SimpleTestCase):
    """Tests for ActivationRecord and ActivationQueueRequest CRUD, Filter, Search, Action & KPI APIs."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, pk=1, id=1)

    def test_activation_and_queue_urls_resolve(self):
        from CRMSuperAdmin.views import (
            ActivationQueueActionAPI,
            ActivationQueueExportAPI,
            ActivationQueueRequestCRUD,
            ActivationQueueRequestFilter,
            ActivationQueueRequestKPIAPI,
            ActivationQueueRequestListwithPagination,
            ActivationQueueRequestSearch,
            ActivationQueueRequestlistwithoutpaginaton,
            ActivationRecordActionAPI,
            ActivationRecordCRUD,
            ActivationRecordExportAPI,
            ActivationRecordFilter,
            ActivationRecordKPIAPI,
            ActivationRecordListwithPagination,
            ActivationRecordSearch,
            ActivationRecordlistwithoutpaginaton,
        )

        cases = [
            ("activation-record-crud", ActivationRecordCRUD),
            ("activation-record-list-paginated", ActivationRecordListwithPagination),
            ("activation-record-search", ActivationRecordSearch),
            ("activation-record-list-without-pagination", ActivationRecordlistwithoutpaginaton),
            ("activation-record-filter", ActivationRecordFilter),
            ("activation-record-kpi", ActivationRecordKPIAPI),
            ("activation-record-action", ActivationRecordActionAPI),
            ("activation-record-export", ActivationRecordExportAPI),
            ("activation-queue-crud", ActivationQueueRequestCRUD),
            ("activation-queue-list-paginated", ActivationQueueRequestListwithPagination),
            ("activation-queue-search", ActivationQueueRequestSearch),
            ("activation-queue-list-without-pagination", ActivationQueueRequestlistwithoutpaginaton),
            ("activation-queue-filter", ActivationQueueRequestFilter),
            ("activation-queue-kpi", ActivationQueueRequestKPIAPI),
            ("activation-queue-action", ActivationQueueActionAPI),
            ("activation-queue-export", ActivationQueueExportAPI),
        ]
        for name, view_cls in cases:
            url = reverse(name, kwargs={"tenant_name": "default"})
            self.assertEqual(resolve(url).func.view_class, view_cls)

    def test_scopes_use_icontains_not_iexact(self):
        from CRMSuperAdmin.views import _apply_activation_queue_scope, _apply_activation_record_scope

        qs1 = MagicMock()
        qs1.filter.return_value = qs1
        _apply_activation_record_scope(
            qs1,
            {
                "Activation_Id": "ACT-100458",
                "Product": "CRM",
                "Plan_Edition": "Professional",
                "Tenant": "Euro",
                "Status": "Active",
                "License_Key": "PGT-CRM",
                "search": "Euro",
            },
        )
        t1 = " ".join(str(c) for c in qs1.filter.call_args_list)
        self.assertIn("icontains", t1)
        self.assertNotIn("iexact", t1)

        qs2 = MagicMock()
        qs2.filter.return_value = qs2
        _apply_activation_queue_scope(
            qs2,
            {
                "Request_Id": "AQ-100458",
                "Product": "CRM",
                "Request_Type": "Activation",
                "Tenant": "Euro",
                "Plan_Edition": "Professional",
                "Status": "Pending",
                "Priority": "High",
                "search": "Euro",
            },
        )
        t2 = " ".join(str(c) for c in qs2.filter.call_args_list)
        self.assertIn("icontains", t2)
        self.assertNotIn("iexact", t2)

    @patch("CRMSuperAdmin.views.ActivationRecord")
    def test_activation_record_kpi_returns_6_cards(self, mock_act):
        import json
        from CRMSuperAdmin.views import ActivationRecordKPIAPI

        qs = MagicMock()
        qs.filter.return_value = qs
        qs.count.side_effect = [1156, 1072, 42, 14, 268, 36]
        qs.values.return_value.annotate.return_value = []
        mock_act.objects.filter.return_value = qs

        req = self.factory.get("/default/superadmin/ActivationRecordKPI/")
        force_authenticate(req, user=self.user)
        resp = ActivationRecordKPIAPI.as_view()(req, tenant_name="default")

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["status"])
        self.assertEqual(body["total_activations"], 1156)
        self.assertEqual(body["active_count"], 1072)
        self.assertEqual(body["pending_count"], 42)
        self.assertEqual(body["failed_count"], 14)
        self.assertEqual(body["renewed_count"], 268)
        self.assertEqual(body["expiring_30_days_count"], 36)
        self.assertEqual(len(body["cards"]), 6)

    @patch("CRMSuperAdmin.views.ActivationQueueRequest")
    def test_activation_queue_kpi_returns_5_cards_and_tab_counts(self, mock_aq):
        import json
        from CRMSuperAdmin.views import ActivationQueueRequestKPIAPI

        qs = MagicMock()
        qs.filter.return_value = qs
        qs.count.side_effect = [42, 12, 6, 18, 20, 20, 3]
        qs.filter.return_value.aggregate.return_value = {"avg_m": 12.0}
        mock_aq.objects.filter.return_value = qs

        req = self.factory.get("/default/superadmin/ActivationQueueRequestKPI/")
        force_authenticate(req, user=self.user)
        resp = ActivationQueueRequestKPIAPI.as_view()(req, tenant_name="default")

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["status"])
        self.assertEqual(body["total_requests"], 42)
        self.assertEqual(body["pending_review_count"], 18)
        self.assertEqual(body["approved_today_count"], 20)
        self.assertEqual(body["rejected_count"], 3)
        self.assertEqual(body["avg_processing_time_mins"], 12)
        self.assertEqual(body["avg_processing_time_label"], "12 mins")
        self.assertEqual(body["tab_counts"]["in_review"], 6)
        self.assertEqual(len(body["cards"]), 5)






