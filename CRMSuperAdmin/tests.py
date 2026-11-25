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
from CRMSuperAdmin.DashboardService.superadmin_dashboard_service import (
    _apply_account_scope,
    _compute_mrr_arr_from_subs,
    _compute_open_tickets,
    _format_inr,
    parse_dashboard_filters,
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
    ProductPerformanceDashboardAPI,
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
