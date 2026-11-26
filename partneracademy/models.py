from django.db import models
from django.conf import settings
from authapp.models import User
from partner.models import *

import uuid
from django.core.files.storage import storages


def academy_video_storage():
    return storages["academy_videos"]


def training_video_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"training-videos/{uuid.uuid4().hex}.{ext}"


# Create your models here.

# done by shajitha
# 12-11-2026
# Pegatto Academy - Partner Training models (one section per sidebar item)

# MY TRAINING  (products -> modules -> videos -> progress)

def Module_Id_I():
    last  = TrainingProductModule.objects.all().order_by('id').last()
    if not last:
        return "TNM" + "000000001"
    number = int(last.TrainingProduct_Id[3:])
    return "TNM" + str(number + 1).zfill(9)

class TrainingProductModule(models.Model):
    """A group of videos inside a product. Next module opens after all videos of this one are done."""
    TrainingProduct_Id = models.CharField(max_length=1000, unique=True, default=Module_Id_I, blank=True, null=True)
    #target_products
    Product_Name = models.CharField(max_length=1000, blank=True, null=True)
    Product_Code =  models.CharField(max_length=1000, blank=True, null=True)
    Module_Name =  models.CharField(max_length=1000, blank=True, null=True)
    Module_Code = models.CharField(max_length=1000, unique=True, blank=True, null=True)
    Title = models.CharField(max_length=200, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    Sequence_No = models.PositiveIntegerField(default=1)
    Status = models.CharField(max_length=32, default='Draft', blank=True, null=True)   # Draft / Published / Archived
    Is_Deleted = models.BooleanField(default=False)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Created_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='createdTrainingModule',blank=True,null=True)
    Updated_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='updatedTrainingModule',blank=True,null=True)

    class Meta:
        db_table = "TrainingProductModule"


def Video_Id_I():
    last = TrainingVideo.objects.all().order_by('id').last()
    if not last:
        return "TNV" + "000000001"
    number = int(last.Video_Id[3:])
    return "TNV" + str(number + 1).zfill(9)

class TrainingVideo(models.Model):
    """One video (= one topic). Stores only the file key and metadata, never the video bytes."""
    Video_Id = models.CharField(max_length=1000, unique=True, default=Video_Id_I, blank=True, null=True)
    Module = models.ForeignKey(TrainingProductModule, on_delete=models.CASCADE, related_name='train_videos', blank=True, null=True)
    Video_Title = models.CharField(max_length=1000, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    Sequence_No = models.PositiveIntegerField(default=1)
    Video_Key = models.CharField(max_length=1000, blank=True, null=True)      # storage object key / streaming manifest
    Thumbnail_Key = models.CharField(max_length=1000, blank=True, null=True)
    Duration_Seconds = models.PositiveIntegerField(blank=True, null=True)
    Min_Watch_Percentage = models.DecimalField(max_digits=5, decimal_places=2, default=90)
    Allow_Rewatch = models.BooleanField(default=False)                      # False = completed videos cannot be watched again
    Upload_Status = models.CharField(max_length=1000, default='Uploading', blank=True, null=True)  # Uploading / Processing / Ready / Failed
    Status = models.CharField(max_length=1000, default='Draft', blank=True, null=True)             # Draft / Published / Archived
    Video_Source = models.CharField(max_length=1000, default='Upload', blank=True, null=True)   # Upload / URL
    Video_URL = models.CharField(max_length=1000, blank=True, null=True)
    Original_Filename = models.CharField(max_length=255, blank=True, null=True)
    File_Size_Bytes = models.BigIntegerField(blank=True, null=True)
    Processing_Error = models.TextField(blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Created_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='createdTrainingVideo',blank=True,null=True)
    Updated_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='updatedTrainingVideo',blank=True,null=True)

    class Meta:
        db_table = "TrainingVideo"




def Enrollment_Id_I():
    last = ModuleEnrollment.objects.all().order_by('id').last()
    if not last:
        return "ERM" + "000000001"
    number = int(last.Enrollment_Id[3:])
    return "ERM" + str(number + 1).zfill(9)


