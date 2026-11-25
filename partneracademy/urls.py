from django.urls import path
from .views import *

urlpatterns = [

    # Training Module
    path('TrainingProductModuleCRUD/', TrainingProductModuleCRUD.as_view()),
    path('TrainingProductModuleSearch/', TrainingProductModuleSearch.as_view()),
    path('TrainingProductModuleFilter/', TrainingProductModuleFilter.as_view()),
    path('TrainingProductModuleList/', TrainingProductModuleList.as_view()),
    path('TrainingProductModuleWithoutPagination/', TrainingProductModuleWithoutPagination.as_view()),

    # Training Video
    path('TrainingVideoCRUD/', TrainingVideoCRUD.as_view()),
    path('TrainingVideoSearch/', TrainingVideoSearch.as_view()),
    path('TrainingVideoFilter/', TrainingVideoFilter.as_view()),
    path('TrainingVideoList/', TrainingVideoList.as_view()),
    path('TrainingVideoWithoutPagination/', TrainingVideoWithoutPagination.as_view()),

    # Training Video - 4 main APIs (database + Cloudflare R2 together, URL or file)
    path('TrainingVideoSave/', TrainingVideoSave.as_view()),        # POST            create
    path('TrainingVideoGet/', TrainingVideoGet.as_view()),          # GET             one / list + Play_URL
    path('TrainingVideoUpdate/', TrainingVideoUpdate.as_view()),    # POST/PUT/PATCH  edit
    path('TrainingVideoDelete/', TrainingVideoDelete.as_view()),    # DELETE / POST   delete

    # Training Video - upload / URL / publish / preview
    path('TrainingVideoUpload/', TrainingVideoUpload.as_view()),
    path('TrainingVideoCreateFromUrl/', TrainingVideoCreateFromUrl.as_view()),
    path('TrainingVideoReplaceFile/', TrainingVideoReplaceFile.as_view()),
    path('TrainingVideoDirectUploadStart/', TrainingVideoDirectUploadStart.as_view()),     # big files: browser -> R2
    path('TrainingVideoDirectUploadFinish/', TrainingVideoDirectUploadFinish.as_view()),
    path('TrainingVideoPublish/', TrainingVideoPublish.as_view()),
    path('TrainingVideoPreview/', TrainingVideoPreview.as_view()),
    path('TrainingVideoByModule/', TrainingVideoByModule.as_view()),

    path('ListOfProductWiseVideos/',ListOfProductWiseVideos.as_view()),

    # Module Enrollment
    path('ModuleEnrollmentCRUD/', ModuleEnrollmentCRUD.as_view()),
    path('ModuleEnrollmentSearch/', ModuleEnrollmentSearch.as_view()),
    path('ModuleEnrollmentFilter/', ModuleEnrollmentFilter.as_view()),
    path('ModuleEnrollmentList/', ModuleEnrollmentList.as_view()),
    path('ModuleEnrollmentWithoutPagination/', ModuleEnrollmentWithoutPagination.as_view()),

    # Video Progress
    path('VideoProgressCRUD/', VideoProgressCRUD.as_view()),
    path('VideoProgressSearch/', VideoProgressSearch.as_view()),
    path('VideoProgressFilter/', VideoProgressFilter.as_view()),
    path('VideoProgressList/', VideoProgressList.as_view()),
    path('VideoProgressWithoutPagination/', VideoProgressWithoutPagination.as_view()),

    # Video Watch Session
    path('VideoWatchSessionCRUD/', VideoWatchSessionCRUD.as_view()),
    path('VideoWatchSessionSearch/', VideoWatchSessionSearch.as_view()),
    path('VideoWatchSessionFilter/', VideoWatchSessionFilter.as_view()),
    path('VideoWatchSessionList/', VideoWatchSessionList.as_view()),
    path('VideoWatchSessionWithoutPagination/', VideoWatchSessionWithoutPagination.as_view()),

    # Video Watch Interval
    path('VideoWatchIntervalCRUD/', VideoWatchIntervalCRUD.as_view()),
    path('VideoWatchIntervalSearch/', VideoWatchIntervalSearch.as_view()),
    path('VideoWatchIntervalFilter/', VideoWatchIntervalFilter.as_view()),
    path('VideoWatchIntervalList/', VideoWatchIntervalList.as_view()),
    path('VideoWatchIntervalWithoutPagination/', VideoWatchIntervalWithoutPagination.as_view()),

    # Certificate
    path('CertificateCRUD/', CertificateCRUD.as_view()),
    path('CertificateSearch/', CertificateSearch.as_view()),
    path('CertificateFilter/', CertificateFilter.as_view()),
    path('CertificateList/', CertificateList.as_view()),
    path('CertificateWithoutPagination/', CertificateWithoutPagination.as_view()),
    path('PartnerCertificateList/',PartnerCertificateList.as_view()),
    path('PartnerTeamMemberCertificateList/',PartnerTeamMemberCertificateList.as_view()),

    # Academy Notification
    path('AcademyNotificationCRUD/', AcademyNotificationCRUD.as_view()),
    path('AcademyNotificationSearch/', AcademyNotificationSearch.as_view()),
    path('AcademyNotificationFilter/', AcademyNotificationFilter.as_view()),
    path('AcademyNotificationList/', AcademyNotificationList.as_view()),
    path('AcademyNotificationWithoutPagination/', AcademyNotificationWithoutPagination.as_view()),

    # Partner portal - My Training
    path('PartnerTrainingProducts/', PartnerTrainingProducts.as_view()),
    path('PartnerVideoPlay/', PartnerVideoPlay.as_view()),
    path('PartnerVideoStop/', PartnerVideoStop.as_view()),
    path('PartnerVideoComplete/', PartnerVideoComplete.as_view()),
    path('PartnerVideoActivity/', PartnerVideoActivity.as_view()),
    path('PartnerCertificateGenerate/', PartnerCertificateGenerate.as_view()),
    path('PartnerCertificateView/', PartnerCertificateView.as_view()),
    path('PartnerDashboard/', PartnerDashboard.as_view()),

]