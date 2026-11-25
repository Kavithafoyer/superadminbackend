from django.urls import path

from CRMUserAdmin.views import *





urlpatterns = [
    
    # Auth User CRUD
    path('login/',LoginAPI.as_view()),
    path('logout/',LogoutAPI.as_view()),
    path('UserCRUD/',UserCRUD.as_view()),
    path('UserCRUD_GET/',UserCRUD_GET.as_view()),
    path('UserCRUD_mailid/',UserCRUD_mailid.as_view()),
    path('UsersList/',UsersList.as_view()),
    path('UserAdditional/',UserAdditional.as_view()),
    path('CRMUserarchive/',CRMUserarchive.as_view()),
    path('CRMUserlist/',CRMUserlist.as_view()),
    path('Userrole/',UserroleCRUD.as_view()),
    path('Userrolelist/',Userrolelist.as_view()),
    # path('Template/',TemplateCRUD.as_view()),
    path('Templatelist/',Templatelist.as_view()),
    path('Notification/',NotificationCRUD.as_view()),
    path('Notificationlist/',Notificationlist.as_view()),
    path('Ticket/',TicketCRUD.as_view()),
    path('Ticketlist/',Ticketlist.as_view()),
    path('TicketResponse/',TicketResponseCRUD.as_view()),
    path('TicketResponselist/',TicketResponselist.as_view()),
     path('Userlookup/',UserlookupCRUD.as_view()),
    path('Userlookuplist/',Userlookuplist.as_view()),
    path('Userlookuplistwithpagination/',Userlookuplistwithpagination.as_view()),
    path('Userlookupsearch/',Userlookupsearch.as_view()),
    path('CRMBusinessHours/',CRMBusinessHoursCRUD.as_view()),
    path('CRMBusinessHourslist/',CRMBusinessHourslist.as_view()),
    path('CRMorganizationCRUD/',CRMorganizationCRUD.as_view()),
    path('TaskuserCRUD/',TaskuserCRUD.as_view()),
    path('Taskuserlist/',Taskuserlist.as_view()),
    path('Mytaskuserlist/',Mytaskuserlist.as_view()),
    
    # Subscription and Plan CRUD Operation 
  #--------------------------------------------------------------------------------------------------------------------#

    # path('subscription/', subscriptionCRUD.as_view()),
    # path('subscriptionlist/', subscriptionlist.as_view()),
    # path('subscriptionarchive/', subscriptionarchive.as_view()),
    # path('subscriptionfilter/', subscriptionfilter.as_view()),
    # path('subscriptionsearch/', subscriptionsearch.as_view()),

    # path('plan/', planCRUD.as_view()),
    # path('planlist/', planlist.as_view()),
    # path('planarchive/', planarchive.as_view()),
    
    # path('addonsubscription/',AddonsubscriptionCRUD.as_view()),
    # path('addonsubscriptionlist/',Addonsubscriptionlist.as_view()),
    # path('Addonsubscriptionfilter/',Addonsubscriptionfilter.as_view()),
    # path('Addonsubscriptionsearch/',Addonsubscriptionsearch.as_view()),

    # path('AddlicenseRequest/',AddlicenseRequest.as_view()),
    # path('UserAddorcancellicenselist/',UserAddorcancellicenselist.as_view()),
    # path('MyuserAddorcancellicenselist/',MyuserAddorcancellicenselist.as_view()),
    # path('UserAddorcancellicenseSearch/',UserAddorcancellicenseSearch.as_view()),
    # path('UserAddorcancellicenseFilter/',UserAddorcancellicenseFilter.as_view()),

    # path('LicenceRequestMail/',LicenceRequestMail.as_view()),
    # path('AddstorageRequest/',AddstorageRequest.as_view()),

    # path('UserAddStoragelist/',UserAddStoragelist.as_view()),
    # path('MyuserAddStoragelist/',MyuserAddStoragelist.as_view()),
    # path('AddstorageSearch/',AddstorageSearch.as_view()),
    # path('AddstorageFilter/',AddstorageFilter.as_view()),
    # path('AddonRequestCRUD/',AddonRequestCRUD.as_view()),
    # path('AddonRequestlist/',AddonRequestlist.as_view()),
    # path('MyaddonRequestlist/',MyaddonRequestlist.as_view()),

    # path('AddonSearch/',AddonSearch.as_view()),
    # path('AddonFilter/',AddonFilter.as_view()),
    # path('CancelplanCRUD/',CancelplanCRUD.as_view()),
    # path('Cancelplanlist/',Cancelplanlist.as_view()),
    # path('MyCancelplanlist/',MyCancelplanlist.as_view()),
    
    # path('CancelPlan_DBBackup/',CancelPlan_DBBackup.as_view()),
    # path('UserRenewalRequestCRUD/',UserRenewalRequestCRUD.as_view()),
    # path('UserRenewalRequestlist/',UserRenewalRequestlist.as_view()),
    # path('MyUserRenewalRequestlist/',MyUserRenewalRequestlist.as_view()),
    # path('RenewalFormData/',RenewalFormData.as_view()),
#--------------------------------------------------------------------------------------------------------------------#
    path('CompanyCRUD/',CompanyCRUD.as_view()),
    # path('Useradmindashboard/',Useradmindashboard.as_view()),
    path('Dashboardticket/',Dashboardticket.as_view()),
    path('Dashboardtask/',Dashboardtask.as_view()),
    path('Dashboarduser/',Dashboarduser.as_view()),

    #  User Template
  
    path('CRMUserCampaignTemplate/', CRMUserCampaignTemplate.as_view()),
    path('CRMUserTemplateCRUD/',CRMUserTemplateCRUD.as_view()),
    path('CRMUserTemplateAdditional/',CRMUserTemplateAdditional.as_view()),

    # User Auto Template
    
    path('CRMUserAutoResponseCRUD/',CRMUserAutoResponseCRUD.as_view()),
    path('CRMUserAutoResponseAdditional/',CRMUserAutoResponseAdditional.as_view()),

   # UserAdminPredictionQuestionsCRUD
   
   path('UserAdminStatusQuestionsAdditional/',UserAdminStatusQuestionsAdditional.as_view()),
   path('UserAdminPredictionQuestionsAdditional/',UserAdminPredictionQuestionsAdditional.as_view()),
   path('UserAdminPredictionQuestionsCRUD/',UserAdminPredictionQuestionsCRUD.as_view()),
   path('UserAdminStatusQuestionsCRUD/',UserAdminStatusQuestionsCRUD.as_view()),

  # Activity List API
  
  path('UserAdminScoreQuestionsCRUD/',UserAdminScoreQuestionsCRUD.as_view()),
  path('UserScoreQuestionsAdditional/',UserScoreQuestionsAdditional.as_view()),
  path('AdminCallActivityQuestionsCRUD/',AdminCallActivityQuestionsCRUD.as_view()),
  path('AdminCallActivityQuestionsAdditional/',AdminCallActivityQuestionsAdditional.as_view()),
  path('AdminMailActivityQuestionsCRUD/',AdminMailActivityQuestionsCRUD.as_view()),
  path('AdminMailActivityQuestionsAdditional/',AdminMailActivityQuestionsAdditional.as_view()),
  path('AdminWebActivityQuestionsCRUD/',AdminWebActivityQuestionsCRUD.as_view()),
  path('WebActivityQuestionsAdditional/',WebActivityQuestionsAdditional.as_view()),

  # Deal Probability & Predictions
  
  path('UserAdminDealProbabilityCRUD/',UserAdminDealProbabilityCRUD.as_view()),
  path('UserAdminDealProbabilityAdditional/',UserAdminDealProbabilityAdditional.as_view()),
  path('UserAdminDealWeightSetupCRUD/',UserAdminDealWeightSetupCRUD.as_view()),
  path('UserAdminDealWeightSetupAdditional/',UserAdminDealWeightSetupAdditional.as_view()),
  path('UserAdminDealFactorSetupAdditional/',UserAdminDealFactorSetupAdditional.as_view()),
  path('UserAdminDealFactorSetupCRUD/',UserAdminDealFactorSetupCRUD.as_view()),
  path('UserAdminDealPredictionCRUD/',UserAdminDealPredictionCRUD.as_view()),
  path('UserAdminDealPredictionAdditional/',UserAdminDealPredictionAdditional.as_view()),
  path('UserAdminDealFactorSetupFullList/',UserAdminDealFactorSetupFullList.as_view()),

  
#  For Mail Configuration

  path('SignupUsers/',SignupUsers.as_view()),
  path('UserAdminMailConfigurationCRUD/',UserAdminMailConfigurationCRUD.as_view()),
  path('MailConfigurationAdditional/',MailConfigurationAdditional.as_view()),
  

  #SystemPreference

  path('UserAdminTaskCalendarAdditional/',UserAdminTaskCalendarAdditional.as_view()),
  path('UserAdminTaskCalendarCRUD/',UserAdminTaskCalendarCRUD.as_view()),
  path('SystemPreferenceCRUD/',SystemPreferenceCRUD.as_view()),
  path('Sytempreferencelist/',Sytempreferencelist.as_view()),
  # path('SuperAdminTicketManagementCRUD/',SuperAdminTicketManagementCRUD.as_view()),
  # path('SuperAdminTicketManagementAdditional/',SuperAdminTicketManagementAdditional.as_view()),
  # path('UserAdminTicketManagementCRUD/',UserAdminTicketManagementCRUD.as_view()),
  # path('UserAdminTicketManagementAdditional/',UserAdminTicketManagementAdditional.as_view()),
  path('UserAdminMailMasterCRUD/',UserAdminMailMasterCRUD.as_view()),
  path('UserAdminMailMasterListAdditional/',UserAdminMailMasterListAdditional.as_view()),

  # Transaction Series
  
  path('UserAdminTransactionalseriesAdditional/',UserAdminTransactionalseriesAdditional.as_view()),
  path('UserAdminTransactionalseriesCRUD/',UserAdminTransactionalseriesCRUD.as_view()),
  path('UserAdminMailsendingSpecifiedEvent/',UserAdminMailsendingSpecifiedEvent.as_view()),

  # Generate OTP

  path('GenerateOTP/',GenerateOTP.as_view()),

  # Form Permisssion

    path('Formpermissioncrud/',Formpermissioncrud.as_view()),
    path('Formpermastercrud/',Formpermastercrud.as_view()),
    path('Formmasterlist/',Formmasterlist.as_view()),
    path('Formpermissionfilter/',Formpermissionfilter.as_view()),
    path('Formpermisionlist/',Formpermisionlist.as_view()),
    path('Formpermisionlists/',Formpermisionlists.as_view()),

  # Role CRUD Permission

    path('RoleCRUD/',RoleCRUD.as_view()),
    path('RoleAdditionalCRUD/',RoleAdditionalCRUD.as_view()),
    path('userrolesearch/',userrolesearch.as_view()),
    path('Rolelist/',Rolelist.as_view()),
    path('Rolelistwithpagination/',Rolelistwithpagination.as_view()),

  # All Permission List
    
    path('Allpermission/',Allpermission.as_view()),

    path('PermissionList/',PermissionList.as_view()),


  # User Invite 

    path('userreg/', userreg, name='UserReg'),

    # path('userupdate/', userupdate, name='userupdate'),
    path('UserUpdate/',UserUpdate.as_view()),
    path('UserCreate/', UserCreate.as_view()),

  # Active Users List
    
    path('UserActiveList/',UserActiveList.as_view()),

  # User Target List
    
    path('CallcenterTargetListAdditional/',CallcenterTargetListAdditional.as_view()),
    path('CallcenterTargetListscrud/',CallcenterTargetListscrud.as_view()),
    path('CallcenterTargetUserbyId/',CallcenterTargetUserbyId.as_view()),


  # Call Center Additional 

#     path('LeadQualificationPercentagecrud/',LeadQualificationPercentagecrud.as_view()),
#     path('LeadQualificationPercentageAdditional/',LeadQualificationPercentageAdditional.as_view()),

#  # Lead DemoGraphics 

#   path('LeadDemoGraphicsCRUD/',LeadDemoGraphicsCRUD.as_view()),

#   path('LeadDemoGraphicsAdditional/',LeadDemoGraphicsAdditional.as_view()),
 
#   # Lead FirmoGraphics 
   
#   path('LeadFirmoGraphicsCRUD/',LeadFirmoGraphicsCRUD.as_view()),

#   path('LeadFirmoGraphicsAdditional/',LeadFirmoGraphicsAdditional.as_view()),

#   # Lead FirmoGraphics 
   
#   path('LeadFirmoGraphicsCRUD/',LeadFirmoGraphicsCRUD.as_view()),

#   path('LeadFirmoGraphicsAdditional/',LeadFirmoGraphicsAdditional.as_view()),

#   # Lead PositiveGraphics 
   
#   path('LeadPositiveGraphicsCRUD/',LeadPositiveGraphicsCRUD.as_view()),

#   path('LeadPositiveGraphicsAdditional/',LeadPositiveGraphicsAdditional.as_view()),

#   # Lead NegativeGraphics 
   
#   path('LeadNegativeGraphicsCRUD/',LeadNegativeGraphicsCRUD.as_view()),

#   path('LeadNegativeGraphicsAdditional/',LeadNegativeGraphicsAdditional.as_view()),
   

#   # Get the Graphics Field List
  
#     path('LeadDemoGraphicsList/', LeadDemoGraphicsFullList.as_view()),

#     path('LeadFirmoGraphicsFullList/', LeadFirmoGraphicsFullList.as_view()),

#     path('LeadPositiveGraphicsFullList/', LeadPositiveGraphicsFullList.as_view()),

#     path('LeadNegativeGraphicsFullList/', LeadNegativeGraphicsFullList.as_view()),

# # Demo Score Rule CRUD

#     path('LeadScoreValuesCRUD/', LeadScoreValuesCRUD.as_view()),

#     path('LeadScoreValuesList/', LeadScoreValuesList.as_view()),

#     path('LeadScoreValuesAdditional/', LeadScoreValuesAdditional.as_view()),

# # Firmo Score Rule CRUD 

#     path('LeadScoreValuesFirmoCRUD/', LeadScoreValuesFirmoCRUD.as_view()),

#     path('LeadScoreValuesFirmoList/', LeadScoreValuesFirmoList.as_view()),

#     path('LeadScoreValuesFirmoAdditional/', LeadScoreValuesFirmoAdditional.as_view()),


# # Positive Score Rule CRUD 

#   path('LeadScoreValuespositiveCRUD/', LeadScoreValuespositiveCRUD.as_view()),

#   path('LeadScoreValuespositiveAdditional/', LeadScoreValuespositiveAdditional.as_view()),

#   path('LeadScoreValuespositiveList/', LeadScoreValuespositiveList.as_view()),

# # negative Score Rule CRUD 

#   path('LeadScoreValuesNegativeCRUD/', LeadScoreValuesNegativeCRUD.as_view()),

#   path('LeadScoreValuesNegativeAdditional/', LeadScoreValuesNegativeAdditional.as_view()),

#   path('LeadScoreValuesNegativeList/', LeadScoreValuesNegativeList.as_view()),
 

path('ImageattachmentCRUD/',ImageattachmentCRUD.as_view()),

path('Imageattachmentlist/',Imageattachmentlist.as_view()),

path('InvoiceTemplateCRUD/',InvoiceTemplateCRUD.as_view()),

path('InvoiceTemplatelist/',InvoiceTemplatelist.as_view()),

# Transaction Series

path('TransactionbyOrg/',TransactionbyOrg.as_view()),

path('UserTransactionalseriesCRUD/',UserTransactionalseriesCRUD.as_view()),

path('UserTransactionalseriesAdditional/',UserTransactionalseriesAdditional.as_view()),

path('UserTransactionalseriesMyAdditional/',UserTransactionalseriesMyAdditional.as_view()),

path('Rolelistwithpagination/',Rolelistwithpagination.as_view()),

path('userrolesearch/',userrolesearch.as_view()),

path('UserorganizationmasterBankDetailsCRUD/',UserorganizationmasterBankDetailsCRUD.as_view()),

path('Sytempreferencegetapi/',Sytempreferencegetapi.as_view()),

##urls for rolepermission
path('RolePermissionCRUD/', RolePermissionCRUD.as_view()),

path('RolePermissionMyList/', RolePermissionMyList.as_view()),

path('RolePermissionAlllist/', RolePermissionAlllist.as_view()),

path('RolePermissionSearch/', RolePermissionSearch.as_view()),

path('RolePermissionFilter/', RolePermissionFilter.as_view()),







]