class ModuleEnrollment(models.Model):
    """A learner starting a module (created when the module is first opened)."""
    Enrollment_Id = models.CharField(max_length=1000, unique=True, default=Enrollment_Id_I, blank=True, null=True)
    Partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='moduleEnrollments', blank=True, null=True)
    PartnerTeamMember = models.ForeignKey(PartnerTeamMember, on_delete=models.CASCADE, related_name='partnerteammoduleEnrollments', blank=True, null=True)
    Module = models.ForeignKey(TrainingProductModule, on_delete=models.CASCADE, related_name='enrollments', blank=True, null=True)
    Started_Date = models.DateTimeField(blank=True, null=True)
    Completed_Date = models.DateTimeField(blank=True, null=True)
    Completion_Percentage = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    Status = models.CharField(max_length=1000, default='Not Started', blank=True, null=True)  # Not Started / In Progress / Completed
    Last_Accessed_Date = models.DateTimeField(blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Created_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='createdModuleEnrollment',blank=True,null=True)
    Updated_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='updatedModuleEnrollment',blank=True,null=True)

    class Meta:
        db_table = "ModuleEnrollment"

def VideoProgress_Id_I():
    last = VideoProgress.objects.all().order_by('id').last()
    if not last:
        return "VID" + "000000001"
    number = int(last.VideoProgress_Id[3:])
    return "VID" + str(number + 1).zfill(9)

class VideoProgress(models.Model):
    """Main table for sequential unlocking: one row per learner per video."""
    VideoProgress_Id = models.CharField(max_length=1000, unique=True, default=VideoProgress_Id_I, blank=True, null=True)
    Enrollment = models.ForeignKey(ModuleEnrollment, on_delete=models.CASCADE, related_name='videoProgress', blank=True, null=True)
    Video = models.ForeignKey(TrainingVideo, on_delete=models.CASCADE, related_name='progress', blank=True, null=True)
    Status = models.CharField(max_length=32, default='Locked', blank=True, null=True)   # Locked / Available / In Progress / Completed
    Watch_Percentage = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    Watched_Seconds = models.PositiveIntegerField(default=0)               # unique validated seconds only
    Last_Position_Seconds = models.PositiveIntegerField(default=0)
    Unlocked_Date = models.DateTimeField(blank=True, null=True)
    First_Started_Date = models.DateTimeField(blank=True, null=True)
    Last_Watched_Date = models.DateTimeField(blank=True, null=True)
    Completed_Date = models.DateTimeField(blank=True, null=True)
    Completion_Method = models.CharField(max_length=1000, blank=True, null=True)          # Video / Admin Override
    Is_Deleted = models.BooleanField(default=False)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Created_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='createdVideoProgress',blank=True,null=True)
    Updated_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='updatedVideoProgress',blank=True,null=True)

    class Meta:
        db_table = "VideoProgress"


def VideoWatchSession_Id_I():
    last = VideoWatchSession.objects.all().order_by('id').last()
    if not last:
        return "VWS" + "000000001"
    number = int(last.VideoWatchSession_Id[3:])
    return "VWS" + str(number + 1).zfill(9)

class VideoWatchSession(models.Model):
    """One playback session (the session id used by the heartbeat API)."""
    VideoWatchSession_Id = models.CharField(max_length=1000, unique=True, default=VideoWatchSession_Id_I, blank=True, null=True)
    Progress = models.ForeignKey(VideoProgress, on_delete=models.CASCADE, related_name='sessions', blank=True, null=True)
    Session_Token_Hash = models.CharField(max_length=1000, unique=True, blank=True, null=True)
    Started_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Last_Heartbeat_Date = models.DateTimeField(blank=True, null=True)
    Ended_Date = models.DateTimeField(blank=True, null=True)
    Last_Position_Seconds = models.PositiveIntegerField(default=0)
    Device_Info = models.JSONField(blank=True, null=True)
    IP_Address = models.GenericIPAddressField(blank=True, null=True)
    Status = models.CharField(max_length=32, default='Active', blank=True, null=True)  # Active / Completed / Expired
    Is_Deleted = models.BooleanField(default=False)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Created_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='createdVideoWatchSession',blank=True,null=True)
    Updated_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='updatedVideoWatchSession',blank=True,null=True)

    class Meta:
        db_table = "VideoWatchSession"



