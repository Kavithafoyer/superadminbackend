from django.urls import path
from .views import *

urlpatterns = [
    # Define partner app URLs here
    path('PartnerApplicationList/', PartnerApplicationList.as_view()),
    path('PartnerApplicationWithoutPagination/', PartnerApplicationWithoutPagination.as_view()),
    path('PartnerApplicationCRUD/',PartnerApplicationCRUD.as_view()),
    path('PartnerWiseApplicationList/',PartnerWiseApplicationList.as_view()),


    path('PartnerCRUD/', PartnerCRUD.as_view()),
    path('PartnerList/', PartnerList.as_view()),
    path('PartnerWithoutPagination/',PartnerWithoutPagination.as_view()),
    path('PartnerProfile/',PartnerProfile.as_view()),
    path('PartnerLogin/', PartnerLogin.as_view()),
    path('PartnerTickets/',PartnerTickets.as_view()),

    path('SuperadminTicketManagementList/', SuperadminTicketManagementList.as_view(), name='superadmin-ticket-list'),
    path('PartnerMyTicketManagementList/', PartnerMyTicketManagementList.as_view(), name='partner-my-ticket-list'),
    path('PartnerAllTeamTicketManagementList/', PartnerAllTeamTicketManagementList.as_view(), name='partner-team-ticket-list'),
    path('PartnerTeamMemberTicketManagementList/', PartnerTeamMemberTicketManagementList.as_view(), name='partner-team-member-ticket-list'),


    path('PartnerTeamMemberProfile/',PartnerTeamMemberProfile.as_view()),

    path('PartnerTeamMemberLogin/',PartnerTeamMemberLogin.as_view()),
    path('PartnerTeamMemberTickets/',PartnerTeamMemberTickets.as_view()),


    path('TicketManagementCRUDwithnotoken/',TicketManagementCRUDwithnotoken.as_view()),
    path('TicketmanagemntListSuperadmin/',TicketmanagemntListSuperadmin.as_view()),

    #for kyc record
    path('KycRecordCRUD/',KycRecordCRUD.as_view()),
    path('KycRecordList/',KycRecordList.as_view()),
    path('KycRecordWithoutPagination/',KycRecordWithoutPagination.as_view()),
    path('PartnerWiseKycList/',PartnerWiseKycList.as_view()),


    # for Partner Agreement
    path('PartnerAgreementCRUD/',PartnerAgreementCRUD.as_view()),
    path('PartnerAgreementList/',PartnerAgreementList.as_view()),
    path('PartnerAgreementWithoutPagination/',PartnerAgreementWithoutPagination.as_view()),

    path('PartnerWiseAgreementList/',PartnerWiseAgreementList.as_view()),

    path('AgreementTemplateList/', AgreementTemplateList.as_view()),
    path('AgreementTemplateWithoutPagination/', AgreementTemplateWithoutPagination.as_view()),
    path('AgreementTemplateCRUD/', AgreementTemplateCRUD.as_view()),

    #for Partner Invitation
    path('PartnerInvitationCRUD/',PartnerInvitationCRUD.as_view()),
    path('PartnerInvitationList/',PartnerInvitationList.as_view()),
    path('PartnerInvitationWithoutPagination/',PartnerInvitationWithoutPagination.as_view()),


    #for Partner Product Support
    path('PartnerProductSupportCRUD/',partnerProductSupportCRUD.as_view()),
    path('PartnerProductSupportList/',partnerProductSupportList.as_view()),
    path('PartnerProductSupportWithoutPagination/',partnerProductSupportWithoutPagination.as_view()),

    #for customer lead
    path('CustomerLeadList/',CustomerLeadList.as_view()),
    path('CustomerLeadWithoutPagination/',CustomerLeadWithoutPagination.as_view()),
    path('CustomerLeadCRUD/',CustomerLeadCRUD.as_view()),

    # for Partner Opportunity
    path('PartnerOpportunityCRUD/',PartnerOpportunityCRUD.as_view()),
    path('PartnerOpportunityList/',PartnerOpportunityList.as_view()),
    path('PartnerOpportunityWithoutPagination/',PartnerOpportunityWithoutPagination.as_view()),

    # For partner customer
    path('PartnerCustomerCRUD/',PartnerCustomerCRUD.as_view()),
    path('PartnerCustomerList/',PartnerCustomerList.as_view()),
    path('PartnerCustomerWithoutPagination/',PartnerCustomerWithoutPagination.as_view()),

    # for business commission
    path('BusinessCommissionCRUD/',BusinessCommissionCRUD.as_view()),
    path('BusinessCommissionList/',BusinessCommissionList.as_view()),
    path('BusinessCommissionWithoutPagination/',BusinessCommissionWithoutPagination.as_view()),


    # for partner payout
    path('PartnerPayoutCRUD/',PartnerPayoutCRUD.as_view()),
    path('PartnerPayoutList/',PartnerPayoutList.as_view()),
    path('PartnerPayoutWithoutPagination/',PartnerPayoutWithoutPagination.as_view()),

    #for business resource
    path('BusinessResourceCRUD/',BusinessResourceCRUD.as_view()),
    path('BusinessResourceList/',BusinessResourceList.as_view()),
    path('BusinessResourceWithoutPagination/',BusinessResourceWithoutPagination.as_view()),

    #for implementation project
    path('ImplementationProjectCRUD/',ImplementationProjectCRUD.as_view()),
    path('ImplementationProjectList/',ImplementationProjectList.as_view()),
    path('ImplementationProjectWithoutPagination/',ImplementationProjectWithoutPagination.as_view()),

    # #for daily work update
    # path('DailyWorkUpdateCRUD/',DailyWorkUpdateCRUD.as_view()),
    # path('DailyWorkUpdateList/',DailyWorkUpdateList.as_view()),
    # path('DailyWorkUpdateWithoutPagination/',DailyWorkUpdateWithoutPagination.as_view()),

    #for tenant provisioning job
    path('TenantProvisioningJobCRUD/',TenantProvisioningJobCRUD.as_view()),
    path('TenantProvisioningJobList/',TenantProvisioningJobList.as_view()),
    path('TenantProvisioningJobWithoutPagination/',TenantProvisioningJobWithoutPagination.as_view()),



    #for partner team member
    path('PartnerTeamMemberCRUD/',PartnerTeamMemberCRUD.as_view()),
    path('PartnerTeamMemberList/',PartnerTeamMemberList.as_view()),
    path('PartnerTeamMemberWithoutPagination/',PartnerTeamMemberWithoutPagination.as_view()),


    #for partner deal
    path('PartnerDealCRUD/',PartnerDealCRUD.as_view()),
    path('PartnerDealList/',PartnerDealList.as_view()),
    path('PartnerDealWithoutPagination/',PartnerDealWithoutPagination.as_view()),

    #for partner customer
    path('PartnerCustomerCRUD/',PartnerCustomerCRUD.as_view()),
    path('PartnerCustomerList/',PartnerCustomerList.as_view()),
    path('PartnerCustomerWithoutPagination/',PartnerCustomerWithoutPagination.as_view()),


    #for kyc record
    path('KycRecordCRUD/',KycRecordCRUD.as_view()),
    path('KycRecordList/',KycRecordList.as_view()),
    path('KycRecordWithoutPagination/',KycRecordWithoutPagination.as_view()),



    # for Partner Agreement
    path('PartnerAgreementCRUD/',PartnerAgreementCRUD.as_view()),
    path('PartnerAgreementList/',PartnerAgreementList.as_view()),
    path('PartnerAgreementWithoutPagination/',PartnerAgreementWithoutPagination.as_view()),



    #for Partner Invitation
    path('PartnerInvitationCRUD/',PartnerInvitationCRUD.as_view()),
    path('PartnerInvitationList/',PartnerInvitationList.as_view()),
    path('PartnerInvitationWithoutPagination/',PartnerInvitationWithoutPagination.as_view()),


    #for Partner Product Support
    path('PartnerProductSupportCRUD/',partnerProductSupportCRUD.as_view()),
    path('PartnerProductSupportList/',partnerProductSupportList.as_view()),
    path('PartnerProductSupportWithoutPagination/',partnerProductSupportWithoutPagination.as_view()),

    #for customer lead
    path('CustomerLeadList/',CustomerLeadList.as_view()),
    path('CustomerLeadWithoutPagination/',CustomerLeadWithoutPagination.as_view()),
    path('CustomerLeadCRUD/',CustomerLeadCRUD.as_view()),

    # for Partner Opportunity
    path('PartnerOpportunityCRUD/',PartnerOpportunityCRUD.as_view()),
    path('PartnerOpportunityList/',PartnerOpportunityList.as_view()),
    path('PartnerOpportunityWithoutPagination/',PartnerOpportunityWithoutPagination.as_view()),

    # For partner customer
    path('PartnerCustomerCRUD/',PartnerCustomerCRUD.as_view()),
    path('PartnerCustomerList/',PartnerCustomerList.as_view()),
    path('PartnerCustomerWithoutPagination/',PartnerCustomerWithoutPagination.as_view()),

    # for business commission
    path('BusinessCommissionCRUD/',BusinessCommissionCRUD.as_view()),
    path('BusinessCommissionList/',BusinessCommissionList.as_view()),
    path('BusinessCommissionWithoutPagination/',BusinessCommissionWithoutPagination.as_view()),


    # for partner payout
    path('PartnerPayoutCRUD/',PartnerPayoutCRUD.as_view()),
    path('PartnerPayoutList/',PartnerPayoutList.as_view()),
    path('PartnerPayoutWithoutPagination/',PartnerPayoutWithoutPagination.as_view()),

    #for business resource
    path('BusinessResourceCRUD/',BusinessResourceCRUD.as_view()),
    path('BusinessResourceList/',BusinessResourceList.as_view()),
    path('BusinessResourceWithoutPagination/',BusinessResourceWithoutPagination.as_view()),

    #for implementation project
    path('ImplementationProjectCRUD/',ImplementationProjectCRUD.as_view()),
    path('ImplementationProjectList/',ImplementationProjectList.as_view()),
    path('ImplementationProjectWithoutPagination/',ImplementationProjectWithoutPagination.as_view()),

    #for daily work update
    path('DailyWorkUpdateCRUD/',DailyWorkUpdateCRUD.as_view()),
    path('DailyWorkUpdateList/',DailyWorkUpdateList.as_view()),
    path('DailyWorkUpdateWithoutPagination/',DailyWorkUpdateWithoutPagination.as_view()),

    path('SuperadminDailyWorkUpdateList/',SuperadminDailyWorkUpdateList.as_view()),
    path('PartnerTeamMemberDailyWorkUpdateList/',PartnerTeamMemberDailyWorkUpdateList.as_view()),
    path('PartnerMyDailyWorkUpdateList/',PartnerMyDailyWorkUpdateList.as_view()),
    path('PartnerAllteamDailyWorkUpdateList/',PartnerAllteamDailyWorkUpdateList.as_view()),


    #for tenant provisioning job
    path('TenantProvisioningJobCRUD/',TenantProvisioningJobCRUD.as_view()),
    path('TenantProvisioningJobList/',TenantProvisioningJobList.as_view()),
    path('TenantProvisioningJobWithoutPagination/',TenantProvisioningJobWithoutPagination.as_view()),



    #for partner team member
    path('PartnerTeamMemberCRUD/',PartnerTeamMemberCRUD.as_view()),
    path('PartnerTeamMemberList/',PartnerTeamMemberList.as_view()),
    path('PartnerTeamMemberWithoutPagination/',PartnerTeamMemberWithoutPagination.as_view()),


    #for partner deal
    path('PartnerDealCRUD/',PartnerDealCRUD.as_view()),
    path('PartnerDealList/',PartnerDealList.as_view()),
    path('PartnerDealWithoutPagination/',PartnerDealWithoutPagination.as_view()),

    #for partner customer
    path('PartnerCustomerCRUD/',PartnerCustomerCRUD.as_view()),
    path('PartnerCustomerList/',PartnerCustomerList.as_view()),
    path('PartnerCustomerWithoutPagination/',PartnerCustomerWithoutPagination.as_view()),

    path('PartnerRegistrationInvitationEmail/',PartnerRegistrationInvitationEmail.as_view()),
    path('PartnerCredentialsEmail/', PartnerCredentialsEmail.as_view(), name='PartnerCredentialsEmail'),

    # Dashboard APIs
    path('SuperAdminUserDashboard/', SuperAdminUserDashboardAPIView.as_view(), name='SuperAdminUserDashboard'),
    path('PartnerDashboardAPIView/', PartnerDashboardAPIView.as_view(), name='PartnerDashboard'),
    path('PartnerTeamMemberDashboard/', PartnerTeamMemberDashboardAPIView.as_view(), name='PartnerTeamMemberDashboard'),
    path('PartnerTeamMemberDashboardAPIView/', PartnerTeamMemberDashboardAPIView.as_view(), name='PartnerTeamMemberDashboardAPIView'),

    # Sales Performance APIs
    path('PartnerSalesPerformance/', PartnerSalesPerformanceAPIView.as_view(), name='PartnerSalesPerformance'),
    path('SuperAdminSalesPerformance/', SuperAdminSalesPerformanceAPIView.as_view(), name='SuperAdminSalesPerformance'),


    path('PartnerCustomerLeadListwithPartnerId/',PartnerCustomerLeadListwithPartnerId.as_view()),
    path('PartnerCustomerLeadList/',PartnerCustomerLeadList.as_view()),
    path('PartnerCustomerLeadWithoutPagination/',PartnerCustomerLeadWithoutPagination.as_view()),

    path('ForgotPasswordEmail/', ForgotPasswordEmail.as_view()),
    path('ResetPassword/', ResetPassword.as_view()),

    path('PartnerMailConfigurationCRUD/', PartnerMailConfigurationCRUD.as_view()),
    path(
        'PartnerMailConfigurationTestConnection/',
        PartnerMailConfigurationTestConnection.as_view(),
        name='PartnerMailConfigurationTestConnection'
    ),
]

