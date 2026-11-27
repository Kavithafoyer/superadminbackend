
from django.urls import path
from CRMSuperAdmin.views import *
from partner.views import PartnerMailConfigurationCRUD

urlpatterns=[

path('InstanceCreationtCRUD/',InstanceCreationtCRUD.as_view()),

path('InstanceCreationList/',InstanceCreationList.as_view()),

path('InstanceCreationSearch/',InstanceCreationSearch.as_view()),

path('InstanceCreationFilter/',InstanceCreationFilter.as_view()),

path('Gettenent/',Gettenent.as_view()),

path('InstanceRequest/',InstanceRequestCRUD.as_view()),

path('InstanceRequestlist/',InstanceRequestlist.as_view()),

path('InstanceRequestfilter/',InstanceRequestfilter.as_view()),

path('InstanceRequestsearch/',InstanceRequestsearch.as_view()),

path('InstanceRequestmylist/',InstanceRequestmylist.as_view()),

path('CancelPlanPost/',CancelPlanPost.as_view()),

path('CancelPlanCRUD/',CancelPlanCRUD.as_view()),


path('CancelPlanlist/',CancelPlanlist.as_view()),

path('CancelPlanfilter/',CancelPlanfilter.as_view()),

path('CancelPlansesearch/',CancelPlansesearch.as_view()),

# Websit Visitors

path('WebsiteVistorsCRUD/',WebsiteVistorsCRUD.as_view()),

path('WebsiteVistorlist/',WebsiteVistorlist.as_view()),


path('Additionalstoragerequest/',AdditionalstoragerequestCRUD.as_view()),

path('Additionalstoragerequestlist/',Additionalstoragerequestlist.as_view()),

path('Additionalstoragerequestfilter/',Additionalstoragerequestfilter.as_view()),

path('Additionalstoragerequestsearch/',Additionalstoragerequestsearch.as_view()),

path('Paymentdetails/', PaymentdetailsCRUD.as_view()),

path('PaymentsAdditional/', PaymentsAdditional.as_view()),

path('Addsubscriptionrequest/',AddsubscriptionrequestCRUD.as_view()),

path('Addsubscriptionrequestlist/',Addsubscriptionrequestlist.as_view()),

path('Addsubscriptionrequestfilter/',Addsubscriptionrequestfilter.as_view()),

path('Addsubscriptionrequestsearch/',Addsubscriptionrequestsearch.as_view()),

path('Invoice/', InvoiceCRUD.as_view()),

path('Invoicemylist/', Invoicemylist.as_view()),


path('InvoiceDetailsAdditional/', InvoiceDetailsAdditional.as_view()),

path('storagemaster/', storagemasterCRUD.as_view()),

path('storagemastermylist/', storagemastermylist.as_view()),


path('storagemasterlist/', storagemasterlist.as_view()),

path('Storagemasterfilter/', Storagemasterfilter.as_view()),

path('Storagemastersearch/', Storagemastersearch.as_view()),


path('subscription/', subscriptionCRUD.as_view()),

path('subscriptionlist/', subscriptionlist.as_view()),

path('subscriptionmylist/', subscriptionmylist.as_view()),


path('subscriptionarchive/', subscriptionarchive.as_view()),

path('subscriptionfilter/', subscriptionfilter.as_view()),

path('subscriptionsearch/', subscriptionsearch.as_view()),


path('planmylist/', planmylist.as_view()),

path('planfilter/', planfilter.as_view()),

path('Paymentmylist/', Paymentmylist.as_view()),

path('InvoiceFullList/', InvoiceFullList.as_view()),

path('AddonsFullList/', AddonsFullList.as_view()),

path('planlist/', planlist.as_view()),

path('planarchive/', planarchive.as_view()),


path('plansearch/', plansearch.as_view()),

path('AddonLookups/', AddonLookupsAPIView.as_view()),

path('Addon/', AddonCRUD.as_view()),

path('AddonCRUDPost/', AddonCRUDPost.as_view()),

path('AddonAdditional/', AddonAdditional.as_view()),

path('Addonsmylist/', Addonsmylist.as_view()),

path('SubscriptionsFullList/', SubscriptionsFullList.as_view()),

path('StorageFullList/', StorageFullList.as_view()),

path('PaymentsFullList/', PaymentsFullList.as_view()),

path('Additionallicenserequest/',AdditionallicenserequestCRUD.as_view()),

path('Additionallicenserequestlist/',Additionallicenserequestlist.as_view()),

path('Additionallicenserequestfilter/',Additionallicenserequestfilter.as_view()),

path('Additionallicenserequestsearch/',Additionallicenserequestsearch.as_view()),

path('AdditionalstoragerequestCRUDPost/',AdditionalstoragerequestCRUDPost.as_view()),

path('AdditionallicenserequestPOST/',AdditionallicenserequestPOST.as_view()),

path('renewalCRUDPost/',renewalCRUDPost.as_view()),

path('renewalCRUD/',renewalCRUD.as_view()),

path('renewallistwithoutpagination/',renewallistwithoutpagination.as_view()),

path('AddsubscriptionrequestCRUDPost/',AddsubscriptionrequestCRUDPost.as_view()),

path('InstanceRequestpendingList/',InstanceRequestpendingList.as_view()),

path('InstanceRequestFullList/',InstanceRequestFullList.as_view()),

path('renewallist/',renewallist.as_view()),

path('renewalfilter/',renewalfilter.as_view()),

path('renewalsearch/',renewalsearch.as_view()),

#Created by Kavitha on 25.03.2026
path('AccountCRUD/',AccountCRUD.as_view()),

path('AccountAdditional/',AccountAdditional.as_view()),

path('AccountFullList/',AccountFullList.as_view()),

path('AccountGeoLocation/',AccountGeoLocation.as_view()),

path('AccountLocationByValue/',AccountLocationByValue.as_view()),

path('AccountMyAdditional/',AccountMyAdditional.as_view()),

path('AccountSearch/',AccountSearch.as_view()),

path('AccountFilter/',AccountFilter.as_view()),

# Account CSV Export API (supports filtering by product, status, search, and selected IDs)
path('AccountExportAPI/', AccountExportAPI.as_view()),

# Customer KPI & Metrics Analytics API (calculates live total, active, expiring, overdue, ARR & product adoption)
path('CustomerKpiAnalyticsAPI/', CustomerKpiAnalyticsAPI.as_view()),

##Dashboard API
path('RevenueDashboardAPI/',RevenueDashboardAPI.as_view()),

path('SubscriptionAnalyticsAPI/',SubscriptionAnalyticsAPI.as_view()),

path('SubscriptionInsightsAPI/',SubscriptionInsightsAPI.as_view()),

path('InstanceAnalyticsAPI/',InstanceAnalyticsAPI.as_view()),

path('UsageAnalyticsAPI/',UsageAnalyticsAPI.as_view()),

path('TrackEventAPI/',TrackEventAPI.as_view()),

path('AccountNotesCRUD/',AccountNotesCRUD.as_view()),

path('AccountNotesAdditional/',AccountNotesAdditional.as_view()),

path('AccountNotesSearch/',AccountNotesSearch.as_view()),

path('AccountNotesFilter/',AccountNotesFilter.as_view()),

path('AccountMailMasterCRUD/',AccountMailMasterCRUD.as_view()),

path('UserMailConfigurationCRUD/',UserMailConfigurationCRUD.as_view()),

path('AccountMailMasterListAdditional/',AccountMailMasterListAdditional.as_view()),

path('UserMailConfigurationCRUD/',UserMailConfigurationCRUD.as_view()),

path('AccountMeetingCRUD/',AccountMeetingCRUD.as_view()),

path('AccountMeetingAdditional/',AccountMeetingAdditional.as_view()),

path('AccountMeetingSearch/',AccountMeetingSearch.as_view()),

path('AccountMeetingFilter/',AccountMeetingFilter.as_view()),

path('AccountMeetingFullList/',AccountMeetingFullList.as_view()),

path('HistoryAccountMeetingFilter/',HistoryAccountMeetingFilter.as_view()),

path('HistoryAccountNotesFilter/',HistoryAccountNotesFilter.as_view()),

path('HistoryAccountMailFilter/',HistoryAccountMailFilter.as_view()),

path('AddonMailSending/',AddonMailSending.as_view()),

path('UserFilesandUrlsCRUD/',UserFilesandUrlsCRUD.as_view()),

##plan UI endpoints

path('AddonListAPI/',AddonListAPI.as_view()),

path('ProductDropdownAPI/',ProductDropdownAPI.as_view()),
path('ActiveProducts/',ProductDropdownAPI.as_view()),

path('planCRUD/',planCRUD.as_view()),

path('PlanFeatures/',PlanFeatures.as_view()),

# path('ModuleMasterCRUD/',ModuleMasterCRUD.as_view()), # Registered below under Module Master with name='module-master-crud'

path('MenuFeatures/',MenuFeatures.as_view()),

path('QuotationMailSending/',QuotationMailSending.as_view()),

path('AdditionalUserMasterCRUD/',AdditionalUserMasterCRUD.as_view()),

path('AdditionalUserMasterList/',AdditionalUserMasterList.as_view()),

path('AdditionalUserMasterSearch/',AdditionalUserMasterSearch.as_view()),

path('AdditionalUserMasterFilter/',AdditionalUserMasterFilter.as_view()),

path('AdditionalUserupdate/',AdditionalUserupdate.as_view()),

path('AdditionalStorageUpdate/',AdditionalStorageUpdate.as_view()),

path('AdditionalAddonUpdate/',AdditionalAddonUpdate.as_view()),

##new path for payment (razor pay)
path('CRMRazorpayFeeMail/',CRMRazorpayFeeMail.as_view()),

path('RazorpayWebhookCRM/',RazorpayWebhookCRM.as_view()),

path('UserActivityCRUD/',UserActivityCRUD.as_view()),

##renewal automation
path('ScheduleSubscriptionRenewal/',ScheduleSubscriptionRenewal.as_view()),
##Notification
path('UserNotificationSearch/',UserNotificationSearch.as_view()),

path('UserNotificationAdditional/',UserNotificationAdditional.as_view()),

path('UserNotificationwithoutpagination/',UserNotificationwithoutpagination.as_view()),

path('UserNotificationCRUD/',UserNotificationCRUD.as_view()),

path('UserNotificationFilter/',UserNotificationFilter.as_view()),
##account overview
path('AccountActivitiesClosed/',AccountActivitiesClosed.as_view()),

path('AccountActivitiesFilter/',AccountActivitiesFilter.as_view()),

path('AccountActivitiesSearch/',AccountActivitiesSearch.as_view()),

path('AccountActivitiesMyAdditional/',AccountActivitiesMyAdditional.as_view()),

path('AccountActivitiesmyList/',AccountActivitiesmyList.as_view()),

path('AccountClosedActivitiesSearch/',AccountClosedActivitiesSearch.as_view()),

path('AccountActivitiesCRUD/',AccountActivitiesCRUD.as_view()),

path('AccountHistorycrud/',AccountHistorycrud.as_view()),

path('AccountHistorylist/',AccountHistorylist.as_view()),

path('AccountHistoryfilter/',AccountHistoryfilter.as_view()),

path('InboxEmailCRUD/',InboxEmailCRUD.as_view()),

path('InboxEmailAccountList/',InboxEmailAccountList.as_view()),

path('RequestOTP/',RequestOTP.as_view()),

path('VerifyOTP/',VerifyOTP.as_view()),

##Analytics Dashboard endpoint

path('PaymentDashboardAnalytics/',PaymentDashboardAnalytics.as_view()),

path('RenewalDashboardAnalytics/',RenewalDashboardAnalytics.as_view()),

path('RenewalFunnelAnalytics/',RenewalFunnelAnalytics.as_view()),

path('CancellationOverviewAnalytics/',CancellationOverviewAnalytics.as_view()),

path('PlanAdoptionDashboardAnalytics/',PlanAdoptionDashboardAnalytics.as_view()),

path('TopPlansDistributionAnalytics/',TopPlansDistributionAnalytics.as_view()),

path('RevenueForecastDashboard/',RevenueForecastDashboard.as_view()),

path('RequestOperationsDashboard/',RequestOperationsDashboard.as_view()),

##ticket and task management
path('Nonproject_TaskManagementCRUD/', Nonproject_TaskManagementCRUD.as_view()),

path('Nonproject_TaskManagementAssignedToList/', Nonproject_TaskManagementAssignedToList.as_view()),

path('Nonproject_TaskManagementCreatedByList/', Nonproject_TaskManagementCreatedByList.as_view()),

path('Nonproject_TaskManagement_AssignedToSearch/', Nonproject_TaskManagement_AssignedToSearch.as_view()),

path('Nonproject_TaskManagement_CreatedBySearch/', Nonproject_TaskManagement_CreatedBySearch.as_view()),

path('Nonproject_TaskManagement_FilterAssignedTo/', Nonproject_TaskManagement_FilterAssignedTo.as_view()),

path('Nonproject_TaskManagement_FilterCreatedBy/', Nonproject_TaskManagement_FilterCreatedBy.as_view()),

path('Nonproject_TaskManagementAdditional/', Nonproject_TaskManagementAdditional.as_view()),

path('TicketManagementCRUD/', TicketManagementCRUD.as_view()),

path('TicketManagementAssignedToList/', TicketManagementAssignedToList.as_view()),

path('TicketManagementCreatedByList/', TicketManagementCreatedByList.as_view()),

path('TicketManagementCreatedBySearch/', TicketManagementCreatedBySearch.as_view()),

path('TicketManagementAssignedToSearch/', TicketManagementAssignedToSearch.as_view()),

path('TicketManagementCreatedByFilter/', TicketManagementCreatedByFilter.as_view()),

path('TicketManagementAssignedToFilter/', TicketManagementAssignedToFilter.as_view()),

#CEO Dashboard (Ticket Management)

path('CEO_DashboardCards_TKM/', CEO_DashboardCards_TKM.as_view()),

path('CEO_BugTrend_TKM/', CEO_BugTrend_TKM.as_view()),

path('CEO_BugsByPriority_TKM/', CEO_BugsByPriority_TKM.as_view()),

path('CEO_BugsByModule_TKM/', CEO_BugsByModule_TKM.as_view()),

path('CEO_TopAssignees_TKM/', CEO_TopAssignees_TKM.as_view()),

path('CEO_SLATrend_TKM/', CEO_SLATrend_TKM.as_view()),

path('CEO_RecentCriticalBugs_TKM/', CEO_RecentCriticalBugs_TKM.as_view()),

path('CEO_TicketSourceCount_TKM/', CEO_TicketSourceCount_TKM.as_view()),

path('Developer_DashboardCards_TKM/', Developer_DashboardCards_TKM.as_view()),

path('Developer_TicketsByStatus_TKM/', Developer_TicketsByStatus_TKM.as_view()),

path('Developer_FixRateVsIncomingTickets_TKM/', Developer_FixRateVsIncomingTickets_TKM.as_view()),

path('Developer_ResolutionTrend_TKM/', Developer_ResolutionTrend_TKM.as_view()),

path('Developer_CriticalVsHighTrend_TKM/', Developer_CriticalVsHighTrend_TKM.as_view()),

path('Developer_PriorityAvgResolutionTrend_TKM/', Developer_PriorityAvgResolutionTrend_TKM.as_view()),

path('Developer_TodaysTickets_TKM/', Developer_TodaysTickets_TKM.as_view()),

path('Developer_TimeSpentByPriority_TKM/', Developer_TimeSpentByPriority_TKM.as_view()),

path('Developer_EstimationVsActualByTickets_TKM/', Developer_EstimationVsActualByTickets_TKM.as_view()),

path('Creator_MonthlyTicketInsights_TKM/', Creator_MonthlyTicketInsights_TKM.as_view()),

path('Creator_HighWaitingTickets_TKM/', Creator_HighWaitingTickets_TKM.as_view()),

##Useradmin related endpoints

path('GeneratePerformanceInvoice/',GeneratePerformanceInvoice.as_view()),

path('PerformanceInvoiceDetails/',PerformanceInvoiceDetails.as_view()),

path('RenewalStatusAPI/',RenewalStatusAPI.as_view()),


path('AdditionalStorageRequestlistCusWise',AdditionalStorageRequestlistCusWise.as_view()),
path('AdditionalLicenseRequestlistCusWise',AdditionalLicenseRequestlistCusWise.as_view()),
path('AdditionalSubscriptionRequestlistCusWise',AdditionalSubscriptionRequestlistCusWise.as_view()),
path('RenewalRequestlistCusWise',RenewalRequestlistCusWise.as_view()),
path('GeneratePaymentBill/',GeneratePaymentBill.as_view()),
path('PlanModuleFeatures/',PlanModuleFeatures.as_view()),

path('PlanMenuTreeAPIView/',PlanMenuTreeAPIView.as_view()),
path('InstanceProductTypeGetApi/', InstanceProductTypeGetApi.as_view()),
path('CreatePegattoSubdomainAPIView/',CreatePegattoSubdomainAPIView.as_view()),

# Product Master
path('ProductMasterCRUD/', ProductMasterCRUD.as_view()),
path('ProductMasterList/', ProductMasterListAPI.as_view()),
path('ProductMasterLookups/', ProductMasterLookupsAPIView.as_view()),
path('ProductMasterFilter/', ProductMasterFilterAPI.as_view()),
path('ProductMasterExport/', ProductMasterExportAPI.as_view()),

# Document Master
path('DocumentMasterCRUD/', DocumentMasterCRUD.as_view()),
path('DocumentMasterList/', DocumentMasterList.as_view()),
path('DocumentMasterFilter/', DocumentMasterFilter.as_view()),
path('DocumentMasterWithoutPagination/', DocumentMasterWithoutPagination.as_view()),

# Audit History
path('AuditHistoryList/', AuditHistoryList.as_view()),
path('AuditHistoryFilter/', AuditHistoryFilter.as_view()),
path('AuditHistoryDetails/', AuditHistoryDetails.as_view()),

# Customer Overview Analytics & KPIs
path('CustomerOverviewAnalytics/', CustomerOverviewAnalyticsAPI.as_view()),
path('CustomerUsageHealthAnalytics/', CustomerUsageHealthAnalyticsAPI.as_view(), name='customer-usage-health-analytics'),

# SuperAdmin Dashboard APIs (Business Overview, System Health & Product-wise Performance)
path('BusinessOverviewDashboardAPI/', BusinessOverviewDashboardAPI.as_view(), name='business-overview-dashboard'),
path('SystemHealthAPI/', SystemHealthAPI.as_view(), name='system-health-api'),
path('ProductPerformanceDashboardAPI/', ProductPerformanceDashboardAPI.as_view(), name='product-performance-dashboard'),
path('CustomerKpiDashboardAPI/', CustomerKpiDashboardAPI.as_view(), name='customer-kpi-dashboard'),
path('PartnerKpiDashboardAPI/', PartnerKpiDashboardAPI.as_view(), name='partner-kpi-dashboard'),
path('RevenueSubscriptionAnalyticsDashboardAPI/', RevenueSubscriptionAnalyticsDashboardAPI.as_view(), name='revenue-subscription-analytics-dashboard'),
path('SystemHealthAlertsDashboardAPI/', SystemHealthAlertsDashboardAPI.as_view(), name='system-health-alerts-dashboard'),




# Add ons :-

path('AddonCategoryCRUD/',AddonCategoryCRUD.as_view()),
path('AddonCategoryListwithPagination/',AddonCategoryListwithPagination.as_view()),
path('AddonCategorySearch/',AddonCategorySearch.as_view()),
path('AddonCategorylistwithoutpaginaton/',AddonCategorylistwithoutpaginaton.as_view()),
path('AddonCategoryFilter/',AddonCategoryFilter.as_view()),

path('AddonCategoryCards/',AddonCategoryCards.as_view()),
path('AddonMasterCards/',AddonMasterCards.as_view()),


path('AddonProductCompatibilityCRUD/',AddonProductCompatibilityCRUD.as_view()),
path('AddonProductCompatibilityListwithPagination/',AddonProductCompatibilityListwithPagination.as_view()),
path('AddonProductCompatibilitySearch/',AddonProductCompatibilitySearch.as_view()),
path('AddonProductCompatibilitylistwithoutpaginaton/',AddonProductCompatibilitylistwithoutpaginaton.as_view()),
path('AddonProductCompatibilityFilter/',AddonProductCompatibilityFilter.as_view()),


path('AddonPriceTemplateCRUD/',AddonPriceTemplateCRUD.as_view()),
path('AddonPriceTemplateListwithPagination/',AddonPriceTemplateListwithPagination.as_view()),
path('AddonPriceTemplateSearch/',AddonPriceTemplateSearch.as_view()),
path('AddonPriceTemplatelistwithoutpaginaton/',AddonPriceTemplatelistwithoutpaginaton.as_view()),
path('AddonPriceTemplateFilter/',AddonPriceTemplateFilter.as_view()),
path('AddonPriceTemplateKPI/',AddonPriceTemplateKPIAPI.as_view()),
path('AddonPriceTemplateExport/',AddonPriceTemplateExportAPI.as_view()),
path('AddonPriceTemplateExportAPI/',AddonPriceTemplateExportAPI.as_view()),


path('AddonPricingCRUD/',AddonPricingCRUD.as_view()),
path('AddonPricingListwithPagination/',AddonPricingListwithPagination.as_view()),
path('AddonPricingSearch/',AddonPricingSearch.as_view()),
path('AddonPricinglistwithoutpaginaton/',AddonPricinglistwithoutpaginaton.as_view()),
path('AddonPricingFilter/',AddonPricingFilter.as_view()),
path('AddonPricingKPI/',AddonPricingKPIAPI.as_view()),
path('AddonPricingExport/',AddonPricingExportAPI.as_view()),
path('AddonPricingExportAPI/',AddonPricingExportAPI.as_view()),


path('AddonTieredPricingCRUD/',AddonTieredPricingCRUD.as_view()),
path('AddonTieredPricingListwithPagination/',AddonTieredPricingListwithPagination.as_view()),
path('AddonTieredPricinglistwithoutpaginaton/',AddonTieredPricinglistwithoutpaginaton.as_view()),
path('AddonTieredPricingFilter/',AddonTieredPricingFilter.as_view()),
path('AddonTieredPricingSearch/',AddonTieredPricingSearch.as_view()),
path('AddonTieredPricingKPI/',AddonTieredPricingKPIAPI.as_view()),
path('AddonTieredPricingExport/',AddonTieredPricingExportAPI.as_view()),


path('AddonDiscountCouponOptions/', AddonDiscountCouponOptions.as_view()),
path('AddonDiscountCouponCRUD/',AddonDiscountCouponCRUD.as_view()),
path('AddonDiscountCouponListwithPagination/',AddonDiscountCouponListwithPagination.as_view()),
path('AddonDiscountCouponlistwithoutpaginaton/',AddonDiscountCouponlistwithoutpaginaton.as_view()),
path('AddonDiscountCouponFilter/',AddonDiscountCouponFilter.as_view()),
path('AddonDiscountCouponSearch/',AddonDiscountCouponSearch.as_view()),
path('AddonDiscountCouponKPI/',AddonDiscountCouponKPIAPI.as_view()),
path('AddonDiscountCouponExport/',AddonDiscountCouponExportAPI.as_view()),


path('AddonPriceHistoryCRUD/',AddonPriceHistoryCRUD.as_view()),
path('AddonPriceHistoryListwithPagination/',AddonPriceHistoryListwithPagination.as_view()),
path('AddonPriceHistorylistwithoutpaginaton/',AddonPriceHistorylistwithoutpaginaton.as_view()),
path('AddonPriceHistoryFilter/',AddonPriceHistoryFilter.as_view()),
path('AddonPriceHistorySearch/',AddonPriceHistorySearch.as_view()),
path('AddonPriceHistoryKPI/',AddonPriceHistoryKPIAPI.as_view()),
path('AddonPriceHistoryExport/',AddonPriceHistoryExportAPI.as_view()),










path('LeadsCRUD/', LeadsCRUD.as_view(), name='LeadsCRUD'),
path('LeadsListwithPagination/', LeadsListwithPagination.as_view(), name='LeadsListwithPagination'),
path('LeadsSearch/', LeadsSearch.as_view(), name='LeadsSearch'),
path('LeadsListWithoutPagination/', LeadsListWithoutPagination.as_view(), name='LeadsListWithoutPagination'),

path('PartnerLeadsListwithPagination/',PartnerLeadsListwithPagination.as_view(), name='PartnerLeadsListwithPagination'),
path('SuperAdminLeadsListwithPagination/',SuperAdminLeadsListwithPagination.as_view(), name='SuperAdminLeadsListwithPagination'),


path('DealCRUD/', DealCRUD.as_view(), name='DealCRUD'),
path('DealListWithoutPagination/', DealListWithoutPagination.as_view(), name='DealListWithoutPagination'),
path('DealListWithPagination/', DealListWithPagination.as_view(), name='DealListWithPagination'),
path('DealSearch/', DealSearch.as_view(), name='DealSearch'),
path('PartnerDealListWithPagination/',PartnerDealListWithPagination.as_view()),


path('CustomerAccountCRUD/', CustomerAccountCRUD.as_view(), name='CustomerAccountCRUD'),
path('CustomerAccountListWithoutPagination/', CustomerAccountListWithoutPagination.as_view(), name='CustomerAccountListWithoutPagination'),
path('CustomerAccountListWithPagination/', CustomerAccountListWithPagination.as_view(), name='CustomerAccountListWithPagination'),
path('CustomerAccountSearch/', CustomerAccountSearch.as_view(), name='CustomerAccountSearch'),
path('PartnerCustomerAccountListWithPagination/',PartnerCustomerAccountListWithPagination.as_view()),

path('SuperAdminUserNotificationListt/', SuperAdminUserNotificationList.as_view(), name='superadmin-notification-list'),
path('PartnerMyNotificationList/', PartnerMyNotificationList.as_view(), name='partner-my-notification-list'),
path('PartnerTeamMemberNotificationList/', PartnerTeamMemberNotificationList.as_view(), name='partner-team-member-notification-list'),
path('PartnerAssignMailAPI/',PartnerAssignMailAPI.as_view()),
path('partner-assign-mail/',PartnerAssignMailAPI.as_view(), name='partner-assign-mail'),
path('PartnerMailConfigurationCRUD/', PartnerMailConfigurationCRUD.as_view(), name='PartnerMailConfigurationCRUD'),

# Product Category
path('ProductCategoryCRUD/', ProductCategoryCRUD.as_view(), name='product-category-crud'),
path('ProductCategoryListwithPagination/', ProductCategoryListwithPagination.as_view(), name='product-category-list-paginated'),
path('ProductCategorySearch/', ProductCategorySearch.as_view(), name='product-category-search'),
path('ProductCategorylistwithoutpaginaton/', ProductCategorylistwithoutpaginaton.as_view(), name='product-category-list-without-pagination'),
path('ProductCategoryFilter/', ProductCategoryFilter.as_view(), name='product-category-filter'),

# Product Feature
path('ProductFeatureCRUD/', ProductFeatureCRUD.as_view(), name='product-feature-crud'),
path('ProductFeatureListwithPagination/', ProductFeatureListwithPagination.as_view(), name='product-feature-list-paginated'),
path('ProductFeatureSearch/', ProductFeatureSearch.as_view(), name='product-feature-search'),
path('ProductFeaturelistwithoutpaginaton/', ProductFeaturelistwithoutpaginaton.as_view(), name='product-feature-list-without-pagination'),
path('ProductFeatureFilter/', ProductFeatureFilter.as_view(), name='product-feature-filter'),

# Plan Feature
path('PlanFeatureCRUD/', PlanFeatureCRUD.as_view(), name='plan-feature-crud'),
path('PlanFeatureListwithPagination/', PlanFeatureListwithPagination.as_view(), name='plan-feature-list-paginated'),
path('PlanFeatureSearch/', PlanFeatureSearch.as_view(), name='plan-feature-search'),
path('PlanFeaturelistwithoutpaginaton/', PlanFeaturelistwithoutpaginaton.as_view(), name='plan-feature-list-without-pagination'),
path('PlanFeatureFilter/', PlanFeatureFilter.as_view(), name='plan-feature-filter'),

# Plan Limit
path('PlanLimitCRUD/', PlanLimitCRUD.as_view(), name='plan-limit-crud'),
path('PlanLimitListwithPagination/', PlanLimitListwithPagination.as_view(), name='plan-limit-list-paginated'),
path('PlanLimitSearch/', PlanLimitSearch.as_view(), name='plan-limit-search'),
path('PlanLimitlistwithoutpaginaton/', PlanLimitlistwithoutpaginaton.as_view(), name='plan-limit-list-without-pagination'),
path('PlanLimitFilter/', PlanLimitFilter.as_view(), name='plan-limit-filter'),

# Product Configuration
path('ProductConfigurationCRUD/', ProductConfigurationCRUD.as_view(), name='product-configuration-crud'),
path('ProductConfigurationListwithPagination/', ProductConfigurationListwithPagination.as_view(), name='product-configuration-list-paginated'),
path('ProductConfigurationSearch/', ProductConfigurationSearch.as_view(), name='product-configuration-search'),
path('ProductConfigurationlistwithoutpaginaton/', ProductConfigurationlistwithoutpaginaton.as_view(), name='product-configuration-list-without-pagination'),
path('ProductConfigurationFilter/', ProductConfigurationFilter.as_view(), name='product-configuration-filter'),

# Module Master
path('ModuleMasterCRUD/', ModuleMasterCRUD.as_view(), name='module-master-crud'),
path('ModuleMasterListwithPagination/', ModuleMasterListwithPagination.as_view(), name='module-master-list-paginated'),
path('ModuleMasterSearch/', ModuleMasterSearch.as_view(), name='module-master-search'),
path('ModuleMasterlistwithoutpaginaton/', ModuleMasterlistwithoutpaginaton.as_view(), name='module-master-list-without-pagination'),
path('ModuleMasterFilter/', ModuleMasterFilter.as_view(), name='module-master-filter'),

# Product Edition
path('ProductEditionCRUD/', ProductEditionCRUD.as_view(), name='product-edition-crud'),
path('ProductEditionListwithPagination/', ProductEditionListwithPagination.as_view(), name='product-edition-list-paginated'),
path('ProductEditionSearch/', ProductEditionSearch.as_view(), name='product-edition-search'),
path('ProductEditionlistwithoutpaginaton/', ProductEditionlistwithoutpaginaton.as_view(), name='product-edition-list-without-pagination'),
path('Planlistwithoutpaginaton/', Planlistwithoutpaginaton.as_view(), name='plan-list-without-pagination'),
path('ProductEditionFilter/', ProductEditionFilter.as_view(), name='product-edition-filter'),

# License & Entitlement Management (ProductCategory pattern + KPI + Actions)
path('LicenseMasterCRUD/', LicenseMasterCRUD.as_view(), name='license-master-crud'),
path('LicenseMasterListwithPagination/', LicenseMasterListwithPagination.as_view(), name='license-master-list-paginated'),
path('LicenseMasterSearch/', LicenseMasterSearch.as_view(), name='license-master-search'),
path('LicenseMasterlistwithoutpaginaton/', LicenseMasterlistwithoutpaginaton.as_view(), name='license-master-list-without-pagination'),
path('LicenseMasterFilter/', LicenseMasterFilter.as_view(), name='license-master-filter'),
path('LicenseMasterKPI/', LicenseMasterKPIAPI.as_view(), name='license-master-kpi'),
path('LicenseAction/', LicenseActionAPI.as_view(), name='license-action'),
path('LicenseUsageCompliance/', LicenseUsageComplianceAPI.as_view(), name='license-usage-compliance'),
path('LicenseLookups/', LicenseLookupsAPI.as_view(), name='license-lookups'),
path('LicenseMasterExport/', LicenseMasterExportAPI.as_view(), name='license-master-export'),

# License Entitlements
path('LicenseEntitlementCRUD/', LicenseEntitlementCRUD.as_view(), name='license-entitlement-crud'),
path('LicenseEntitlementListwithPagination/', LicenseEntitlementListwithPagination.as_view(), name='license-entitlement-list-paginated'),
path('LicenseEntitlementSearch/', LicenseEntitlementSearch.as_view(), name='license-entitlement-search'),
path('LicenseEntitlementlistwithoutpaginaton/', LicenseEntitlementlistwithoutpaginaton.as_view(), name='license-entitlement-list-without-pagination'),
path('LicenseEntitlementFilter/', LicenseEntitlementFilter.as_view(), name='license-entitlement-filter'),
path('LicenseEntitlementKPI/', LicenseEntitlementKPIAPI.as_view(), name='license-entitlement-kpi'),

# License Assignments
path('LicenseAssignmentCRUD/', LicenseAssignmentCRUD.as_view(), name='license-assignment-crud'),
path('LicenseAssignmentListwithPagination/', LicenseAssignmentListwithPagination.as_view(), name='license-assignment-list-paginated'),
path('LicenseAssignmentSearch/', LicenseAssignmentSearch.as_view(), name='license-assignment-search'),
path('LicenseAssignmentlistwithoutpaginaton/', LicenseAssignmentlistwithoutpaginaton.as_view(), name='license-assignment-list-without-pagination'),
path('LicenseAssignmentFilter/', LicenseAssignmentFilter.as_view(), name='license-assignment-filter'),

# License Renewals
path('LicenseRenewalCRUD/', LicenseRenewalCRUD.as_view(), name='license-renewal-crud'),
path('LicenseRenewalListwithPagination/', LicenseRenewalListwithPagination.as_view(), name='license-renewal-list-paginated'),
path('LicenseRenewalSearch/', LicenseRenewalSearch.as_view(), name='license-renewal-search'),
path('LicenseRenewallistwithoutpaginaton/', LicenseRenewallistwithoutpaginaton.as_view(), name='license-renewal-list-without-pagination'),
path('LicenseRenewalFilter/', LicenseRenewalFilter.as_view(), name='license-renewal-filter'),

# Trial Configuration (Single Table - ProductCategory pattern + KPI)
path('TrialConfigurationCRUD/', TrialConfigurationCRUD.as_view(), name='trial-configuration-crud'),
path('TrialConfigurationListwithPagination/', TrialConfigurationListwithPagination.as_view(), name='trial-configuration-list-paginated'),
path('TrialConfigurationSearch/', TrialConfigurationSearch.as_view(), name='trial-configuration-search'),
path('TrialConfigurationlistwithoutpaginaton/', TrialConfigurationlistwithoutpaginaton.as_view(), name='trial-configuration-list-without-pagination'),
path('TrialConfigurationFilter/', TrialConfigurationFilter.as_view(), name='trial-configuration-filter'),
path('TrialConfigurationKPI/', TrialConfigurationKPIAPI.as_view(), name='trial-configuration-kpi'),
]