def VideoWatchInterval_Id_I():
    last = VideoWatchInterval.objects.all().order_by('id').last()
    if not last:
        return "VWI" + "000000001"
    number = int(last.VideoWatchInterval_Id[3:])
    return "VWI" + str(number + 1).zfill(9)


class VideoWatchInterval(models.Model):
    """Validated watched ranges. Merge overlaps to get real coverage (0-300 watched twice = 300 sec)."""
    VideoWatchInterval_Id = models.CharField(max_length=1000, unique=True, default=VideoWatchInterval_Id_I, blank=True, null=True)
    Session = models.ForeignKey(VideoWatchSession, on_delete=models.CASCADE, related_name='session_intervals', blank=True, null=True)
    Progress = models.ForeignKey(VideoProgress, on_delete=models.CASCADE, related_name='intervals', blank=True, null=True)
    Start_Second = models.PositiveIntegerField(default=0)
    End_Second = models.PositiveIntegerField(default=0)
    Validated_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Created_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='createdVideoWatchInterval',blank=True,null=True)
    Updated_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='updatedVideoWatchInterval',blank=True,null=True)


    class Meta:
        db_table = "VideoWatchInterval"


# CERTIFICATION  (opens after all videos of a product are completed)


def Certificate_Id_I():
    last = Certificate.objects.all().order_by('id').last()
    if not last:
        return "CTF" + "000000001"
    number = int(last.Certificate_Id[3:])
    return "CTF" + str(number + 1).zfill(9)

class Certificate(models.Model):
    """Issued per learner per product after all videos (and assessment, if any) are completed."""
    Certificate_Id = models.CharField(max_length=1000, unique=True, default=Certificate_Id_I, blank=True, null=True)
    Certificate_Number = models.CharField(max_length=1000, unique=True, blank=True, null=True)   # public verification number
    Partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='certificates', blank=True, null=True)
    PartnerTeamMember = models.ForeignKey(PartnerTeamMember, on_delete=models.CASCADE, related_name='partnerteamcertificate', blank=True, null=True)
    Product = models.ForeignKey(TrainingProductModule, on_delete=models.CASCADE, related_name='product_certificates', blank=True, null=True)
    Product_Name = models.CharField(max_length=50, blank=True, null=True)
    Issued_Date = models.DateTimeField(blank=True, null=True)
    Expiry_Date = models.DateTimeField(blank=True, null=True)
    Certificate_File = models.CharField(max_length=1000, blank=True, null=True)  # object key of the PDF
    Status = models.CharField(max_length=32, default='Locked', blank=True, null=True)  # Locked / Eligible / Issued / Expired / Revoked
    Is_Deleted = models.BooleanField(default=False)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Created_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='createdCertificate',blank=True,null=True)
    Updated_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='updatedCertificate',blank=True,null=True)

    class Meta:
        db_table = "Certificate"


# MY PROFILE -> Notifications

def AcademyNotification_Id_I():
    last = AcademyNotification.objects.all().order_by('id').last()
    if not last:
        return "ANO" + "000000001"
    number = int(last.AcademyNotification_Id[3:])
    return "ANO" + str(number + 1).zfill(9)

class AcademyNotification(models.Model):
    AcademyNotification_Id = models.CharField(max_length=1000, unique=True, default=AcademyNotification_Id_I, blank=True, null=True)
    Recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='AcademyNotifications', blank=True, null=True)
    Partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='academyNotifications', blank=True, null=True)   # partner portal user
    PartnerTeamMember = models.ForeignKey(PartnerTeamMember, on_delete=models.CASCADE, related_name='partnerteamnoti', blank=True, null=True)
    Title = models.CharField(max_length=1000, blank=True, null=True)
    Message = models.TextField(blank=True, null=True)
    Notification_Type = models.CharField(max_length=64, blank=True, null=True)   # Video Unlocked / Certificate / Ticket Reply
    Link = models.CharField(max_length=1000, blank=True, null=True)
    Is_Read = models.BooleanField(default=False)
    Read_Date = models.DateTimeField(blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Created_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='createdAcademyNotification',blank=True,null=True)
    Updated_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='updatedAcademyNotification',blank=True,null=True)

    class Meta:
        db_table = "AcademyNotification"


