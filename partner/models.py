"""Pegatto Partner database models."""

import secrets
import sys
import uuid
from datetime import timedelta
from enum import Enum
from typing import Optional

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from authapp.models import *

from datetime import date
from CRMUserAdmin.models import *

# -----------------------------------------------------------------------------
# 1. PARTNER ONBOARDING & CORE
# -----------------------------------------------------------------------------

def PartnerApplication_Id_I():
    try:
        last_obj = PartnerApplication.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerApplication_id:
            return "APP" + "000000001"
        number = int(last_obj.PartnerApplication_id[3:])
        return "APP" + str(number + 1).zfill(9)
    except Exception:
        return "APP" + "000000001"


class PartnerApplication(models.Model):
    PartnerApplication_id = models.CharField(max_length=1000, blank=True, null=True, default=PartnerApplication_Id_I)
    application_number = models.CharField(max_length=1000, unique=True, blank=True, null=True)
    applicant_name = models.CharField(max_length=1000, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    organisation_name = models.CharField(max_length=1000, blank=True, null=True)
    entity_type = models.CharField(max_length=1000, default='PRIVATE_LIMITED', blank=True, null=True)
    status = models.CharField(max_length=1000, default='SUBMITTED', blank=True, null=True)
    target_products = models.JSONField(default=list, blank=True, null=True)
    country = models.CharField(max_length=1000, default='India', blank=True, null=True)
    city = models.CharField(max_length=1000, default='Bengaluru', blank=True, null=True)
    reviewer_remarks = models.TextField(blank=True, null=True)
    reviewed_by = models.CharField(max_length=1000, blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    # shajitha
    Lead_Id = models.ForeignKey('CRMSuperAdmin.Leads', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'PartnerApplication'


def KycRecord_Id_I():
    try:
        last_obj = KycRecord.objects.all().order_by('id').last()
        if not last_obj or not last_obj.KycRecord_id:
            return "KYC" + "000000001"
        number = int(last_obj.KycRecord_id[3:])
        return "KYC" + str(number + 1).zfill(9)
    except Exception:
        return "KYC" + "000000001"


class KycRecord(models.Model):
    KycRecord_id = models.CharField(max_length=64, default=KycRecord_Id_I, blank=True, null=True)
    partner_org_id = models.CharField(max_length=64, default='org-cloudcraft-01', blank=True, null=True)
    partner_name = models.CharField(max_length=255, blank=True, null=True)
    pan_number = models.CharField(max_length=32, blank=True, null=True)
    gst_number = models.CharField(max_length=32, blank=True, null=True)
    cin_number = models.CharField(max_length=32, blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    documents = models.JSONField(default=list, blank=True, null=True)
    reviewer_remarks = models.TextField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Lead_Id = models.ForeignKey('CRMSuperAdmin.Leads', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'KycRecord'


def PartnerInvitation_Id_I():
    try:
        last_obj = PartnerInvitation.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerInvitation_id:
            return "PAR_INV" + "000000001"
        number = int(last_obj.PartnerInvitation_id[7:])
        return "PAR_INV" + str(number + 1).zfill(9)
    except Exception:
        return "PAR_INV" + "000000001"


class PartnerInvitation(models.Model):
    PartnerInvitation_id = models.CharField(max_length=64, default=PartnerInvitation_Id_I, blank=True, null=True)
    invitation_code = models.CharField(max_length=64, unique=True, blank=True, null=True)
    partner_org_id = models.CharField(max_length=64, blank=True, null=True)
    recipient_name = models.CharField(max_length=128, blank=True, null=True)
    recipient_email = models.EmailField(blank=True, null=True)
    partner_type = models.CharField(max_length=32, default='COMPANY', blank=True, null=True)
    target_country = models.CharField(max_length=64, default='India', blank=True, null=True)
    target_city = models.CharField(max_length=64, default='Bengaluru', blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    invited_by = models.CharField(max_length=128, default='Super Admin', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Lead_Id = models.ForeignKey('CRMSuperAdmin.Leads', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'PartnerInvitation'


def Partner_Id_I():
    try:
        last_obj = Partner.objects.all().order_by('id').last()
        if not last_obj or not last_obj.Partner_Id:
            return "PAR" + "000000001"
        number = int(last_obj.Partner_Id[3:])
        return "PAR" + str(number + 1).zfill(9)
    except Exception:
        return "PAR" + "000000001"


class Partner(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE, related_name='partner_org', blank=True, null=True)
    Partner_Id = models.CharField(max_length=100, unique=True, default=Partner_Id_I, blank=True, null=True)
    Partner_Code = models.CharField(max_length=64, unique=True, blank=True, null=True)
    Legal_Name = models.CharField(max_length=255, blank=True, null=True)
    Trade_Name = models.CharField(max_length=255, blank=True, null=True)
    Tier = models.CharField(max_length=64, blank=True, null=True)
    Status = models.CharField(max_length=32, blank=True, null=True)
    Country = models.CharField(max_length=64, default='India', blank=True, null=True)
    City = models.CharField(max_length=64, default='Chennai', blank=True, null=True)
    Primary_Contact_Name = models.CharField(max_length=128, default='Partner Admin', blank=True, null=True)
    Primary_Email = models.EmailField(blank=True, null=True)
    Password = models.CharField(max_length=1000, blank=True, null=True)
    Primary_Phone = models.CharField(max_length=32, blank=True, null=True)
    Website = models.URLField(blank=True, null=True)
    Rating = models.DecimalField(max_digits=3, decimal_places=2, default=4.8, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    PartnerApplication_Id = models.ForeignKey(PartnerApplication, on_delete=models.CASCADE, related_name='app_partner', blank=True, null=True)
    PartnerInvitation_Id = models.ForeignKey(PartnerInvitation, on_delete=models.CASCADE, related_name='parinv_partner', blank=True, null=True)
    # PartnerAgreement_Id = models.ForeignKey(PartnerAgreement, on_delete=models.CASCADE, related_name='paragree_partner', blank=True, null=True)
    KycRecord_Id = models.ForeignKey(KycRecord, on_delete=models.CASCADE, related_name='kyc_partner', blank=True, null=True)
    Partner_Type = models.CharField(max_length=1000, blank=True, null=True)
    Lead_Id = models.ForeignKey('CRMSuperAdmin.Leads', on_delete=models.CASCADE, blank=True, null=True)
    Products = models.JSONField(default=list, blank=True, null=True)

    class Meta:
        db_table = "Partner"


class PartnerMailConfiguration(models.Model):
    Partner_Id = models.ForeignKey('Partner', on_delete=models.CASCADE, null=True, blank=True)
    SMTPHost = models.CharField(max_length=250, null=True, blank=True)
    SMTPPort = models.CharField(max_length=25, null=True, blank=True)
    MailId = models.EmailField(null=True, blank=True)
    MailPassword = models.CharField(max_length=250, null=True, blank=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'PartnerMailConfiguration'
        ordering = ['-id']



def AgreementTemplate_Id_I():
    try:
        last_obj = AgreementTemplate.objects.all().order_by('id').last()
        if not last_obj or not last_obj.Template_Name_Id:
            return "ATE" + "000000001"
        number = int(last_obj.Template_Name_Id[3:])
        return "ATE" + str(number + 1).zfill(9)
    except Exception:
        return "ATE" + "000000001"

class AgreementTemplate(models.Model):
    Template_Name_Id = models.CharField(max_length=1000, blank=True, null=True,default=AgreementTemplate_Id_I)
    Template_Name = models.CharField(max_length=100, blank=True, null=True)
    Version = models.CharField(max_length=100, blank=True, null=True)   # v2.4-master
    File = models.FileField(blank=True, null=True)
    FileName = models.CharField(max_length=1000, blank=True, null=True)
    Is_Active = models.BooleanField(default=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        db_table = 'AgreementTemplate'


def PartnerAgreement_Id_I():
    try:
        last_obj = PartnerAgreement.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerAgreement_id:
            return "PAG" + "000000001"
        number = int(last_obj.PartnerAgreement_id[3:])
        return "PAG" + str(number + 1).zfill(9)
    except Exception:
        return "PAG" + "000000001"


class PartnerAgreement(models.Model):
    PartnerAgreement_id = models.CharField(max_length=64, default=PartnerAgreement_Id_I, blank=True, null=True)
    agreement_code = models.CharField(max_length=64, unique=True, blank=True, null=True)
    partner_org_id = models.CharField(max_length=64, blank=True, null=True)
    partner_org_name = models.CharField(max_length=255, blank=True, null=True)
    template_version = models.CharField(max_length=32, default='v2.4-master', blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    e_sign_platform = models.CharField(max_length=64, default='Aadhaar eSign', blank=True, null=True)
    signatory_name = models.CharField(max_length=128, default='Vikram Sengupta', blank=True, null=True)
    signatory_email = models.EmailField(default='vikram@cloudcraft.com', blank=True, null=True)
    signed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Lead_Id = models.ForeignKey('CRMSuperAdmin.Leads', on_delete=models.CASCADE, blank=True, null=True)
    Partner_Id = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='Partneragreements', blank=True, null=True)
    File = models.FileField(blank=True, null=True)
    FileName = models.CharField(max_length=250, blank=True, null=True)
    AgreementTemplate_Id = models.ForeignKey(AgreementTemplate, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'PartnerAgreement'


def PartnerProductSupport_Id_I():
    try:
        last_obj = PartnerProductSupport.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerProductSupport_id:
            return "PAR_PSUP" + "000000001"
        number = int(last_obj.PartnerProductSupport_id[8:])
        return "PAR_PSUP" + str(number + 1).zfill(9)
    except Exception:
        return "PAR_PSUP" + "000000001"


class PartnerProductSupport(models.Model):
    PartnerProductSupport_id = models.CharField(max_length=64, default=PartnerProductSupport_Id_I, blank=True, null=True)
    partner_organisation = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='product_supports', blank=True, null=True)
    product_id = models.CharField(max_length=64, db_index=True, blank=True, null=True)
    is_supported = models.BooleanField(default=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
       db_table = 'PartnerProductSupport'


# -----------------------------------------------------------------------------
# 2. BUSINESS DOMAIN MODELS
# -----------------------------------------------------------------------------


def PartnerCustomerLead_Id_I():
    try:
        last_obj = PartnerCustomerLead.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerCustomerLead_id:
            return "PAR_CL" + "000000001"
        number = int(last_obj.PartnerCustomerLead_id[6:])
        return "PAR_CL" + str(number + 1).zfill(9)
    except Exception:
        return "PAR_CL" + "000000001"


class PartnerCustomerLead(models.Model):
    PartnerCustomerLead_id = models.CharField(max_length=64, default=PartnerCustomerLead_Id_I, blank=True, null=True)
    lead_code = models.CharField(max_length=64, unique=True, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person = models.CharField(max_length=128, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    location = models.CharField(max_length=128, default='Bengaluru, India', blank=True, null=True)
    city = models.CharField(max_length=64, default='Bengaluru', blank=True, null=True)
    country = models.CharField(max_length=64, default='India', blank=True, null=True)
    product_interested = models.CharField(max_length=64,  default='Pegatto CRM', blank=True, null=True)
    lead_source = models.CharField(max_length=64, default='PARTNER_REFERRAL', blank=True, null=True)
    estimated_deal_value = models.DecimalField(max_digits=12, decimal_places=2, default=250000, blank=True, null=True)
    lead_owner = models.CharField(max_length=128, default='Partner Admin', blank=True, null=True)
    partner_org_id = models.CharField(max_length=64, default='org-cloudcraft-01', blank=True, null=True)
    partner_org_name = models.CharField(max_length=255, default='CloudCraft Solutions Pvt. Ltd.', blank=True, null=True)
    next_follow_up_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    lead_status = models.CharField(max_length=32, default='New', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)


    # ---------------- Fields added from Leads model ----------------
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE, related_name='partnercuslead_org', blank=True, null=True)
    Salutation = models.CharField(max_length=20, blank=True, null=True)
    LeadFirstName = models.CharField(max_length=50, blank=True, null=True)
    LeadLastName = models.CharField(max_length=50, blank=True, null=True)
    File = models.FileField(blank=True, null=True)
    FileName = models.CharField(max_length=250, blank=True, null=True)
    LeadType = models.CharField(max_length=100, blank=True, null=True)
    Pincode = models.CharField(max_length=250, blank=True, null=True)
    Mobile_No = models.CharField(max_length=20, blank=True, null=True)
    WebsiteURL = models.CharField(max_length=10000, blank=True, null=True)
    BuildingDoorNo = models.CharField(max_length=10000, blank=True, null=True)
    StreetName = models.CharField(max_length=50, blank=True, null=True)
    AreaName = models.CharField(max_length=50, blank=True, null=True)
    State = models.CharField(max_length=50, blank=True, null=True)
    LeadScore = models.IntegerField(default=0, blank=True, null=True)
    Lead_Stage = models.CharField(max_length=250, blank=True, null=True)
    Recommaned_Action = models.CharField(max_length=1000, blank=True, null=True)
    LifeCycleStage = models.CharField(max_length=250, blank=True, null=True)
    Maps = models.CharField(max_length=10000, default='', blank=True, null=True)
    LeadDescription = models.CharField(max_length=2500, blank=True, null=True)

    # Qualification
    LeadMLQStatus = models.BooleanField(default=False, blank=True, null=True)
    LeadMLQuestions = models.JSONField(blank=True, null=True)
    LeadSLQStatus = models.BooleanField(default=False, blank=True, null=True)
    LeadSLQuestions = models.JSONField(blank=True, null=True)
    LeadQualifyStatus = models.BooleanField(default=False, blank=True, null=True)
    MQL_Qualified_Date = models.DateField(default=date.today, blank=True, null=True)
    SQL_Qualified_Date = models.DateField(default=date.today, blank=True, null=True)

    # Owner / user links
    Lead_Owner_Id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partnercuslead_owner', blank=True, null=True)
    Created_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partnercuslead_created_by', blank=True, null=True)
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partnercuslead_updated_by', blank=True, null=True)

    # Contact person details
    Job_Title = models.CharField(max_length=1000, blank=True, null=True)
    Job_Role = models.CharField(max_length=1000, blank=True, null=True)
    Designation = models.CharField(max_length=1000, blank=True, null=True)
    Decissionmaker = models.BooleanField(default=False, blank=True, null=True)
    Yrs_of_Experience = models.CharField(max_length=1000, blank=True, null=True)
    Date_Of_Birth = models.CharField(max_length=250, blank=True, null=True)
    Prefered_Contact_Method = models.CharField(max_length=250, blank=True, null=True)
    Fax = models.CharField(max_length=250, blank=True, null=True)
    LinkedIn_Profile = models.CharField(max_length=250, blank=True, null=True)
    Twitter_Profile = models.CharField(max_length=250, blank=True, null=True)

    # Company details
    LeadNoOfEmployees = models.IntegerField(blank=True, null=True)
    Lead_Industry = models.CharField(max_length=100, blank=True, null=True)
    LeadCompanyTurnOver = models.FloatField(blank=True, null=True)
    Head_Quarter = models.CharField(max_length=1000, blank=True, null=True)
    Year_of_Founded = models.CharField(max_length=1000, blank=True, null=True)
    Organization_structure = models.CharField(max_length=1000, blank=True, null=True)
    Company_status = models.BooleanField(default=False, blank=True, null=True)

    # Budget / purchase info
    Budget_Availability = models.CharField(max_length=1000, blank=True, null=True)
    Budget = models.CharField(max_length=1000, blank=True, null=True)
    Level_of_detail_provided = models.CharField(max_length=1000, blank=True, null=True)
    Previous_purchases = models.CharField(max_length=1000, blank=True, null=True)

    # Campaign / calling
    Campaign_Id = models.CharField(max_length=100, blank=True, null=True)
    ContactId = models.CharField(max_length=100, blank=True, null=True)
    Callconnected = models.BooleanField(default=False, blank=True, null=True)
    MobileCountry_Id = models.CharField(max_length=100, blank=True, null=True)

    # Deal / prediction / misc
    Deal_Created = models.BooleanField(default=False, blank=True, null=True)
    GrowthChoice = [('Up', 'Up'), ('Down', 'Down')]
    LeadGrowth = models.CharField(max_length=250, choices=GrowthChoice, default='Down', blank=True, null=True)
    prediction = models.CharField(max_length=250, blank=True, null=True)
    Lead_Json = models.JSONField(default=dict, blank=True, null=True)
    Ratings = models.CharField(max_length=250, blank=True, null=True)
    Tags = models.JSONField(default=list, blank=True, null=True)
    Source_Details = models.CharField(max_length=250, blank=True, null=True)
    Partner_Id = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='PartnerCustomerLeadss', blank=True, null=True)

    class Meta:
        db_table = 'PartnerCustomerLead'




def PartnerOpportunity_Id_I():
    try:
        last_obj = PartnerOpportunity.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerOpportunity_id:
            return "PAR_OPP" + "000000001"
        number = int(last_obj.PartnerOpportunity_id[7:])
        return "PAR_OPP" + str(number + 1).zfill(9)
    except Exception:
        return "PAR_OPP" + "000000001"


class PartnerOpportunity(models.Model):
    PartnerOpportunity_id = models.CharField(max_length=64, default=PartnerOpportunity_Id_I, blank=True, null=True)
    opportunity_code = models.CharField(max_length=64, unique=True, blank=True, null=True)
    deal_name = models.CharField(max_length=255, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_domain = models.CharField(max_length=255, blank=True, null=True)
    customer_contact_person = models.CharField(max_length=128, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=32, blank=True, null=True)
    industry = models.CharField(max_length=128, default='Enterprise Business', blank=True, null=True)
    city = models.CharField(max_length=64, default='Bengaluru', blank=True, null=True)
    country = models.CharField(max_length=64, default='India', blank=True, null=True)
    target_products = models.JSONField(default=list, blank=True, null=True)
    estimated_deal_value = models.DecimalField(max_digits=12, decimal_places=2, default=250000, blank=True, null=True)
    currency = models.CharField(max_length=16, default='INR', blank=True, null=True)
    estimated_users = models.IntegerField(default=100, blank=True, null=True)
    deal_stage = models.CharField(max_length=32, default='Qualification', blank=True, null=True)
    deal_status = models.CharField(max_length=32, default='Active', blank=True, null=True)
    expected_closing_date = models.DateField(blank=True, null=True)
    actual_closing_date = models.DateField(blank=True, null=True)
    commission_plan = models.CharField(max_length=128, default='Project-Specific Fee Agreement', blank=True, null=True)
    expected_commission = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    final_commission = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    business_requirements = models.TextField(blank=True, null=True)
    lost_reason = models.TextField(blank=True, null=True)
    partner_org_id = models.CharField(max_length=64, default='org-cloudcraft-01', blank=True, null=True)
    partner_org_name = models.CharField(max_length=255, default='CloudCraft Solutions Pvt. Ltd.', blank=True, null=True)
    activities = models.JSONField(default=list, blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        db_table = 'PartnerOpportunity'


def PartnerCustomer_Id_I():
    try:
        last_obj = PartnerCustomer.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerCustomer_id:
            return "PAR_CUST" + "000000001"
        number = int(last_obj.PartnerCustomer_id[8:])
        return "PAR_CUST" + str(number + 1).zfill(9)
    except Exception:
        return "PAR_CUST" + "000000001"


class PartnerCustomer(models.Model):
    PartnerCustomer_id = models.CharField(max_length=64, default=PartnerCustomer_Id_I, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=128, blank=True, null=True)
    contact_person = models.CharField(max_length=128, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    city = models.CharField(max_length=64, default='Bengaluru', blank=True, null=True)
    state = models.CharField(max_length=64, default='Karnataka', blank=True, null=True)
    country = models.CharField(max_length=64, default='India', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    partner_org_id = models.CharField(max_length=64, default='org-cloudcraft-01', blank=True, null=True)
    associated_lead_ids = models.JSONField(default=list, blank=True, null=True)
    associated_deal_ids = models.JSONField(default=list, blank=True, null=True)
    active_project_ids = models.JSONField(default=list, blank=True, null=True)
    interactions = models.JSONField(default=list, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        db_table = 'PartnerCustomer'


def BusinessCommission_ID_I():
    try:
        last_obj = BusinessCommission.objects.all().order_by('id').last()
        if not last_obj or not last_obj.BusinessCommission_id:
            return "PAR_COMM" + "000000001"
        number = int(last_obj.BusinessCommission_id[8:])
        return "PAR_COMM" + str(number + 1).zfill(9)
    except Exception:
        return "PAR_COMM" + "000000001"


class BusinessCommission(models.Model):
    BusinessCommission_id = models.CharField(max_length=64, default=BusinessCommission_ID_I, blank=True, null=True)
    commission_code = models.CharField(max_length=64, unique=True, blank=True, null=True)
    partner_id = models.CharField(max_length=64, default='org-cloudcraft-01', blank=True, null=True)
    deal_id = models.CharField(max_length=64, blank=True, null=True)
    deal_code = models.CharField(max_length=64, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    product_name = models.CharField(max_length=64,blank=True, null=True)
    deal_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    calculated_commission = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    approval_status = models.CharField(max_length=32, blank=True, null=True)
    payment_status = models.CharField(max_length=32, blank=True, null=True)
    related_project_code = models.CharField(max_length=64, blank=True, null=True)
    approved_by = models.CharField(max_length=128, blank=True, null=True)
    approved_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        db_table = 'BusinessCommission'


def PartnerPayout_ID_I():
    try:
        last_obj = PartnerPayout.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerPayout_id:
            return "PAR_PAY" + "000000001"
        number = int(last_obj.PartnerPayout_id[7:])
        return "PAR_PAY" + str(number + 1).zfill(9)
    except Exception:
        return "PAR_PAY" + "000000001"


class PartnerPayout(models.Model):
    PartnerPayout_id = models.CharField(max_length=64, default=PartnerPayout_ID_I, blank=True, null=True)
    payout_id = models.CharField(max_length=64, unique=True, blank=True, null=True)
    partner_id = models.CharField(max_length=64, default='org-cloudcraft-01', blank=True, null=True)
    settlement_cycle = models.CharField(max_length=64, default='Oct 2026 Batch #01', blank=True, null=True)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    tds_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    net_payable = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    related_project_code = models.CharField(max_length=64, blank=True, null=True)
    settlement_date = models.DateField(blank=True, null=True)
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='prepared_payouts')
    utr_reference = models.CharField(max_length=64, blank=True, null=True)
    disbursement_date = models.DateField(blank=True, null=True)
    statement_url = models.CharField(max_length=255, default='#', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        db_table = 'PartnerPayout'


def BusinessResource_ID_I():
    try:
        last_obj = BusinessResource.objects.all().order_by('id').last()
        if not last_obj or not last_obj.BusinessResource_id:
            return "BUS_RES" + "000000001"
        number = int(last_obj.BusinessResource_id[7:])
        return "BUS_RES" + str(number + 1).zfill(9)
    except Exception:
        return "BUS_RES" + "000000001"


class BusinessResource(models.Model):
    BusinessResource_id = models.CharField(max_length=64, default=BusinessResource_ID_I, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=32, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    format = models.CharField(max_length=16, default='PDF', blank=True, null=True)
    file_size = models.CharField(max_length=32, default='2.4 MB', blank=True, null=True)
    download_url = models.CharField(max_length=255, default='#', blank=True, null=True)
    tags = models.JSONField(default=list, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        db_table = 'BusinessResource'


# -----------------------------------------------------------------------------
# 3. DELIVERY DOMAIN MODELS
# -----------------------------------------------------------------------------

def ImplementationProject_ID_I():
    try:
        last_obj = ImplementationProject.objects.all().order_by('id').last()
        if not last_obj or not last_obj.ImplementationProject_id:
            return "IMP_PJ" + "000000001"
        number = int(last_obj.ImplementationProject_id[6:])
        return "IMP_PJ" + str(number + 1).zfill(9)
    except Exception:
        return "IMP_PJ" + "000000001"


class ImplementationProject(models.Model):
    ImplementationProject_id = models.CharField(max_length=64, default=ImplementationProject_ID_I, blank=True, null=True)
    project_code = models.CharField(max_length=64, unique=True, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    partner_org_id = models.CharField(max_length=64, blank=True, null=True)
    partner_org_name = models.CharField(max_length=255, blank=True, null=True)
    product = models.CharField(max_length=64, blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    progress_percentage = models.IntegerField(default=45, blank=True, null=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=250000, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    target_go_live_date = models.DateField(blank=True, null=True)
    actual_go_live_date = models.DateField(blank=True, null=True)
    lead_consultant_name = models.CharField(max_length=128, default='Priya Sharma', blank=True, null=True)
    lead_consultant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_projects')
    assigned_consultant_ids = models.JSONField(default=list, blank=True, null=True)
    milestones = models.JSONField(default=list, blank=True, null=True)
    allocated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='allocated_projects')
    allocated_at = models.DateTimeField(null=True, blank=True)
    uat_signed_off = models.BooleanField(default=False, blank=True, null=True)
    uat_signed_off_at = models.DateTimeField(null=True, blank=True)
    uat_signed_off_by = models.CharField(max_length=128, null=True, blank=True)
    uat_signed_off_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uat_signed_projects')
    customer_final_acceptance = models.BooleanField(default=False, blank=True, null=True)
    customer_acceptance_document = models.CharField(max_length=255, null=True, blank=True)
    admin_completion_approved = models.BooleanField(default=False, blank=True, null=True)
    admin_completion_approved_at = models.DateTimeField(null=True, blank=True)
    admin_completion_approved_by = models.CharField(max_length=128, null=True, blank=True)
    admin_completion_approved_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_completion_projects')
    customer_payment_collected = models.BooleanField(default=False, blank=True, null=True)
    customer_payment_reference = models.CharField(max_length=128, blank=True, null=True)
    customer_payment_date = models.DateField(blank=True, null=True)
    audit_trail = models.JSONField(default=list, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        db_table = 'ImplementationProject'




def TenantProvisioningJob_ID_I():
    try:
        last_obj = TenantProvisioningJob.objects.all().order_by('id').last()
        if not last_obj or not last_obj.TenantProvisioningJob_id:
            return "TPJ" + "000000001"
        number = int(last_obj.TenantProvisioningJob_id[3:])
        return "TPJ" + str(number + 1).zfill(9)
    except Exception:
        return "TPJ" + "000000001"


class TenantProvisioningJob(models.Model):
    TenantProvisioningJob_id = models.CharField(max_length=64, default=TenantProvisioningJob_ID_I, blank=True, null=True)
    job_code = models.CharField(max_length=64, unique=True, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    product = models.CharField(max_length=64, default='Pegatto Retail', blank=True, null=True)
    subdomain = models.CharField(max_length=128, blank=True, null=True)
    environment = models.CharField(max_length=32, default='PRODUCTION', blank=True, null=True)
    status = models.CharField(max_length=32, default='COMPLETED', blank=True, null=True)
    cloud_region = models.CharField(max_length=64, default='asia-south1 (Mumbai)', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        db_table = 'TenantProvisioningJob'


def PartnerTeamMember_ID_I():
    try:
        last_obj = PartnerTeamMember.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerTeamMember_id:
            return "PTT" + "000000001"
        number = int(last_obj.PartnerTeamMember_id[3:])
        return "PTT" + str(number + 1).zfill(9)
    except Exception:
        return "PTT" + "000000001"


def PartnerTeam_ID_I():
    return PartnerTeamMember_ID_I()


class PartnerTeamMember(models.Model):
    PartnerTeamMember_id = models.CharField(max_length=1000, default=PartnerTeamMember_ID_I, blank=True, null=True)
    # User_Id = models.CharField(max_length=64, blank=True, null=True)
    First_Name = models.CharField(max_length=128, blank=True, null=True)
    Last_Name = models.CharField(max_length=128, blank=True, null=True)
    Email = models.EmailField(blank=True, null=True)
    Phone_Number = models.CharField(max_length=32, blank=True, null=True)
    Password = models.CharField(max_length=1000, blank=True, null=True)
    Role = models.CharField(max_length=64, blank=True, null=True)
    Designation = models.CharField(max_length=128, blank=True, null=True)
    Profile_Image = models.ImageField(upload_to='partner_team/', blank=True, null=True)
    Is_Primary_User = models.BooleanField(default=False, blank=True, null=True)
    Is_Active = models.BooleanField(default=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_Date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Updated_Date = models.DateTimeField(auto_now=True, blank=True, null=True)
    Partner_Id = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='partner_team_members', blank=True, null=True)
    Created_By = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_team_members')
    Updated_By = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_team_members')

    class Meta:
        db_table = 'PartnerTeamMember'


# class PartnerTeam(models.Model):
#     PartnerTeam_id = models.CharField(max_length=64, primary_key=True, default=PartnerTeam_ID_I)
#     partner_org_id = models.CharField(max_length=64, blank=True, null=True)
#     user_id = models.CharField(max_length=64, blank=True, null=True)
#     password = models.CharField(max_length=1000, blank=True, null=True)
#     role = models.CharField(max_length=32, blank=True, null=True)
#     is_active = models.BooleanField(default=True, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     created_by = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_partner_team_members')
#     updated_by = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_partner')
#     Is_Deleted = models.BooleanField(default=False)

#     class Meta:
#         db_table = 'PartnerTeam'


def PartnerDeal_ID_I():
    try:
        last_obj = PartnerDeal.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerDeal_id:
            return "PDI" + "000000001"
        number = int(last_obj.PartnerDeal_id[3:])
        return "PDI" + str(number + 1).zfill(9)
    except Exception:
        return "PDI" + "000000001"


class PartnerDeal(models.Model):
    PartnerDeal_id = models.CharField(max_length=64, default=PartnerDeal_ID_I, blank=True, null=True)
    partner_org_id = models.CharField(max_length=64, blank=True, null=True)
    deal_name = models.CharField(max_length=255, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    estimated_deal_value = models.DecimalField(max_digits=12, decimal_places=2, default=250000, blank=True, null=True)
    deal_stage = models.CharField(max_length=32, blank=True, null=True)
    expected_closing_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_partner_deals')
    updated_by = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_partner_deals')
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        db_table = 'PartnerDeal'




def DailyWorkUpdate_ID_I():
    try:
        last_obj = DailyWorkUpdate.objects.all().order_by('id').last()
        if not last_obj or not last_obj.DailyWorkUpdate_id:
            return "DWU" + "000000001"
        number = int(last_obj.DailyWorkUpdate_id[3:])
        return "DWU" + str(number + 1).zfill(9)
    except Exception:
        return "DWU" + "000000001"


class DailyWorkUpdate(models.Model):
    DailyWorkUpdate_id = models.CharField(max_length=64, default=DailyWorkUpdate_ID_I, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    project_code = models.CharField(max_length=64, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    consultant_id = models.CharField(max_length=64, blank=True, null=True)
    consultant_name = models.CharField(max_length=128, blank=True, null=True)
    partner_org_id = models.CharField(max_length=64, default='org-cloudcraft-01', blank=True, null=True)
    work_date = models.DateField(blank=True, null=True)
    hours_logged = models.DecimalField(max_digits=4, decimal_places=2, default=8.0, blank=True, null=True)
    tasks_completed = models.TextField(blank=True, null=True)
    tasks_planned_tomorrow = models.TextField(blank=True, null=True)
    blockers = models.TextField(blank=True, null=True)
    is_blocked = models.BooleanField(default=False, blank=True, null=True)
    review_status = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    Partner_Id = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='partner_dailywork', blank=True, null=True)
    PartnerTeamMember_Id = models.ForeignKey(PartnerTeamMember, on_delete=models.CASCADE, related_name='partner_dailywork', blank=True, null=True)

    class Meta:
        db_table = 'DailyWorkUpdate'




# PARTNER COMMISSION

from CRMSuperAdmin.models import *
from CRMUserAdmin.models import *


def PartnerCommissionRule_ID_I():
    try:
        last_obj = PartnerCommissionRule.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerCommissionRule_id:
            return "PCR" + "000000001"
        number = int(last_obj.PartnerCommissionRule_id[3:])
        return "PCR" + str(number + 1).zfill(9)
    except Exception:
        return "PCR" + "000000001"


# ==================== Partner Commission Rule ====================

class PartnerCommissionRule(models.Model):
    PartnerCommissionRule_id = models.CharField(max_length=64, default=PartnerCommissionRule_ID_I, blank=True, null=True)
    Commission_Type = models.CharField(max_length=50, blank=True, null=True)
    Commission_Percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)
    Is_Active = models.BooleanField(default=True, blank=True, null=True)
    Effective_From = models.DateField(default=timezone.now, blank=True, null=True)
    Effective_To = models.DateField(blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Created_By = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='create_partner_comm')
    Updated_By = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='update_partner_comm')

    class Meta:
        db_table = 'PartnerCommissionRule'


def PartnerCommission_ID_I():
    try:
        last_obj = PartnerCommission.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerCommission_id:
            return "PC" + "000000001"
        number = int(last_obj.PartnerCommission_id[2:])
        return "PC" + str(number + 1).zfill(9)
    except Exception:
        return "PC" + "000000001"


# ==================== Partner Commission ====================

class PartnerCommission(models.Model):
    COMMISSION_TYPES = [
        ('Implementation', 'Implementation'),
        ('Product', 'Product'),
        ('Extension', 'Extension'),
    ]

    COMMISSION_STATUS = [
        ('Pending', 'Pending'),
        ('Eligible', 'Eligible'),
        ('Invoice Submitted', 'Invoice Submitted'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Paid', 'Paid'),
    ]

    PartnerCommission_id = models.CharField(max_length=64, default=PartnerCommission_ID_I, blank=True, null=True)
    Partner_Id = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='partner_commissions', blank=True, null=True)
    Customer_Id = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='partner_commissions', blank=True, null=True)
    Invoice_Id = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='partner_commissions', blank=True, null=True)
    InstanceRequest_Id = models.ForeignKey(InstanceRequest, on_delete=models.CASCADE, related_name='partner_commissions', blank=True, null=True)
    Product_Id = models.ForeignKey(ProductMaster, on_delete=models.CASCADE, related_name='partner_commissions', blank=True, null=True)
    Rule_Id = models.ForeignKey(PartnerCommissionRule, on_delete=models.SET_NULL, related_name='partner_commissions', blank=True, null=True)
    Commission_Type = models.CharField(max_length=50, choices=COMMISSION_TYPES, blank=True, null=True)
    Sales_Order_Value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True)
    Commission_Percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)
    Commission_Amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True)
    Eligibility_Status = models.CharField(max_length=30, default='Not Eligible', blank=True, null=True)
    Commission_Status = models.CharField(max_length=50, choices=COMMISSION_STATUS, default='Pending', blank=True, null=True)
    Implementation_Completed = models.BooleanField(default=False, blank=True, null=True)
    Customer_Signoff_Received = models.BooleanField(default=False, blank=True, null=True)
    Customer_Payment_Received = models.BooleanField(default=False, blank=True, null=True)
    Eligible_Date = models.DateTimeField(blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)

    class Meta:
        db_table = 'PartnerCommission'



def PartnerCommissionInvoice_ID_I():
    try:
        last_obj = PartnerCommissionInvoice.objects.all().order_by('id').last()
        if not last_obj or not last_obj.PartnerCommissionInvoice_id:
            return "PCI" + "000000001"
        number = int(last_obj.PartnerCommissionInvoice_id[3:])
        return "PCI" + str(number + 1).zfill(9)
    except Exception:
        return "PCI" + "000000001"


# ==================== Partner Commission Invoice ====================

class PartnerCommissionInvoice(models.Model):
    APPROVAL_STATUS = [
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Paid', 'Paid'),
    ]

    PartnerCommissionInvoice_id = models.CharField(max_length=64, default=PartnerCommissionInvoice_ID_I, blank=True, null=True)
    Partner_Id = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='commission_invoices', blank=True, null=True)
    PartnerCommission_Id = models.ForeignKey(PartnerCommission, on_delete=models.CASCADE, related_name='commission_invoices', blank=True, null=True)
    Partner_Invoice_No = models.CharField(max_length=100, blank=True, null=True)
    Partner_Invoice_Date = models.DateField(blank=True, null=True)
    Invoice_Amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True)
    Invoice_File = models.FileField(blank=True, null=True)
    Invoice_File_Name = models.CharField(max_length=100, blank=True, null=True)
    Approval_Status = models.CharField(max_length=30, choices=APPROVAL_STATUS, default='Submitted', blank=True, null=True)
    Approved_By = models.ForeignKey(UserAdmin, on_delete=models.SET_NULL, related_name='approved_partner_commission_invoices', blank=True, null=True)
    Approved_Date = models.DateTimeField(blank=True, null=True)
    Rejection_Reason = models.TextField(blank=True, null=True)
    Payment_Status = models.CharField(max_length=30, choices=PAYMENT_STATUS, default='Pending', blank=True, null=True)
    Payment_Date = models.DateTimeField(blank=True, null=True)
    Payment_Reference_No = models.CharField(max_length=150, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Created_By = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='create_partner_invoice')

    class Meta:
        db_table = 'PartnerCommissionInvoice'