from CRMSuperAdmin.models import *

def Documentation_Id_I():
    last = TechnicalDocumentation.objects.all().order_by('id').last()

    if not last:
        return "TDD000000001"

    number = int(last.Documentation_Id[3:])
    return "TDD" + str(number + 1).zfill(9)


class TechnicalDocumentation(models.Model):
    Documentation_Id = models.CharField(max_length=1000, unique=True, default=Documentation_Id_I, blank=True, null=True)
    Product_Id = models.ForeignKey(ProductMaster, on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    Products = models.IntegerField(default=0, blank=True, null=True)
    Product_Name = models.CharField(max_length=1000, blank=True, null=True)
    Module_Name = models.CharField(max_length=1000, blank=True, null=True)
    Document_Type = models.CharField(max_length=1000, blank=True, null=True)
    Document_Title = models.CharField(max_length=1000, blank=True, null=True)
    Document_Code = models.CharField(max_length=1000, blank=True, null=True)
    Category = models.CharField(max_length=1000, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    Document_File = models.CharField(max_length=2000, blank=True, null=True)
    Pending_Document_File = models.CharField(max_length=2000, blank=True, null=True)
    Original_Filename = models.CharField(max_length=255, blank=True, null=True)
    File_Type = models.CharField(max_length=100, blank=True, null=True)
    File_Size_Bytes = models.BigIntegerField(blank=True, null=True)
    Version = models.CharField(max_length=100, default='1.0', blank=True, null=True)
    Status = models.CharField(max_length=100, default='Draft', blank=True, null=True)
    Remarks = models.CharField(max_length=1000, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Created_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='createdTechnicalDocumentation', blank=True, null=True)
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updatedTechnicalDocumentation', blank=True, null=True)
    Partner_Id = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='partner_tech', blank=True, null=True)
    Customer_Id = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='customer_tech', blank=True, null=True)
    PartnerTeamMember_Id = models.ForeignKey(PartnerTeamMember, on_delete=models.CASCADE, related_name='partnerteammember_tech', blank=True, null=True)
    User_Id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Techincal_user', blank=True, null=True)

    class Meta:
        db_table = "TechnicalDocumentation"

def PartnerFAQ_Id_I():
    last = PartnerFAQ.objects.all().order_by('id').last()

    if not last:
        return "FAQ000000001"

    number = int(last.PartnerFAQ_Id[3:])
    return "FAQ" + str(number + 1).zfill(9)


class PartnerFAQ(models.Model):

    PartnerFAQ_Id = models.CharField(max_length=1000, unique=True, default=PartnerFAQ_Id_I, blank=True, null=True)
    Category_Name = models.CharField(max_length=255, blank=True, null=True)
    Question = models.CharField(max_length=500, blank=True, null=True)
    Answer = models.TextField(blank=True, null=True)
    Short_Description = models.TextField(blank=True, null=True)
    Display_Order = models.PositiveIntegerField(default=0, blank=True, null=True)
    Is_Active = models.BooleanField(default=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Modified_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Created_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='createdFAQ', blank=True, null=True)
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updatedFAQ', blank=True, null=True)
    Show_To_Partner = models.BooleanField(default=True, blank=True, null=True)
    Show_To_Team_Member = models.BooleanField(default=False, blank=True, null=True)
    Show_To_User = models.BooleanField(default=False, blank=True, null=True)
    Visible_User_Roles = models.JSONField(default=list, blank=True, null=True)
    
    class Meta:
        db_table = 'PartnerFAQ'

