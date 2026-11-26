from uuid import uuid4
# =========================
# 1. Python Standard Library
# =========================
from datetime import date
from secrets import choice
from random import choices
from enum import unique
from email.policy import default

# =========================
# 2. Django Imports
# =========================
from django.db import models
from django.utils import timezone
from django.conf import settings

from django.contrib.auth import get_user_model
UserAdmin = get_user_model()
from django.contrib.auth.models import Group, Permission

from django.core.validators import MaxValueValidator, MinValueValidator

from django.db.models.signals import post_save
from django.dispatch import receiver

# =========================
# 3. Project-Specific Imports
# =========================
from CRMSuperAdmin.Tenant_DB_Creation import create_tenant_database
from CRMUserAdmin.models import *


# Super Admin Models


# Auto increment function for Leads
def Lead_ID_I():
    Organizatio = Leads.objects.all().order_by('id').last()
    if not Organizatio:
        return "LED" + "000000001"
    Organizati = Organizatio.LeadId
    Organizat = int(Organizati[3:])
    Organiza = Organizat + 1
    Configur = "LED" + str(Organiza).zfill(9)
    return Configur



class Leads(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE, blank=True, null=True)
    LeadId = models.CharField(unique=True, max_length=1000, default=Lead_ID_I, blank=True, null=True)
    Salutation = models.CharField(max_length=20, blank=True, null=True)
    LeadFirstName = models.CharField(max_length=50, blank=True, null=True)
    File = models.FileField(blank=True, null=True)
    FileName = models.CharField(max_length=250, blank=True, null=True)
    LeadLastName = models.CharField(max_length=50, blank=True, null=True)
    LeadType = models.CharField(max_length=100, blank=True, null=True)
    Pincode = models.CharField(max_length=250, blank=True, null=True)
    CompanyName = models.CharField(max_length=100, blank=True, null=True)
    PhoneNo = models.CharField(max_length=20, blank=True, null=True, unique=True)
    EmailId = models.CharField(max_length=100, unique=True, blank=True, null=True)
    WebsiteURL = models.CharField(max_length=10000, blank=True, null=True)
    BuildingDoorNo = models.CharField(max_length=10000, blank=True, null=True)
    StreetName = models.CharField(max_length=50, blank=True, null=True)
    AreaName = models.CharField(max_length=50, blank=True, null=True)
    City = models.CharField(max_length=50, blank=True, null=True)
    State = models.CharField(max_length=50, blank=True, null=True)
    Country = models.CharField(max_length=50, blank=True, null=True)
    LeadSource = models.CharField(max_length=1000, blank=True, null=True)
    LeadScore = models.IntegerField(default=0, blank=True, null=True)
    StatusChoice = [('Cool', 'Cool'), ('Warm', 'Warm'), ('Hot', 'Hot')]
    Lead_Stage = models.CharField(max_length=250, null=True, blank=True)
    Recommaned_Action = models.CharField(max_length=1000, null=True, blank=True)
    Lead_Status = models.CharField(max_length=100, default="open", blank=True, null=True)
    LifeCycleStage = models.CharField(max_length=250, null=True, blank=True)
    Maps = models.CharField(max_length=10000, default='', blank=True, null=True)
    LeadDescription = models.CharField(max_length=2500, null=True, blank=True)
    LeadMLQStatus = models.BooleanField(default=False, blank=True, null=True)
    LeadMLQuestions = models.JSONField(null=True, blank=True)
    LeadSLQStatus = models.BooleanField(default=False, blank=True, null=True)
    LeadSLQuestions = models.JSONField(null=True, blank=True)
    LeadQualifyStatus = models.BooleanField(default=False, blank=True, null=True)
    GrowthChoice = [('Up', 'Up'), ("Down", "Down")]
    Lead_Owner = models.CharField(max_length=100, blank=True, null=True)
    Lead_Owner_Id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leadownerqualified", blank=True, null=True)
    Job_Title = models.CharField(max_length=1000, blank=True, null=True)
    Job_Role = models.CharField(max_length=1000, blank=True, null=True)
    Designation = models.CharField(max_length=1000, blank=True, null=True)
    Decissionmaker = models.BooleanField(default=False, blank=True, null=True)
    Yrs_of_Experience = models.CharField(max_length=1000, blank=True, null=True)
    LeadNoOfEmployees = models.IntegerField(blank=True, null=True)
    Lead_Industry = models.CharField(max_length=100, blank=True, null=True)
    LeadCompanyTurnOver = models.FloatField(blank=True, null=True)
    Head_Quarter = models.CharField(max_length=1000, blank=True, null=True)
    LeadLocation = models.CharField(max_length=1000, null=True, blank=True)
    Year_of_Founded = models.CharField(max_length=1000, blank=True, null=True)
    Organization_structure = models.CharField(max_length=1000, blank=True, null=True)
    LeadSource = models.CharField(max_length=100, blank=True, null=True)
    Budget_Availability = models.CharField(max_length=1000, blank=True, null=True)
    Budget = models.CharField(max_length=1000, blank=True, null=True)
    Level_of_detail_provided = models.CharField(max_length=1000, blank=True, null=True)
    Previous_purchases = models.CharField(max_length=1000, blank=True, null=True)
    Campaign_Id = models.CharField(max_length=100, blank=True, null=True)
    ContactId = models.CharField(max_length=100, blank=True, null=True)
    Callconnected = models.BooleanField(default=False, blank=True, null=True)
    MobileCountry_Id = models.CharField(max_length=100, blank=True, null=True)
    Deal_Created = models.BooleanField(default=False, blank=True, null=True)
    LeadGrowth = models.CharField(max_length=250, choices=GrowthChoice, default="Down", blank=True, null=True)
    prediction = models.CharField(max_length=250, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Lead_Json = models.JSONField(default=dict, blank=True, null=True)
    Company_status = models.BooleanField(default=False, blank=True, null=True)
    MQL_Qualified_Date = models.DateField(default=date.today(), null=True, blank=True)
    SQL_Qualified_Date = models.DateField(default=date.today(), null=True, blank=True)
    Created_By = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    Created_Date = models.DateField(default=date.today(), blank=True, null=True)
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Userupdatedqualifiedlead', blank=True, null=True)
    Updated_Date = models.DateField(default=date.today(), blank=True, null=True)
    Ratings = models.CharField(max_length=250, blank=True, null=True)
    Tags = models.JSONField(default=list, null=True, blank=True)
    Source_Details = models.CharField(max_length=250, blank=True, null=True)
    Notes = models.CharField(max_length=250, blank=True, null=True)
    Prefered_Contact_Method = models.CharField(max_length=250, blank=True, null=True)
    Fax = models.CharField(max_length=250, blank=True, null=True)
    LinkedIn_Profile = models.CharField(max_length=250, blank=True, null=True)
    Twitter_Profile = models.CharField(max_length=250, blank=True, null=True)
    Date_Of_Birth = models.CharField(max_length=250, blank=True, null=True)
    Mobile_No = models.CharField(max_length=20, blank=True, null=True, unique=True)

    #shajitha on 19-11-2026
    Partner_Id = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, blank=True, null=True)
    Customer_Id = models.IntegerField(default=1, blank=True, null=True)
    Partner_Or_Customer_Leads = models.CharField(max_length=250, blank=True, null=True)  # Partner Or Customer

    class Meta:
        db_table = 'Leads'


# Auto increment function for Deal
def Deal_ID_I():
    Organizatio = Deal.objects.all().order_by('id').last()
    if not Organizatio:
        return "DEA" + "000000001"
    Organizati = Organizatio.Deal_Id
    Organizat = int(Organizati[3:])
    Organiza = Organizat + 1
    Configur = "DEA" + str(Organiza).zfill(9)
    return Configur


class Deal(models.Model):

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE, blank=True, null=True)
    Deal_Id = models.CharField(unique=True, max_length=20, default=Deal_ID_I, blank=True, null=True)
    Deal_Code = models.CharField(max_length=100, blank=True, null=True)
    Deal_Name = models.CharField(max_length=100, blank=True, null=True)
    Deal_Type = models.CharField(max_length=100, blank=True, null=True)
    # Account_Id=models.ForeignKey(Account,on_delete=models.CASCADE,blank=True,null=True)
    Account_Name = models.CharField(max_length=100, blank=True, null=True)
    Lead_Id = models.ForeignKey('partner.PartnerCustomerLead', on_delete=models.CASCADE, blank=True, null=True)
    Lead_Name = models.CharField(max_length=100, blank=True, null=True)
    Contact_Person = models.CharField(max_length=100, blank=True, null=True)
    Phoene = models.CharField(max_length=100, blank=True, null=True)
    Amount = models.IntegerField(default=0, blank=True, null=True)
    Deal_Owner = models.CharField(max_length=100, blank=True, null=True)
    DealScore = models.FloatField(default=0, blank=True, null=True)
    ApproxDealAmount = models.FloatField(default=0, blank=True, null=True)
    ActualDealAmount = models.FloatField(default=0, blank=True, null=True)
    MinimumTurnOver = models.FloatField(default=0, blank=True, null=True)
    Current_Status = models.CharField(max_length=100, blank=True, null=True)
    Deal_Stage = models.CharField(max_length=255, blank=True, null=True)
    Lost_Reason = models.CharField(max_length=255, blank=True, null=True)
    Lead_Source = models.CharField(max_length=255, blank=True, null=True)
    # Deal_competitor=models.CharField(max_length=100,blank=True)
    # Competitor_Price=models.CharField(max_length=100,blank=True)
    Deal_Competitor = models.JSONField(default=dict, blank=True, null=True)
    Deal_Probablity = models.CharField(max_length=1000, blank=True, null=True)
    Probability_Id = models.IntegerField(default=0, blank=True, null=True)
    Next_Step = models.CharField(max_length=1000, blank=True, null=True)
    Deal_Note = models.TextField(max_length=10000, blank=True, null=True)
    ExpClosing_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Recommaned_Action = models.CharField(max_length=100, blank=True, null=True)
    Prediction = models.CharField(max_length=100, blank=True, null=True)
    Active_Flag = models.BooleanField(default=False, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Deal_Json = models.JSONField(default=dict, blank=True, null=True)
    Won_Deal_Date = models.DateField(default=date.today(), blank=True, null=True)
    Created_By = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    Created_Date = models.DateField(default=date.today(), blank=True, null=True)
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name="updateDeal", blank=True, null=True)
    Updated_Date = models.DateField(default=date.today(), blank=True, null=True)
    Attachfile = models.FileField(blank=True, null=True)
    Pipeline_Name = models.CharField(max_length=100, blank=True, null=True)
    Campaign_Name = models.CharField(max_length=100, blank=True, null=True)
    #shajitha
    Partner_Id = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, blank=True, null=True)   # need because customer leads will be here and assigend to partner's by superadmin
    Product_Name = models.CharField(max_length=100, blank=True, null=True)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='dealproduct')

    @property
    def Products(self):
        return self.Product_Name

    @Products.setter
    def Products(self, value):
        self.Product_Name = value


    class Meta:
        db_table = 'Deal'




def Account_ID_I():
    Organizatio = Account.objects.all().order_by('id').last()
    if not Organizatio:
        return "ACC" + "000000001"
    Organizati = Organizatio.Account_Id
    Organizat = int(Organizati[3:])
    Organiza = Organizat + 1
    Configur = "ACC" + str(Organiza).zfill(9)
    return Configur


class Account(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE, blank=True, null=True)
    Account_Id = models.CharField(unique=True, max_length=20, default=Account_ID_I, blank=True, null=True)
    File = models.FileField(blank=True, null=True)
    FileName = models.CharField(max_length=250, blank=True, null=True)
    Contact_Name = models.CharField(max_length=100, blank=True, null=True)
    Account_Owner = models.CharField(max_length=100, blank=True, null=True)
    Country_Code = models.CharField(max_length=100, blank=True, null=True)
    Phone_Number = models.CharField(max_length=20, blank=True, null=True)
    Land_Line = models.CharField(max_length=20, blank=True, null=True)
    Mail = models.EmailField(unique=True, blank=True, null=True)
    Fax = models.CharField(max_length=100, blank=True, null=True)
    Decision_Maker = models.BooleanField(default=False, blank=True, null=True)
    Turn_Over = models.FloatField(default=0, null=True, blank=True)
    Employees = models.CharField(max_length=100, null=True, blank=True)
    Industry = models.CharField(max_length=100, null=True, blank=True)
    Website = models.CharField(max_length=100, null=True, blank=True)
    Country = models.CharField(max_length=1000, null=True, blank=True)
    State = models.CharField(max_length=1000, null=True, blank=True)
    City = models.CharField(max_length=1000, null=True, blank=True)
    Location = models.CharField(max_length=1000, null=True, blank=True)
    Latitude = models.CharField(max_length=1000, null=True, blank=True)
    Longitude = models.CharField(max_length=1000, null=True, blank=True)
    GST_No = models.CharField(max_length=1000, null=True, blank=True)
    Payment_Terms = models.CharField(max_length=1000, null=True, blank=True)
    Organization_Name = models.CharField(max_length=1000, null=True, blank=True)
    Address = models.JSONField(null=True, blank=True, max_length=1000)
    ReasonForChurn = models.CharField(null=True, blank=True, max_length=1000)
    LeadCheck = models.IntegerField(default=0, blank=True, null=True)
    Active_Flag = models.BooleanField(default=False, blank=True, null=True)
    Status_Flag = models.CharField(blank=True, null=True, max_length=1000)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, blank=True, null=True)
    Created_Date = models.DateField(default=date.today, blank=True, null=True)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name="updateAccount", blank=True, null=True) # Need To discuss & Change
    Updated_Date = models.DateField(default=date.today, blank=True, null=True)

    # shajitha 19-11-2026
    # Additional Account fields - added based on comparison
    Company_Json = models.JSONField(default=dict, blank=True, null=True)
    Gender = models.CharField(max_length=1000, blank=True, null=True)
    Date_Of_Birth = models.DateField(blank=True, null=True)
    Lead_Source = models.CharField(max_length=1000, null=True, blank=True)
    Lead_Id = models.ForeignKey('partner.PartnerCustomerLead', on_delete=models.CASCADE, blank=True, null=True)   # lead id for customer coming from lead to customer
    Lead_Name = models.CharField(max_length=100, blank=True, null=True)
    Client_Type = models.CharField(max_length=1000, null=True, blank=True)
    Client_Status = models.CharField(max_length=1000, null=True, blank=True)
    Vat_Number = models.CharField(max_length=1000, null=True, blank=True)
    Reg_Number = models.CharField(max_length=1000, null=True, blank=True)
    Branch_Office = models.CharField(max_length=1000, null=True, blank=True)
    # Attachment = models.ManyToManyField(UserFilesandUrls,blank=True,related_name='account_attachments')
    Tags = models.JSONField(default=list, blank=True, null=True)
    About = models.TextField(blank=True, null=True)

    # shajitha on 19-11-2026
    Partner_Id = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, blank=True, null=True)   # need because customer leads will be here and assigend to partner's by superadmin
    Partner_Or_Customer_Leads = models.CharField(max_length=250, blank=True, null=True)  # Partner Or Customer
    Deal_Id = models.ManyToManyField(Deal, blank=True)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='accounts')

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table = 'Account'
        ordering = ['-id']





# Add-Ons Module - Pegatto Super Admin --> Santhosh P :-



# 1. ADD-ON CATEGORIES


def AddonCategory_I():
    Task= AddonCategory.objects.all().order_by('id').last()
    if not Task:
        return "ACI" + "000000001"
    Tasking = Task. AddonCategory_Id
    Taski=int(Tasking[3:])
    Tas= Taski + 1
    Configur = "ACI" + str(Tas).zfill(9)
    return Configur


def AddonProductCompatibility_I():
    return f'APC{uuid4().hex}'


def AddonPriceTemplate_I():
    Task= AddonPriceTemplate.objects.all().order_by('id').last()
    if not Task:
        return "APT" + "000000001"
    Tasking = Task. AddonPriceTemplate_Id
    Taski=int(Tasking[3:])
    Tas= Taski + 1
    Configur = "APT" + str(Tas).zfill(9)
    return Configur



def AddonPricing_I():
    Task= AddonPricing.objects.all().order_by('id').last()
    if not Task:
        return "API" + "000000001"
    Tasking = Task. AddonPricing_Id
    Taski=int(Tasking[3:])
    Tas= Taski + 1
    Configur = "API" + str(Tas).zfill(9)
    return Configur


def AddonTieredPricing_I():
    Task= AddonTieredPricing.objects.all().order_by('id').last()
    if not Task:
        return "ATPS" + "000000001"
    Tasking = Task. AddonTieredPricing_Id
    Taski=int(Tasking[4:])
    Tas= Taski + 1
    Configur = "ATPS" + str(Tas).zfill(9)
    return Configur


def AddonDiscountCoupon_I():
    Task= AddonDiscountCoupon.objects.all().order_by('id').last()
    if not Task:
        return "ADC" + "000000001"
    Tasking = Task. AddonDiscountCoupon_Id
    Taski=int(Tasking[4:])
    Tas= Taski + 1
    Configur = "ADC" + str(Tas).zfill(9)
    return Configur


def AddonPriceHistory_I():
    Task = AddonPriceHistory.objects.all().order_by('id').last()
    if not Task:
        return "APH" + "000000001"
    Tasking = Task.AddonPriceHistory_Id
    if not Tasking:
        return "APH" + "000000001"
    try:
        Taski = int(Tasking[3:])
        Tas = Taski + 1
        Configur = "APH" + str(Tas).zfill(9)
        return Configur
    except Exception:
        import re
        digits = re.findall(r'\d+', str(Tasking))
        if digits:
            Tas = int(digits[-1]) + 1
            return "APH" + str(Tas).zfill(9)
        return "APH" + "000000001"




def AddonMaster_I():
    # Match the generated format, ignoring legacy rows with missing or custom codes.
    latest = (
        AddonMaster.objects.filter(AddonMaster_Id__regex=r'^AME([0-9]{9}|[1-9][0-9]{9,46})$')
        .order_by(models.functions.Length('AddonMaster_Id').desc(), '-AddonMaster_Id')
        .values_list('AddonMaster_Id', flat=True)
        .first()
    )
    next_number = int(latest[3:]) + 1 if latest else 1
    return f"AME{next_number:09d}"





class AddonCategory(models.Model):
    AddonCategory_Id = models.CharField(max_length=50,unique=True,default=AddonCategory_I)
    Category_Code = models.CharField(max_length=50, unique=True,blank=True,null=True)
    Category_Name = models.CharField(max_length=150)
    Description = models.TextField(blank=True, null=True)
    Display_Order = models.PositiveIntegerField(default=0)
    Show_In_Marketplace = models.BooleanField(default=True)
    Status = models.CharField(max_length=100,blank=True,null=True)
    Category_Icon = models.CharField(max_length=255, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="Created_AddonCategory")
    Created_Date = models.DateField(default=timezone.localdate)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="Updated_AddonCategory") # Need To discuss & Change
    Updated_Date = models.DateField(default=timezone.localdate)

    class Meta:
        db_table = 'AddonCategory'
        ordering = ['-id']


# 2.Existing - ADD-ON MASTER


BILLING_CYCLE_CHOICES = [
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('half_yearly', 'Half Yearly'),
    ('yearly', 'Yearly'),
    ('one_time', 'One Time'),
]




class DocumentMaster(models.Model):
    Document_Id = models.CharField(max_length=64, unique=True,blank=True,null=True)
    Account_Id = models.ForeignKey('Account',on_delete=models.CASCADE,related_name='documents')
    File = models.FileField(upload_to='account_documents/')
    FileName = models.CharField(max_length=250, blank=True, null=True)
    File_Type = models.CharField(max_length=100, blank=True, null=True)
    File_Size = models.CharField(max_length=50, blank=True, null=True)
    Description = models.CharField(max_length=1000, blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="document_create_by")
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="document_updated_by") # Need To discuss & Change
    Updated_Date = models.DateField(default=timezone.now)
    Is_Deleted = models.BooleanField(default=False)
    class Meta:
        db_table = 'DocumentMaster'
        
        
class AddonMaster(models.Model):
    BILLING_CYCLE_CHOICES = BILLING_CYCLE_CHOICES

    AddonMaster_Id = models.CharField(max_length=50,unique=True,default=AddonMaster_I)

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE, blank=True, null=True)
    Addon_Code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    Addon_Name = models.CharField(max_length=250, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    Products = models.ManyToManyField('ProductMaster', blank=True, db_table='AddonMaster_Products', related_name='addons')
    Plans = models.ManyToManyField('Plan', blank=True, db_table='AddonMaster_Plans', related_name='addons')
    Category = models.CharField(max_length=100, blank=True, null=True)
    Billing_Cycle = models.CharField(max_length=20, default='monthly', choices=BILLING_CYCLE_CHOICES, blank=True, null=True)
    Price = models.FloatField(default=0, blank=True, null=True)
    Tax = models.CharField(max_length=100, blank=True, null=True)
    TaxPercentage = models.FloatField(default=0, blank=True, null=True)
    TaxAmount = models.FloatField(default=0, blank=True, null=True)
    TotalAmount = models.FloatField(default=0, blank=True, null=True)
    NoofUsers = models.IntegerField(default=0, blank=True, null=True)
    Currency_code = models.CharField(max_length=10, default='INR', blank=True, null=True)
    Country = models.CharField(max_length=100, blank=True, null=True)
    Features = models.JSONField(default=list, blank=True, null=True)
    Cloudflare_Public_Id = models.JSONField(default=list, blank=True, null=True)
    Started_Date = models.DateField(default=date.today, blank=True, null=True)
    Is_Active = models.BooleanField(default=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Created_addons_SAi1', blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedaddons_SAi1', blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)

    # New Field :- Santhosh P
    # Category = models.CharField(max_length=100, blank=True, null=True)
    Addon_Category = models.ForeignKey(AddonCategory, on_delete=models.CASCADE, blank=True, null=True)
    Status = models.CharField(max_length=100,blank=True,null=True)


    Minimum_Core_API_Version = models.CharField(max_length=100, blank=True, null=True)
    Known_Incompatibilities = models.TextField(blank=True, null=True)
    Release_Version = models.CharField(max_length=100, blank=True, null=True)
    Release_Status = models.CharField(max_length=100, blank=True, null=True)
    Release_Notes = models.TextField(blank=True, null=True)

    License_Model = models.CharField(max_length=20, choices=[
        ('Per Tenant', 'Per Tenant'), ('Per User', 'Per User'),
        ('Usage Based', 'Usage Based'), ('Tiered Volume', 'Tiered Volume'),
    ], default='Per Tenant')
    Trial_Available = models.BooleanField(default=False)
    Trial_Days = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'AddonMaster'
        ordering = ['-id']




# 3. PRODUCT COMPATIBILITY

class AddonProductCompatibility(models.Model):
    AddonProductCompatibility_Id = models.CharField(max_length=50,unique=True,default=AddonProductCompatibility_I)
    Addon = models.ForeignKey('AddonMaster', on_delete=models.CASCADE, related_name='ProductCompatibilities')
    Addon_Name = models.CharField(max_length=250, blank=True, null=True)
    Product_Name = models.CharField(max_length=250, blank=True, null=True)
    Product = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, related_name='AddonCompatibilities')
    Is_Compatible = models.BooleanField(default=True)
    Compatibility_Type = models.CharField(max_length=20, blank=True,null=True)
    Dependencies = models.JSONField(default=list, blank=True)
    Version_Constraint = models.BooleanField(default=False)
    Minimum_Version = models.CharField(max_length=100, blank=True, default='')
    Maximum_Version = models.CharField(max_length=100, blank=True, default='')
    Rule_Description = models.TextField(blank=True, default='')
    Is_Active = models.BooleanField(default=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="Created_ProductCompatibility")
    Created_Date = models.DateField(default=timezone.localdate)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="Updated_ProductCompatibility") # Need To discuss & Change
    Updated_Date = models.DateField(default=timezone.localdate)

    class Meta:
        db_table = 'AddonProductCompatibility'
        constraints = [
            models.UniqueConstraint(fields=['Addon', 'Product'], name='unique_addon_product_compatibility')
        ]


# 4. PRICE TEMPLATES

class AddonPriceTemplate(models.Model):
    AddonPriceTemplate_Id = models.CharField(max_length=50,unique=True,default=AddonPriceTemplate_I)   
    Template_Code = models.CharField(max_length=50, unique=True)
    Template_Name = models.CharField(max_length=150)
    Description = models.TextField(blank=True, default='')
    Tiers = models.JSONField(default=list, blank=True)
    Discount_Percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    Show_For_New_Addons = models.BooleanField(default=False)
    Allow_Customization = models.BooleanField(default=False)
    Billing_Type = models.CharField(max_length=100,blank=True,null=True)
    Billing_Cycle = models.CharField(max_length=100,blank=True,null=True)
    Currency = models.CharField(max_length=10, default='INR')
    Is_Active = models.BooleanField(default=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="Created_AddonPriceTemplate")
    Created_Date = models.DateField(default=date.today, blank=True, null=True)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="Updated_AddonPriceTemplate") # Need To discuss & Change
    Updated_Date = models.DateField(default=date.today, blank=True, null=True)


    class Meta:
        db_table = 'AddonPriceTemplate'


# 5. ADD-ON PRICING

class AddonPricing(models.Model):

    AddonPricing_Id = models.CharField(max_length=50,unique=True,default=AddonPricing_I)   
    Addon = models.ForeignKey('AddonMaster', on_delete=models.CASCADE, related_name='PricingDetails')
    Price_Template = models.ForeignKey('AddonPriceTemplate', on_delete=models.CASCADE, related_name='AddonPrices')
    Addon_Name = models.CharField(max_length=250, blank=True, null=True)
    Price_Template_Name = models.CharField(max_length=250, blank=True, null=True)
    Pricing_Options = models.JSONField(default=dict, blank=True)
    Tier_Schedule = models.JSONField(default=dict, blank=True)
    Base_Price = models.DecimalField(max_digits=12, decimal_places=2)
    Effective_From = models.DateField(default=date.today, blank=True, null=True)
    Effective_To = models.DateField(blank=True, null=True)
    Is_Active = models.BooleanField(default=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="Created_AddonPricing")
    Created_Date = models.DateField(default=date.today, blank=True, null=True)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="Updated_AddonPricing") # Need To discuss & Change
    Updated_Date = models.DateField(default=date.today, blank=True, null=True)

    class Meta:
        db_table = 'AddonPricing'


# 6. TIERED PRICING

class AddonTieredPricing(models.Model):
    AddonTieredPricing_Id = models.CharField(max_length=50,unique=True,default=AddonTieredPricing_I)   
    Addon_Pricing = models.ForeignKey('AddonPricing', on_delete=models.CASCADE, related_name='Tiers')
    Name = models.CharField(max_length=100, blank=True, default='')
    Rate_Details = models.JSONField(default=dict, blank=True)
    Min_Employees = models.PositiveIntegerField()
    Max_Employees = models.PositiveIntegerField()
    Tier_Price = models.DecimalField(max_digits=12, decimal_places=2)
    Is_Active = models.BooleanField(default=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Created_TieredPricing', blank=True, null=True)
    Created_Date = models.DateTimeField(default=date.today, blank=True, null=True)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updateTieredPricing', blank=True, null=True)
    Updated_Date = models.DateTimeField(default=date.today, blank=True, null=True)

    class Meta:
        db_table = 'AddonTieredPricing'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(Min_Employees__lte=models.F('Max_Employees')),
                name='valid_addon_employee_tier_range'
            )
        ]


# 7. DISCOUNTS & COUPONS

class AddonDiscountCoupon(models.Model):
    Name = models.CharField(max_length=150, blank=True, default='')
    Kind = models.CharField(max_length=10, choices=[('Discount', 'Discount'), ('Coupon', 'Coupon')], default='Coupon')
    Applicability = models.CharField(max_length=15, choices=[('Subscription', 'Subscription'), ('Add-on', 'Add-on'), ('All', 'All')], default='Add-on')
    Scope = models.CharField(max_length=15, choices=[('All', 'All'), ('New', 'New'), ('Existing', 'Existing')], default='All')
    Applicable_Products = models.ManyToManyField('ProductMaster', blank=True, related_name='DiscountCoupons')
    Applicable_Plans = models.ManyToManyField('Plan', blank=True, related_name='DiscountCoupons')
    Per_Customer_Limit = models.PositiveIntegerField(blank=True, null=True)
    AddonDiscountCoupon_Id = models.CharField(max_length=50,unique=True,default=AddonDiscountCoupon_I)   
    Coupon_Code = models.CharField(max_length=50, unique=True)
    Discount_Type = models.CharField(max_length=100,blank=True,null=True)
    Discount_Value = models.DecimalField(max_digits=12, decimal_places=2)
    Applicable_Addons = models.ManyToManyField('AddonMaster', blank=True, related_name='DiscountCoupons')
    Valid_From = models.DateTimeField()
    Valid_To = models.DateTimeField()
    Usage_Limit = models.PositiveIntegerField(blank=True, null=True)
    Is_Active = models.BooleanField(default=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Created_Discount', blank=True, null=True)
    Created_Date = models.DateTimeField(default=date.today, blank=True, null=True)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updateDiscount', blank=True, null=True)
    Updated_Date = models.DateTimeField(default=date.today, blank=True, null=True)


    class Meta:
        db_table = 'AddonDiscountCoupon'


# 8. PRICE HISTORY

class AddonPriceHistory(models.Model):
    AddonPriceHistory_Id = models.CharField(max_length=50,unique=True,default=AddonPriceHistory_I)   
    Addon_Pricing = models.ForeignKey('AddonPricing', on_delete=models.PROTECT, related_name='PriceHistory')
    Old_Base_Price = models.DecimalField(max_digits=12, decimal_places=2)
    New_Base_Price = models.DecimalField(max_digits=12, decimal_places=2)
    Reason = models.TextField(blank=True, null=True)
    Changed_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Created_PriceHistory', blank=True, null=True)
    Change_Date = models.DateTimeField(default=date.today, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
   
    class Meta:
        db_table = 'AddonPriceHistory'
        ordering = ['-Change_Date']






##created by Kavitha 

def ProductCategory_I():
    Task = ProductCategory.objects.all().order_by('id').last()
    if not Task:
        return "PCY" + "000000001"
    Tasking = Task.Category_Id
    if not Tasking:
        return "PCY" + "000000001"
    try:
        Taski = int(Tasking[3:])
        Tas = Taski + 1
        Configur = "PCY" + str(Tas).zfill(9)
        return Configur
    except Exception:
        import re
        digits = re.findall(r'\d+', str(Tasking))
        if digits:
            Tas = int(digits[-1]) + 1
            return "PCY" + str(Tas).zfill(9)
        return "PCY" + "000000001"


class ProductCategory(models.Model):
    Category_Id = models.CharField(max_length=50, unique=True, default=ProductCategory_I)
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE, blank=True, null=True)
    Category_Code = models.CharField(max_length=100, blank=True, null=True)
    Category_Name = models.CharField(max_length=250, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    Is_Active = models.BooleanField(default=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='created_product_category_set', blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updated_product_category_set', blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)

    class Meta:
        db_table = 'ProductCategory'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['Organization_Id', 'Category_Code'],
                name='unique_product_category_code_per_org'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.Category_Id:
            self.Category_Id = ProductCategory_I()
        if not self.Category_Code:
            self.Category_Code = self.Category_Id
        super().save(*args, **kwargs)

    def __str__(self):
        return self.Category_Name or ''


class ProductMaster(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE, blank=True, null=True)
    Product_Code = models.CharField(max_length=100, blank=True, null=True, unique=True)
    Product_Name = models.CharField(max_length=250, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    Detailed_Description = models.TextField(blank=True, null=True)
    Category = models.CharField(max_length=100, blank=True, null=True)
    Category_id = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, blank=True, null=True)
    Features = models.JSONField(default=list, blank=True, null=True)
    Cloudflare_Public_Id = models.JSONField(default=list, blank=True, null=True)
    Status = models.CharField(max_length=250, blank=True, null=True)
    Current_version =  models.CharField(max_length=100, blank=True, null=True)
    Release_Date = models.DateField(blank=True, null=True)
    Product_Logo = models.CharField(max_length=500,blank=True,null=True)
    Product_Icon = models.CharField(max_length=500,blank=True,null=True)
    Lifecycle_stage = models.CharField(max_length=100,blank=True , null=True) 
    Is_Active = models.BooleanField(default=True, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='created_product_master_set', blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updated_product_master_set', blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)

    @property
    def Product_Id(self):
        # Backward-compatibility alias
        return self.Product_Code

    class Meta:
        db_table = 'ProductMaster'
        ordering = ['-id']





def ProductEdition_I():
    last_edition = ProductEdition.objects.order_by('-id').first()

    if not last_edition:
        return 'PED000000001'

    last_id = last_edition.Edition_Id

    try:
        last_number = int(last_id.replace('PED', ''))
    except (ValueError, AttributeError):
        last_number = 0

    new_number = last_number + 1

    return f'PED{new_number:09d}'

class ProductEdition(models.Model):

    Edition_Id = models.CharField(
        max_length=50,
        unique=True,
        default=ProductEdition_I
    )

    Organization_Id = models.ForeignKey(
        Userorganizationmaster,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    Product_Id = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='product_editions'
    )

    Edition_Code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    Edition_Name = models.CharField(
        max_length=250,
        blank=True,
        null=True
    )

    Description = models.TextField(
        blank=True,
        null=True
    )

    Edition_Logo = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    Edition_Icon = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    Is_Active = models.BooleanField(
        default=True,
        blank=True,
        null=True
    )

    Is_Deleted = models.BooleanField(
        default=False,
        blank=True,
        null=True
    )

    Created_By = models.ForeignKey(
        UserAdmin,
        on_delete=models.CASCADE,
        related_name='created_product_edition_set',
        blank=True,
        null=True
    )

    Created_Date = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )

    Updated_By = models.ForeignKey(
        UserAdmin,
        on_delete=models.CASCADE,
        related_name='updated_product_edition_set',
        blank=True,
        null=True
    )

    Updated_Date = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'ProductEdition'
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if not self.Edition_Id:
            self.Edition_Id = ProductEdition_I()
        if not self.Edition_Code:
            self.Edition_Code = self.Edition_Id
        elif not self.Edition_Id:
            self.Edition_Id = self.Edition_Code

        super().save(*args, **kwargs)

    def __str__(self):
        return self.Edition_Name or ''


class Plan(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE,blank=True,null=True)
    Plan_Id = models.CharField(max_length=20,unique=True)
    Product = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, related_name='plans')
    Plan_price=models.JSONField(blank=True,null=True)    ##{Feature price list  "feature name":"whatsapp","price","1000"}
    Plan_per_month = models.BooleanField(default=False,blank=True,null=True)
    Plan_per_year = models.BooleanField(default=False,blank=True,null=True)
    Planmonth_price = models.IntegerField(default=0,blank=True,null=True)
    Planyear_price=models.IntegerField(default=0,blank=True,null=True)
    Description = models.TextField(default='',blank=True,null=True)
    ##--------
    Plan_Name = models.CharField(max_length=50,blank=True,null=True)  ##product Name
    Noofcontacts = models.IntegerField(blank=True,null=True)
    Noofmonths = models.IntegerField(blank=True,null=True)
    Country = models.CharField(max_length=50,blank=True,null=True)
    Plantype = models.CharField(max_length=20,blank=True,null=True)
    Trialperiod = models.IntegerField(blank=True,null=True)
    UnitPrice = models.FloatField(blank=True,null=True)
    Setupfees = models.FloatField(blank=True,null=True)
    Currency_Type = models.CharField(max_length=10,blank=True,null=True)
    No_Of_Users = models.IntegerField(blank=True,null=True)   ##minimun users
    AllocatedStorage = models.IntegerField(blank=True,null=True)  ##storage
    AllocatedAddons = models.ManyToManyField(AddonMaster, blank=True)
    billing_cycle = models.CharField(max_length=20, default='monthly', choices=BILLING_CYCLE_CHOICES, blank=True, null=True)
    Tax = models.CharField(max_length=100, blank=True, null=True)
    TaxPercentage = models.FloatField(default=0, blank=True, null=True)
    TaxAmount = models.FloatField(default=0, blank=True, null=True)
    TotalAmount = models.FloatField(default=0, blank=True, null=True)
    is_limited = models.BooleanField(default=False, blank=True, null=True)
    Is_Active_Flg = models.BooleanField(default=True,blank=True,null=True)
    # Modules = models.ManyToManyField(ModuleMaster, related_name="plans", blank=True) ##commented by kavi on 23 nov
    Is_Deleted = models.BooleanField(default=False,blank=True,null=True)
    Is_Archived = models.BooleanField(default=False,blank=True,null=True)
    ##updated fields
    Max_Leads = models.IntegerField(null=True, blank=True)
    ProductEdition_id = models.ForeignKey(ProductEdition,on_delete=models.CASCADE,related_name='created_productedition')
    ProductEdition_Name = models.CharField(max_length=100,blank=True,null=True)
    Max_account = models.IntegerField(null=True, blank=True)
    Created_By = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_Plan_SA1i',blank=True,null=True)
    Created_Date = models.DateTimeField(default=timezone.now,blank=True,null=True)
    Updated_By = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='updatedplan_SA1i',blank=True,null=True)
    Updated_Date = models.DateTimeField(default=timezone.now,blank=True,null=True)
    # role = models.ForeignKey('authapp.Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='plans')
    menu = models.ManyToManyField('authapp.Menu', blank=True, related_name='menus')

    @property
    def PlanDetails(self):
        # Backward compatibility alias
        return self.Description or ""

    @property
    def Addstorage(self):
        # Backward compatibility alias
        return 0

    class Meta:
        db_table = 'Plan'
        ordering = ['-id']




def ProductFeature_I():
    Task = ProductFeature.objects.all().order_by('id').last()

    if not Task:
        return "PFT" + "000000001"

    Tasking = Task.Feature_Id

    if not Tasking:
        return "PFT" + "000000001"

    try:
        Taski = int(Tasking[3:])
        Tas = Taski + 1
        Configur = "PFT" + str(Tas).zfill(9)
        return Configur
    except Exception:
        import re
        digits = re.findall(r'\d+', str(Tasking))
        if digits:
            Tas = int(digits[-1]) + 1
            return "PFT" + str(Tas).zfill(9)

        return "PFT" + "000000001"


class ProductFeature(models.Model):

    Feature_Id = models.CharField(
        max_length=50,
        unique=True,
        default=ProductFeature_I
    )

    Organization_Id = models.ForeignKey(
        Userorganizationmaster,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    Product_Id = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='product_features',
        blank=True,
        null=True
    )
    ProductCategory_id = models.ForeignKey(ProductCategory , on_delete=models.CASCADE,blank=True,null=True,related_name='product_featurecatname')

    Feature_Code = models.CharField(max_length=100,blank=True,null=True)
    Feature_Name = models.CharField(max_length=250,blank=True,null=True)
    Description = models.TextField(blank=True,null=True)
    Is_Active = models.BooleanField(default=True,blank=True,null=True)
    Is_Deleted = models.BooleanField(default=False,blank=True,null=True)
    Created_By = models.ForeignKey(UserAdmin,on_delete=models.CASCADE,related_name='created_product_feature_set',blank=True,null=True)
    Created_Date = models.DateTimeField(default=timezone.now,blank=True,null=True)
    Updated_By = models.ForeignKey(UserAdmin,on_delete=models.CASCADE,related_name='updated_product_feature_set',blank=True,null=True)
    Updated_Date = models.DateTimeField(default=timezone.now,blank=True,null=True)

    class Meta:
        db_table = 'ProductFeature'
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if not self.Feature_Id:
            self.Feature_Id = ProductFeature_I()

        if not self.Feature_Code:
            self.Feature_Code = self.Feature_Id

        super().save(*args, **kwargs)

    def __str__(self):
        return self.Feature_Name or ''




def PlanFeature_I():
    Task = PlanFeature.objects.all().order_by('id').last()

    if not Task:
        return "PFL" + "000000001"

    Tasking = Task.PlanFeature_Id

    if not Tasking:
        return "PFL" + "000000001"

    try:
        Taski = int(Tasking[3:])
        Tas = Taski + 1
        return "PFL" + str(Tas).zfill(9)

    except Exception:
        import re
        digits = re.findall(r'\d+', str(Tasking))

        if digits:
            return "PFL" + str(int(digits[-1]) + 1).zfill(9)

        return "PFL" + "000000001"


class PlanFeature(models.Model):

    PlanFeature_Id = models.CharField(
        max_length=50,
        unique=True,
        default=PlanFeature_I
    )

    Organization_Id = models.ForeignKey(
        Userorganizationmaster,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    Plan_Id = models.ForeignKey(Plan,
        on_delete=models.CASCADE,
        related_name='plan_features'
    )

    Feature_Id = models.ForeignKey(
        ProductFeature,
        on_delete=models.CASCADE,
        related_name='feature_plans'
    )

    Is_Included = models.BooleanField(
        default=True
    )

    Feature_Price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    Is_Active = models.BooleanField(
        default=True
    )

    Is_Deleted = models.BooleanField(
        default=False
    )

    Created_By = models.ForeignKey(
        UserAdmin,
        on_delete=models.CASCADE,
        related_name='created_plan_feature_set',
        blank=True,
        null=True
    )

    Created_Date = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )

    Updated_By = models.ForeignKey(
        UserAdmin,
        on_delete=models.CASCADE,
        related_name='updated_plan_feature_set',
        blank=True,
        null=True
    )

    Updated_Date = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'PlanFeature'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['Plan_Id', 'Feature_Id'],
                name='unique_feature_per_plan'
            )
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.Plan_Id_id and
            self.Feature_Id_id and
            self.Plan_Id.Product_id != self.Feature_Id.Product_Id_id
        ):
            raise ValidationError(
                "The selected feature must belong to the same product as the plan."
            )

    def save(self, *args, **kwargs):
        if not self.PlanFeature_Id:
            self.PlanFeature_Id = PlanFeature_I()

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.Plan_Id.Plan_Name or '')


def PlanLimit_I():
    Task = PlanLimit.objects.all().order_by('id').last()

    if not Task:
        return "PLM" + "000000001"

    Tasking = Task.PlanLimit_Id

    if not Tasking:
        return "PLM" + "000000001"

    try:
        Taski = int(Tasking[3:])
        Tas = Taski + 1
        return "PLM" + str(Tas).zfill(9)

    except Exception:
        import re
        digits = re.findall(r'\d+', str(Tasking))

        if digits:
            return "PLM" + str(int(digits[-1]) + 1).zfill(9)

        return "PLM" + "000000001"


class PlanLimit(models.Model):

    PlanLimit_Id = models.CharField(
        max_length=50,
        unique=True,
        default=PlanLimit_I
    )

    Organization_Id = models.ForeignKey(
        Userorganizationmaster,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    Plan_Id = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='plan_limits'
    )

    Limit_Name = models.CharField(
        max_length=150
    )

    Limit_Code = models.CharField(
        max_length=100
    )

    Limit_Value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    Unit = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    Is_Unlimited = models.BooleanField(
        default=False
    )

    Is_Active = models.BooleanField(
        default=True
    )

    Is_Deleted = models.BooleanField(
        default=False
    )

    Created_By = models.ForeignKey(
        UserAdmin,
        on_delete=models.CASCADE,
        related_name='created_plan_limit_set',
        blank=True,
        null=True
    )

    Created_Date = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )

    Updated_By = models.ForeignKey(
        UserAdmin,
        on_delete=models.CASCADE,
        related_name='updated_plan_limit_set',
        blank=True,
        null=True
    )

    Updated_Date = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'PlanLimit'
        ordering = ['-id']

        constraints = [
            models.UniqueConstraint(
                fields=['Plan_Id', 'Limit_Code'],
                name='unique_limit_code_per_plan'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.PlanLimit_Id:
            self.PlanLimit_Id = PlanLimit_I()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.Limit_Name or ''


def ProductConfiguration_I():
    Task = ProductConfiguration.objects.all().order_by('id').last()

    if not Task:
        return "PCF" + "000000001"

    Tasking = Task.Configuration_Id

    if not Tasking:
        return "PCF" + "000000001"

    try:
        Taski = int(Tasking[3:])
        Tas = Taski + 1
        return "PCF" + str(Tas).zfill(9)

    except Exception:
        import re
        digits = re.findall(r'\d+', str(Tasking))

        if digits:
            return "PCF" + str(int(digits[-1]) + 1).zfill(9)

        return "PCF" + "000000001"


class ProductConfiguration(models.Model):

    Configuration_Id = models.CharField(
        max_length=50,
        unique=True,
        default=ProductConfiguration_I
    )

    Organization_Id = models.ForeignKey(
        Userorganizationmaster,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    Product_Id = models.ForeignKey(
        ProductMaster,
        on_delete=models.CASCADE,
        related_name='product_configurations'
    )

    General_Settings = models.JSONField(
        default=dict,
        blank=True
    )

    Module_Configuration = models.JSONField(
        default=dict,
        blank=True
    )

    Feature_Controls = models.JSONField(
        default=dict,
        blank=True
    )

    Integrations = models.JSONField(
        default=dict,
        blank=True
    )

    Branding = models.JSONField(
        default=dict,
        blank=True
    )

    Advanced_Settings = models.JSONField(
        default=dict,
        blank=True
    )

    Version = models.PositiveIntegerField(
        default=1
    )

    Configuration_Status = models.CharField(
        max_length=20,
        choices=[
            ('Draft', 'Draft'),
            ('Published', 'Published'),
            ('Archived', 'Archived'),
        ],
        default='Draft'
    )

    Is_Active = models.BooleanField(
        default=True
    )

    Is_Deleted = models.BooleanField(
        default=False
    )

    Created_By = models.ForeignKey(
        UserAdmin,
        on_delete=models.CASCADE,
        related_name='created_product_configuration_set',
        blank=True,
        null=True
    )

    Created_Date = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )

    Updated_By = models.ForeignKey(
        UserAdmin,
        on_delete=models.CASCADE,
        related_name='updated_product_configuration_set',
        blank=True,
        null=True
    )

    Updated_Date = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'ProductConfiguration'
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if not self.Configuration_Id:
            self.Configuration_Id = ProductConfiguration_I()

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.Product_Id.Product_Name or '')



##Table for creation of modulemaster
# class ModuleMaster(models.Model):
#     PRODUCT_CHOICES = [
#         ('education', 'Education'),
#         ('retail', 'Retail'),
#         ('it', 'IT'),]
#     ModuleMasterId = models.CharField(unique=True, max_length=50)
#     Module_key = models.CharField(max_length=50)
#     Module_name = models.CharField(max_length=100)
#     Product = models.CharField(max_length=20, choices=PRODUCT_CHOICES)
#     # optional
#     Route = models.CharField(max_length=100, blank=True)
#     Icon = models.CharField(max_length=50, blank=True)
#     # Self-reference for submenus
#     # Parent_Module = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='submodules')

# # JSON dictionary storing allowed actions and their defaults
#     Permissions = models.JSONField(default=dict, blank=True)
#     Is_active = models.BooleanField(default=True)
#     Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name='CreatedModuleMaster')
#     Created_Date = models.DateTimeField(default=timezone.now())
#     Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UpdatedModuleMaster')
#     Updated_Date = models.DateTimeField(default=timezone.now())
#     Is_Deleted = models.BooleanField(default=False)
#     Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)

#     class Meta:
#         db_table = 'ModuleMaster'

def ModuleMaster_I():
    Task = ModuleMaster.objects.all().order_by('id').last()
    if not Task:
        return "MOD" + "000000001"
    Tasking = Task.ModuleMasterId
    if not Tasking:
        return "MOD" + "000000001"
    try:
        Taski = int(Tasking[3:])
        Tas = Taski + 1
        Configur = "MOD" + str(Tas).zfill(9)
        return Configur
    except Exception:
        import re
        digits = re.findall(r'\d+', str(Tasking))
        if digits:
            Tas = int(digits[-1]) + 1
            return "MOD" + str(Tas).zfill(9)
        return "MOD" + "000000001"


##Table for creation of modulemaster
class ModuleMaster(models.Model):
    ModuleMasterId = models.CharField(unique=True, max_length=50, default=ModuleMaster_I)
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE, blank=True, null=True)
    Module_Code = models.CharField(max_length=100, blank=True, null=True)
    Module_name = models.CharField(max_length=250, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    Module_Type = models.CharField(max_length=100, blank=True, null=True)
    Status = models.CharField(max_length=50, blank=True, null=True, default='Active')

    # Existing compatibility fields
    Module_key = models.CharField(max_length=100, blank=True, null=True)
    ProductCategory_id = models.ForeignKey(ProductCategory , on_delete=models.CASCADE,blank=True,null=True,related_name='product_categoryname')
    Product_Edition_id = models.ManyToManyField(ProductEdition,blank=True)
    ProductFeature_id = models.ManyToManyField(ProductFeature,blank=True)
    ProductCategory = models.CharField(max_length=50, blank=True, null=True)
    Route = models.CharField(max_length=100, blank=True, null=True)
    Icon = models.CharField(max_length=50, blank=True, null=True)
    Is_active = models.BooleanField(default=True, blank=True, null=True)
    Parent_Module = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='submodules')
    Permissions = models.JSONField(default=dict, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False, blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='CreatedModuleMaster', blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UpdatedModuleMaster', blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)

    @property
    def Module_Name(self):
        return self.Module_name

    @Module_Name.setter
    def Module_Name(self, value):
        self.Module_name = value

    class Meta:
        db_table = 'ModuleMaster'
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if not self.ModuleMasterId:
            self.ModuleMasterId = ModuleMaster_I()
        if not self.Module_Code:
            self.Module_Code = self.Module_key or self.ModuleMasterId
        if not self.Module_key:
            self.Module_key = self.Module_Code or self.ModuleMasterId
        if not self.Module_Name:
            self.Module_Name = self.Module_name or ''
        if not self.Module_name:
            self.Module_name = self.Module_Name or ''
        if self.Status and self.Status.lower() == 'active':
            self.Is_active = True
        elif self.Status and self.Status.lower() in ['inactive', 'disabled']:
            self.Is_active = False
        elif self.Is_active is not None and not self.Status:
            self.Status = 'Active' if self.Is_active else 'Inactive'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.Module_Name or self.Module_name or self.ModuleMasterId or ''


class AdditionalUserMaster(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    AdditionalUser_Id = models.CharField(max_length=20, unique=True)
    No_Of_Users = models.IntegerField(default=0)
    Amount_Per_User = models.FloatField(default=0.0, blank=True, null=True)
    Total_Amount = models.FloatField(default=0.0, blank=True, null=True)
    Tax = models.CharField(max_length=100, blank=True, null=True)
    TaxPercentage = models.FloatField(default=0, blank=True, null=True)
    TaxAmount = models.FloatField(default=0, blank=True, null=True)
    Currency_code = models.CharField(max_length=250,blank=True, null=True)
    Country = models.CharField(max_length=100,blank=True, null=True)
    Is_active = models.BooleanField(default=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin,on_delete=models.CASCADE,related_name="created_AdditionalUserMaster",)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin,on_delete=models.CASCADE,related_name="updated_AdditionalUserMaster",)
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "AdditionalUserMaster"
        ordering = ['-id']


class Storagemaster(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Storage_Id = models.CharField(max_length=20)
    Name = models.CharField(max_length=100,blank=True,null=True)
    Price = models.FloatField()
    Tax = models.CharField(max_length=100, blank=True, null=True)
    TaxPercentage = models.FloatField(default=0, blank=True, null=True)
    TaxAmount = models.FloatField(default=0, blank=True, null=True)
    TotalAmount = models.FloatField(default=0, blank=True, null=True)
    Storage_Type = models.CharField(max_length=100,blank=True,null=True)
    Storage_Size = models.IntegerField()
    Country = models.CharField(max_length=100,blank=True,null=True)
    Currency = models.CharField(max_length=100,blank=True,null=True)
    Is_Deleted = models.BooleanField(default=False)
    Is_active = models.BooleanField(default=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='created_Storagemaster_SA1i')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updated_storage_SA1i')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'Storagemaster'
        ordering = ['-id']


class Subscriptions(models.Model):
    STATUS_CHOICES = (
        ("trial", "Trial"),
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    )

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE,blank=True,null=True)
    Subscription_Id = models.CharField(max_length=20,blank=True,null=True)
    Customer_Name=models.CharField(max_length=1000,blank=True,null=True)
    Plan_Name=models.CharField(max_length=1000,blank=True,null=True)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='subscriptions')
    Customer_Id = models.ForeignKey(Account, on_delete=models.CASCADE,blank=True,null=True)
    Plan_Id = models.ForeignKey(Plan, on_delete=models.CASCADE,blank=True,null=True)
    SubscriptionDate = models.DateField(default=timezone.now,blank=True,null=True)
    Base_Users = models.IntegerField(default=0,blank=True,null=True)
    Basestorage_Size = models.IntegerField(default=0,blank=True,null=True)
    UnitPrice = models.FloatField(default=0,blank=True,null=True)
    Subscription_Name=models.CharField(max_length=100,blank=True,null=True)
    SubscriptionPeriod = models.CharField(max_length=30,blank=True,null=True)
    discount=models.FloatField(blank=True,null=True)
    TaxPercentage = models.FloatField(default=0,blank=True,null=True)
    TaxAmount = models.FloatField(default=0,blank=True,null=True)
    Transaction_Type = models.CharField(max_length=10,blank=True,null=True)
    SuscriptionAmount = models.FloatField(default=0,blank=True,null=True)
    Is_Deleted = models.BooleanField(default=False)
    Is_Archived = models.BooleanField(default=False,blank=True,null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,blank=True,null=True)
    previous_subscription = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    start_date = models.DateField(blank=True,null=True)
    end_date = models.DateField(null=True, blank=True)
    is_trial = models.BooleanField(default=False)
    Server_cost = models.FloatField(default=0,blank=True,null=True)
    Operation_cost = models.FloatField(default=0,blank=True,null=True)
    ##New fields
    Additional_users = models.IntegerField(blank=True, null=True)
    Additional_storage = models.IntegerField(blank=True, null=True)
    Additional_Addon = models.CharField(max_length=100,blank=True,null=True)
    AllocatedAddons = models.ManyToManyField(AddonMaster,blank=True)
    Storage_Id=models.ManyToManyField(Storagemaster,blank=True)
    Addtionaluser_Id =models.ManyToManyField(AdditionalUserMaster,blank=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='created_subscription_SA1i')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updated_subscription_SA1i',blank=True,null=True)
    Updated_Date = models.DateTimeField(default=timezone.now)
    ##new fields need to migrate
    Renewal_Date = models.DateField(blank=True, null=True)
    Next_Renewal_Date = models.DateField(blank=True, null=True)
    Last_Payment_Status = models.CharField(max_length=20,blank=True,null=True)
    Auto_Renewal_Flag = models.BooleanField(default=False,blank=True,null=True)
    Subscription_History = models.CharField(max_length=1000,blank=True,null=True)

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table = 'Subscriptions'
        ordering = ['-id']



class Invoice(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Subscription_Id = models.ForeignKey(Subscriptions, on_delete=models.CASCADE, blank=True, null=True)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='invoices')
    Invoice_Id = models.CharField(max_length=20)
    Customer_Id = models.ForeignKey(Account, on_delete=models.CASCADE)
    InvoiceFor = models.CharField(max_length=100,blank=True,null=True)
    Invoice_Code = models.CharField(max_length=250,blank=True,null=True)
    Invoice_Date = models.DateTimeField(default=timezone.now)
    InvoiceAmount = models.FloatField()
    TaxAmount = models.FloatField()
    NetAmount = models.FloatField()
    Is_Archived = models.BooleanField(default=False)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Created_Invoice_SA1i')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Updated_Bysubtransaction_SA1i')
    Updated_Date = models.DateTimeField(default=timezone.now)
    ##new field
    Payment_Status=models.CharField(max_length=1000,blank=True,null=True)
    Is_Combined = models.BooleanField(default=False, blank=True, null=True)
    Subscriptions = models.ManyToManyField(Subscriptions, blank=True, related_name='combined_invoices')
    Products = models.ManyToManyField('ProductMaster', blank=True, related_name='combined_invoices')

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table = 'Invoice'
        ordering = ['-id']


class InvoiceLineItem(models.Model):
    ITEM_TYPE_CHOICES = (
        ('plan', 'Plan'),
        ('addon', 'Addon'),
        ('license', 'License'),
        ('storage', 'Storage'),
        ('other', 'Other'),
    )

    Invoice_Id = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', db_column='Invoice_Id')
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, related_name='invoice_items', db_column='Product_Id')
    Subscription_Id = models.ForeignKey(Subscriptions, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_items', db_column='Subscription_Id')
    Plan_Id = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_items', db_column='Plan_Id')
    Item_Type = models.CharField(max_length=50, default='plan', choices=ITEM_TYPE_CHOICES)
    Description = models.CharField(max_length=500, blank=True, null=True)
    Quantity = models.PositiveIntegerField(default=1)
    UnitPrice = models.FloatField(default=0.0)
    Tax = models.CharField(max_length=100, blank=True, null=True)
    TaxPercentage = models.FloatField(default=0.0)
    TaxAmount = models.FloatField(default=0.0)
    TotalAmount = models.FloatField(default=0.0)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_Date = models.DateTimeField(default=timezone.now)
    Is_Deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'InvoiceLineItem'
        ordering = ['id']

    def __str__(self):
        return f"{self.Invoice_Id.Invoice_Id} - {self.Product_Id.Product_Code if self.Product_Id else ''}: {self.Description}"


class ProformaInvoice(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster,on_delete=models.CASCADE)
    Subscription_Id = models.ForeignKey(Subscriptions,on_delete=models.CASCADE,blank=True,null=True)
    Customer_Id = models.ForeignKey(Account,on_delete=models.CASCADE)
    Invoice_id = models.ForeignKey(Invoice,on_delete=models.CASCADE,blank=True,null=True)
    ProformaInvoice_Date = models.DateTimeField(default=timezone.now)
    ProformaInvoiceAmount = models.FloatField(blank=True,null=True)
    TaxAmount = models.FloatField(blank=True,null=True)
    NetAmount = models.FloatField(blank=True,null=True)
    ProformaInvoice_Status = models.CharField(max_length=100,default="generated",blank=True,null=True)
    Payment_Status = models.CharField(max_length=100,default="pending",blank=True,null=True)
    Email_Sent_Flag = models.BooleanField(default=False)
    Is_Archived = models.BooleanField(default=False)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin,on_delete=models.CASCADE,related_name='created_performance_invoice',blank=True,null=True)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin,on_delete=models.CASCADE,related_name='updated_performance_invoice',blank=True,null=True)
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ProformaInvoice"
        ordering = ['-id']


class Payments(models.Model):

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Subscription_Id = models.ForeignKey(Subscriptions, on_delete=models.CASCADE)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='payments')
    Invoice_Id = models.ForeignKey(Invoice, on_delete=models.CASCADE,blank=True,null=True)
    PerformanceInvoice_id = models.ForeignKey(ProformaInvoice,on_delete=models.CASCADE,blank=True,null=True)
    Payment_Id = models.CharField(max_length=20)
    Payment_Mode=models.CharField(max_length=10000,blank=True,null=True)
    Payment_details=models.CharField(max_length=1000000,blank=True,null=True)
    Transaction_No=models.CharField(max_length=10000,blank=True,null=True)
    Customer_Name=models.CharField(max_length=10000,blank=True,null=True)
    Invoice_Date=models.DateField(default=timezone.now)
    Payment_Date=models.DateField(default=timezone.now)
    Customer_Id = models.ForeignKey(Account, on_delete=models.CASCADE)
    InvoiceFor = models.CharField(max_length=100)
    InvoiceAmount = models.FloatField(default=0)
    TaxAmount = models.FloatField(default=0)
    NetAmount = models.FloatField(default=0)
    grossAmount= models.FloatField(default=0)
    paid_amount= models.FloatField(default=0)
    Is_Archived = models.BooleanField(default=False)
    Is_Deleted = models.BooleanField(default=False)
    status = models.CharField(max_length=20)  # success, failed
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name='created_Bypaymentdetails_SA')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Updated_Bypaymentdetails_SA')
    Updated_Date = models.DateTimeField(default=timezone.now)
    ##new fields
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table = 'Payments'
        ordering = ['-id']



class Renewal(models.Model):
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='created_renewal_SAi1',blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updated_renewal_SAi1',blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now)
    Renewal_Id=models.CharField(max_length=20,unique=True,blank=True)
    old_Subscription_id=models.ForeignKey(Subscriptions,on_delete=models.CASCADE,blank=True, null=True)
    new_Subscription_id=models.ForeignKey(Subscriptions,on_delete=models.CASCADE,related_name='Updatedsubscriptionid',blank=True, null=True)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='renewals')
    Customer_Id = models.ForeignKey(Account,on_delete=models.CASCADE,null=True,blank=True)
    Customer_Name = models.CharField(max_length=100,blank=True)
    Producttype = models.CharField(max_length=1000, blank=True, null=True)
    PlanNetAmount = models.FloatField(blank=True,null= True)
    PlangrossAmount = models.FloatField(blank=True,null= True)
    PlanTaxAmount = models.FloatField(blank=True,null= True)
    Tax = models.CharField(max_length=100, blank=True, null=True)
    TaxPercentage = models.FloatField(default=0, blank=True, null=True)
    TaxAmount = models.FloatField(default=0, blank=True, null=True)
    proformaInvoice_id = models.ForeignKey(ProformaInvoice,on_delete=models.CASCADE,blank=True,null=True)
    proformainvoice_Flag = models.BooleanField(default=False,blank=True,null= True)
    Invoice_id = models.ForeignKey(Invoice,on_delete=models.CASCADE,blank=True,null=True)
    InvoicegenFlag = models.BooleanField(default=False)
    Invoiceemail_Sent_Flag = models.BooleanField(default=False,blank=True,null= True)
    proformaemail_Sent_Flag = models.BooleanField(default=False,blank=True,null= True)
    Requested_By = models.CharField(max_length=100,blank=True, null=True)
    Requestedusers = models.IntegerField(blank=True,null=True)
    status = models.CharField(max_length=100,blank=True,null= True)
    RequestedPlan_Id = models.ForeignKey(Plan,on_delete=models.CASCADE,blank=True,null=True)
    Renewal_Status = models.CharField(max_length=20,default="pending",blank=True,null= True)
    Approved_By = models.ForeignKey(UserAdmin,on_delete=models.CASCADE,null=True,blank=True,related_name="approved_renewals")
    Approved_Date = models.DateTimeField(null=True,blank=True)
    Rejected_Reason = models.TextField(null=True,blank=True)
    Payment_id = models.ForeignKey(Payments,on_delete=models.CASCADE,null=True,blank=True)
    Payment_Status = models.CharField(max_length=20,default="pending",blank=True,null= True)

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table = 'Renewal'
        ordering = ['-id']

class Addsubscriptionrequest(models.Model):
    Addonsubscriptionid= models.CharField(max_length=100,blank=True, null=True)
    Subscription_Id =models.ForeignKey(Subscriptions, on_delete=models.CASCADE)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='addon_subscription_requests')
    addonMasterid =models.ForeignKey(AddonMaster,on_delete=models.CASCADE,blank=True,null=True)  #changed
    Plan_Id =models.ForeignKey(Plan, on_delete=models.CASCADE)
    TenantSubscription_Id = models.IntegerField(default=0,blank=True,null=True)
    Customer_Id = models.ForeignKey(Account,on_delete=models.CASCADE,null=True,blank=True)
    Invoice_Id = models.ForeignKey(Invoice,on_delete=models.CASCADE,null=True,blank=True)
    proformaInvoiceid= models.ForeignKey(ProformaInvoice, on_delete=models.CASCADE,null=True,blank=True)
    Customername = models.CharField(max_length=100,blank=True,null=True)
    Planname = models.CharField(max_length=100,blank=True,null=True)
    RequestDate = models.DateField(default=date.today())
    Requested_By = models.CharField(max_length=100,blank=True, null=True)
    Requestedaddon = models.IntegerField(blank=True,null=True)
    addonPerAmount = models.IntegerField(blank=True,null=True)
    addonTotalAmount = models.IntegerField(blank=True,null=True)
    Tax = models.CharField(max_length=100, blank=True, null=True)
    TaxPercentage = models.FloatField(default=0, blank=True, null=True)
    TaxAmount = models.FloatField(default=0, blank=True, null=True)
    Currency_code = models.CharField(max_length=250,blank=True, null=True)
    Country = models.CharField(max_length=100,blank=True, null=True)
    proformaInvoiceflg = models.BooleanField(default=False)
    Invoiceflg = models.BooleanField(default=False)
    Paymentsflg = models.BooleanField(default=False)
    sync_status = models.CharField(max_length=100,blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UsersubscriptionCreatedBy',blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now())
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UserSubscriptionUpdatedBy',blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now())

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table = 'Addsubscriptionrequest'
        ordering = ['-id']

class Additionallicenserequest(models.Model):
    Subscription_Id =models.ForeignKey(Subscriptions, on_delete=models.CASCADE)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='additional_license_requests')
    userMasterid =models.ForeignKey(AdditionalUserMaster,on_delete=models.CASCADE,blank=True,null=True)  #changed
    Plan_Id =models.ForeignKey(Plan, on_delete=models.CASCADE)
    TenantSubscription_Id = models.IntegerField(default=0,blank=True,null=True)
    Customer_Id = models.ForeignKey(Account,on_delete=models.CASCADE,null=True,blank=True)
    Invoice_Id = models.ForeignKey(Invoice,on_delete=models.CASCADE,null=True,blank=True)
    proformaInvoiceid= models.ForeignKey(ProformaInvoice, on_delete=models.CASCADE,null=True,blank=True)
    Licensereqid = models.CharField(max_length=100,blank=True,null=True)
    Customername = models.CharField(max_length=100,blank=True,null=True)
    Planname = models.CharField(max_length=100,blank=True,null=True)
    RequestDate = models.DateField(default=date.today())
    Requested_By = models.CharField(max_length=100,blank=True, null=True)
    Requestedusers = models.IntegerField(blank=True,null=True)
    UserPerAmount = models.IntegerField(blank=True,null=True)
    UserTotalAmount = models.IntegerField(blank=True,null=True)
    Tax = models.CharField(max_length=100, blank=True, null=True)
    TaxPercentage = models.FloatField(default=0, blank=True, null=True)
    TaxAmount = models.FloatField(default=0, blank=True, null=True)
    Currency_code = models.CharField(max_length=250,blank=True, null=True)
    Country = models.CharField(max_length=100,blank=True, null=True)
    proformaInvoiceflg = models.BooleanField(default=False)
    Invoiceflg = models.BooleanField(default=False)
    Paymentsflg = models.BooleanField(default=False)
    sync_status = models.CharField(max_length=100,blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UserAddorcancellicenseCreatedBy',blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now())
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UserAddorcancellicenseUpdatedBy',blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now())

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table = 'Additionallicenserequest'
        ordering = ['-id']

class Additionalstoragerequest(models.Model):
    AddStorageRequestKey = models.CharField(max_length=100,blank=True,null=True)
    Subscription_Id = models.ForeignKey(Subscriptions, on_delete=models.CASCADE)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='additional_storage_requests')
    storageMasterid = models.ForeignKey(Storagemaster,on_delete=models.CASCADE,null=True,blank=True)
    Plan_Id =models.ForeignKey(Plan, on_delete=models.CASCADE)
    TenantSubscription_Id = models.IntegerField(default=0,blank=True,null=True)
    Customer_Id = models.ForeignKey(Account,on_delete=models.CASCADE,null=True,blank=True)
    Invoice_Id = models.ForeignKey(Invoice,on_delete=models.CASCADE,null=True,blank=True)
    proformaInvoiceid= models.ForeignKey(ProformaInvoice, on_delete=models.CASCADE,null=True,blank=True)
    Customername = models.CharField(max_length=100,blank=True,null=True)
    Planname = models.CharField(max_length=100,blank=True,null=True)
    RequestDate = models.DateField(default=date.today())
    Requested_By = models.CharField(max_length=100,blank=True, null=True)
    Requestedstorage = models.IntegerField(blank=True,null=True)
    storagePerAmount = models.IntegerField(blank=True,null=True)
    storageTotalAmount = models.IntegerField(blank=True,null=True)
    Tax = models.CharField(max_length=100, blank=True, null=True)
    TaxPercentage = models.FloatField(default=0, blank=True, null=True)
    TaxAmount = models.FloatField(default=0, blank=True, null=True)
    Currency_code = models.CharField(max_length=250,blank=True, null=True)
    Country = models.CharField(max_length=100,blank=True, null=True)
    proformaInvoiceflg = models.BooleanField(default=False)
    Invoiceflg = models.BooleanField(default=False)
    Paymentsflg = models.BooleanField(default=False)
    sync_status = models.CharField(max_length=100,blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UseradditionalstorageCreatedBy',blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now())
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UseradditionalstorageupdateddBy',blank=True, null=True)
    Updated_Date = models.DateTimeField(default=timezone.now())

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table = 'Additionalstoragerequest'
        ordering = ['-id']

class Cancelplans(models.Model):
    OrganizationId = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Cancelplan_Id = models.CharField(max_length=20,unique=True)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='cancel_plans')
    Plan_Name=models.CharField(max_length=100,blank=True)
    Domain_Name = models.CharField(max_length=100,blank=True)
    Customer_Name = models.CharField(max_length=100,blank=True)
    NoofUsers = models.IntegerField(blank=True)
    Expiry_Date = models.DateField(default=timezone.now)
    NextRenewal_Date = models.DateField(default=timezone.now)
    Pending_Payment = models.FloatField(blank=True)
    Is_Deleted = models.BooleanField(default=False)
    status = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Cancelplan_CreatedBy_S1iA')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Cancelplan_UpdatedBy_Si1A')
    Updated_Date = models.DateTimeField(default=timezone.now)

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table = 'Cancelplans'
        ordering = ['-id']

class InstanceRequest(models.Model):

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Subscription_Id = models.ForeignKey(Subscriptions, on_delete=models.CASCADE)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='instance_requests')
    Invoice_Id = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    Invoice_No=models.CharField(max_length=1000,null=True)
    RequestId = models.CharField(max_length=20,unique=True)
    SubscriptionId = models.CharField(max_length=30)
    PlanName = models.CharField(max_length=50)
    plan_id=models.ForeignKey(Plan,on_delete=models.CASCADE)
    RequestDate = models.DateField(default=timezone.now)
    UserId = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    CustomerName = models.CharField(max_length=50)
    InstanceName = models.CharField(max_length=50)
    URLName = models.CharField(max_length=250)
    Noofusers = models.IntegerField()
    Paidamount = models.IntegerField()
    InstanceCreatedFlag = models.BooleanField(default=False)
    InstCreatedDate = models.DateField(default=timezone.now)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='created_Instancerequest_SAi1')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updated_Instancerequest_SA1')
    Updated_Date = models.DateTimeField(default=timezone.now)

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table = 'InstanceRequest'
        ordering = ['-id']

class Instance_Creation(models.Model):
    PRODUCT_CHOICES = (
        ("education", "Education CRM"),
        ("retail", "Retail CRM"),
        ("it", "IT CRM"),
    )
    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("suspended", "Suspended"),
    )

    Instance_Request_No = models.CharField(max_length=255, unique=True)
    Customer_Name = models.CharField(max_length=100000)
    Subscription_Id = models.ForeignKey(Subscriptions, on_delete=models.CASCADE,unique=True)
    Product_Id = models.ForeignKey('ProductMaster', on_delete=models.CASCADE, blank=True, null=True, db_column='Product_Id', related_name='instance_creations')
    Tenent_Id=models.IntegerField(default=0)
    product_type = models.CharField(max_length=100, blank=True, null=True)
    Customer_Id = models.ForeignKey(Account, on_delete=models.CASCADE)
    Domain_Name = models.CharField(max_length=1000)  # Increase the max_length value
    Database_Name = models.CharField(max_length=1000)
    Create_Schema = models.CharField(max_length=100,blank=True,null=True)
    Customer_Email= models.CharField(max_length=100,blank=True,null=True)
    Create_Application = models.CharField(max_length=100,blank=True,null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name='Instance_Creation_Created_SAi1')
    Created_Date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="active")
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Instance_Creation_Updated_SAi1')
    Updated_Date = models.DateTimeField(default=timezone.now)
    Is_Deleted = models.BooleanField(default=False)

    @property
    def Product(self):
        return self.Product_Id

    class Meta:
        db_table="Instance_CreationUserAdmin"
        ordering = ['-id']


class WebsiteVistors(models.Model):

    VistorName = models.CharField(max_length=10000)
    VistorEmailID = models.EmailField(max_length=10000000)
    CompanyName = models.CharField(max_length=10000)

    class Meta:
        db_table = 'WebsiteVistors'
        ordering = ['-id']

class UserActivity(models.Model):

    ACTION_CHOICES = (
        ("login", "Login"),
        ("create_lead", "Create Lead"),
        ("view_dashboard", "View Dashboard"),
        ("export_report", "Export Report"),
        ("api_call", "API Call"),
        ("payment","Payment"),
    )

    # 🔥 IMPORTANT CHANGE
    external_user_id = models.CharField(max_length=100)
    instance = models.ForeignKey(Instance_Creation, on_delete=models.CASCADE,blank=True, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["external_user_id"]),
            models.Index(fields=["instance"]),
        ]
##created this model from crmuser

class UserMailConfiguration(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    User_Id = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,unique=True)
    SMTPHost = models.CharField(max_length=250)
    SMTPPort = models.CharField(max_length=25)
    IMAPHost = models.CharField(max_length=250)
    IMAPPort = models.CharField(max_length=25)
    MailId = models.EmailField(unique=True)
    MailPassword = models.CharField(max_length=250)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Usercreateduseremail')
    Created_Date = models.DateTimeField(default=timezone.now())
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='Userupdateuseremail')
    Updated_Date = models.DateTimeField(default=timezone.now())

    class Meta:
        db_table = 'UserMailConfiguration'
        ordering = ['-id']

class AccountMailMaster(models.Model):
    MailId = models.CharField(max_length=25, unique=True)
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    MailConfiguration = models.ForeignKey(UserMailConfiguration, on_delete=models.CASCADE)
    MailSubject = models.CharField(max_length=25000)
    MailBody = models.TextField()
    file=models.CharField(max_length=2500000,null=True)
    Account_Id=models.ForeignKey(Account, on_delete=models.CASCADE)
    RecevierMailId = models.CharField(max_length=250)
    NoofTimesMailOpened = models.IntegerField(default=0)
    NoofTimesMailClicked = models.IntegerField(default=0)
    NoofTimesFileisDownloaded = models.IntegerField(default=0)
    RecevierResponded = models.BooleanField(default=False)
    MailBouned = models.BooleanField(default=False)
    MailReplied = models.BooleanField(default=False)
    MailSentDate = models.DateField(default=date.today())
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='AccountMailCreatedBy')
    Created_Date = models.DateTimeField(default=timezone.now())
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='AccountMailUpdatedBy')
    Updated_Date = models.DateTimeField(default=timezone.now())

    class Meta:
        db_table = 'AccountMailMaster'
        ordering = ['-id']

class AccountNotes(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    AccountNotes_Id=models.CharField(unique=True, max_length=20)
    Subject=models.CharField(max_length=1000,blank=True)
    Account_Id=models.ForeignKey(Account, on_delete=models.CASCADE)
    Notes=models.CharField(max_length=10000)
    Active_Flag=models.BooleanField(default=False)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="updateAccountNotes")
    Updated_Date = models.DateTimeField(default=timezone.now)
    class Meta:
        db_table ='AccountNotes'
        ordering = ['-id']

class AccountAddress(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Address_Id=models.ForeignKey(Useraddress,on_delete=models.CASCADE)
    Account_Id=models.ForeignKey(Account, on_delete=models.CASCADE)
    Active_Flag=models.BooleanField(default=False)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="updateAccountAddress")
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table ='AccountAddress'
        ordering = ['-id']

class AccountCommunication(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Communication_Id=models.CharField(unique=True, max_length=20)  # Need To Discuss
    Account_Id=models.ForeignKey(Account, on_delete=models.CASCADE)
    Active_Flag=models.BooleanField(default=False)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="updateAccountCommunication") # Need To discuss & Change
    Updated_Date = models.DateTimeField(default=timezone.now)
    class Meta:
        db_table ='AccountCommunication'
        ordering = ['-id']

##used this model from crmuser
class Calls(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Call_Id=models.CharField(unique=True, max_length=20)
    Start_DateTime=models.DateTimeField(default=timezone.now)
    End_DateTime=models.DateTimeField(default=timezone.now)
    Duration=models.IntegerField(default=0)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="UpdateCalls")
    Updated_Date = models.DateTimeField(default=timezone.now)
    class Meta:
        db_table ='Calls'
        ordering = ['-id']

class AccountCalls(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Call_Id=models.ForeignKey(Calls, on_delete=models.CASCADE)  # Need To Discuss
    Account_Id=models.ForeignKey(Account, on_delete=models.CASCADE)
    Active_Flag=models.BooleanField(default=False)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="updateAccountCalls") # Need To discuss & Change
    Updated_Date = models.DateTimeField(default=timezone.now)
    class Meta:
        db_table ='AccountCalls'
        ordering = ['-id']

##used this model from crmuser
class UserRemainder(models.Model):
    RemainderDueDate=models.CharField(max_length=10000,blank=True)
    Remainder_Id=models.CharField(unique=True,max_length=100)
    Repeat_EveryDay=models.CharField(max_length=10000,blank=True)
    ReminderFor=models.CharField(max_length=10000,blank=True)
    RemainderMessage=models.CharField(max_length=10000,blank=True)
    Is_Deleted=models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='CreatedUserRemainder')
    Created_Date = models.DateField(default=date.today())
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UpdatedUserRemainder')
    Updated_Date = models.DateField(default=date.today())

    class Meta:
        db_table = "UserRemainder"
        ordering = ['-id']

class AccountMeeting(models.Model):
    Subject=models.CharField(max_length=1000,blank=True)
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    AccountMeeting_Id=models.CharField(unique=True,max_length=100) # Need To Discuss
    Account_Id=models.ForeignKey(Account, on_delete=models.CASCADE)
    FromDate_Time=models.TimeField()
    ToDate_Time=models.TimeField()
    Date=models.DateField(default=date.today())
    Location=models.CharField(max_length=100)
    Venue=models.CharField(max_length=100)
    Details=models.CharField(max_length=100000,blank=True)
    Active_Flag=models.BooleanField(default=False)
    Is_Deleted = models.BooleanField(default=False)
    Reminder_Id=models.ForeignKey(UserRemainder, on_delete=models.CASCADE,blank=True,null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name="updateAccountMeeting") # Need To discuss & Change
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table ='AccountMeeting'
        ordering = ['-id']


class UserFilesandUrls(models.Model):

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    FileID = models.CharField(max_length=250)
    FileName = models.CharField(max_length=250,unique=True)
    File = models.FileField(blank=True)
    Urls = models.CharField(max_length=250,blank=True)
    Description = models.TextField(default='')
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now())
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UserUpdateFileAndUrl')
    Updated_Date = models.DateTimeField(default=timezone.now())

    class Meta:
        db_table ='UserFilesandUrls'
        ordering = ['-id']

##Account overview
class UserNotification(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Notification_Id = models.CharField(max_length=20, unique=True)
    NotificationModule = models.CharField(max_length=100, null=True)
    Notificationname = models.CharField(max_length=5000, null=True)
    NotificationMsg = models.CharField(max_length=50000, null=True)
    Notification_Time = models.DateTimeField(default=timezone.now)
    Is_Deleted = models.BooleanField(default=False)
    Open_flg = models.BooleanField(default=False)
    Created_By = models.ForeignKey(User, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updatednotification')
    Updated_Date = models.DateTimeField(default=timezone.now)
    # Shajitha -> to display the notification to superadmin and the partner
    Partner_Id = models.ForeignKey('partner.Partner',on_delete=models.CASCADE,related_name='PartnerNotifications',blank=True,null=True)
    PartnerTeamMember_Id = models.ForeignKey('partner.PartnerTeamMember',on_delete=models.CASCADE,related_name='PartnerTeamMemberNotifications',blank=True,null=True)


    class Meta:
        db_table = 'UserNotification'
        ordering = ['-id']

class AccountActivities(models.Model):

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    AccountActivities_Id=models.CharField(unique=True,max_length=20)
    Account_Id=models.ForeignKey(Account,on_delete=models.CASCADE)
    Task=models.CharField(max_length=10000)
    Task_Description=models.CharField(max_length=10000)
    Expected_Date=models.DateField(default=date.today())
    Subject=models.CharField(max_length=1000,blank=True)
    Expected_Time=models.TimeField()
    Activity_Type=models.CharField(max_length=100)
    Active_Flag=models.BooleanField(default=False)
    Reminder_Id=models.ForeignKey(UserRemainder, on_delete=models.CASCADE,blank=True,null=True)
    Is_Deleted = models.BooleanField(default=False)
    Default_Date = models.DateTimeField(default=timezone.now)
    Created_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name="AccountActivities")
    Created_Date = models.DateField(default=date.today())
    Updated_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name="UpdatedAccountActivities")
    Updated_Date = models.DateField(default=date.today())

    class Meta:
        db_table ='AccountActivities'
        ordering = ['-id']

class AccountHistory(models.Model):

    Document_Id=models.CharField(max_length=100,blank=True)
    # Record_Id=models.CharField(unique=True, max_length=20,blank=True)
    Module_Name=models.CharField(max_length=100,blank=True)
    Updated_Person=models.CharField(max_length=100,blank=True)
    Updated_Field = models.CharField(max_length=250,blank=True)
    Updated_Time = models.DateTimeField(default=timezone.now())
    Account_Id=models.ForeignKey(Account,on_delete=models.CASCADE)
    Modified_By=models.CharField(max_length=100,blank=True)
    Is_Deleted = models.BooleanField(default=False)
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updatedAccountHistory')
    Updated_Date = models.DateField(default=date.today())

    class Meta:

        db_table = 'AccountHistory'
        ordering = ['-id']

class InboxEmail(models.Model):
    unique_identifier = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=100000)
    Account_Id=models.ForeignKey(Account,on_delete=models.CASCADE,blank=True)
    sender = models.EmailField(max_length=10000000)  # Increase the max_length value
    recipient = models.EmailField(max_length=10000000)  # Increase the max_length value
    body = models.TextField(null=True)
    received_date = models.DateTimeField(null=True)

    class Meta:

        db_table="InboxEmail"
        ordering = ['-id']


from django.db import models
from django.utils import timezone
from datetime import timedelta


class OTPVerification(models.Model):
    email = models.EmailField(db_index=True)
    otp_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "OTPVerification"
        ordering = ['-id']

    def is_expired(self):
        return timezone.now() > self.expires_at


##Ticket and task management
##the below tables are including project and task management

class UserSales(models.Model):

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE,related_name="UserSalesORG")
    Sale_Id=models.CharField(unique=True,max_length=100)
    SalesUser_Id=models.ForeignKey(User, on_delete=models.CASCADE, related_name="updatedSalesUser")
    Po_Number =models.CharField(max_length=10000)
    Po_Date=models.DateField(default=date.today())
    Payment_Terms=models.CharField(max_length=1000000,blank=True,null=True)
    Delivery_Terms=models.CharField(max_length=1000000,blank=True,null=True)
    freight=models.CharField(max_length=10000,blank=True,null=True)
    Account_Id=models.ForeignKey(Account,on_delete=models.CASCADE)
    # Quotation_Id = models.ForeignKey(ProductOffer,on_delete=models.CASCADE)
    Price_Book=models.CharField(max_length=10000,blank=True,null=True)
    Total_Amount=models.FloatField(default=0.0)
    Net_Amount=models.FloatField(default=0.0)
    Sales_Person=models.CharField(max_length=200,blank=True,null=True)
    Note=models.CharField(max_length=10000000,blank=True,null=True)
    # Lead_Id=models.ForeignKey(UserQualifiedLeads, on_delete=models.CASCADE,blank=True,null=True)
    # Deal_Id=models.ForeignKey(Deal, on_delete=models.CASCADE,blank=True,null=True)
    Total_Discount=models.CharField(max_length=10000,blank=True,null=True)
    Customer_Name=models.CharField(max_length=1000)
    SalesOrder_Details=models.JSONField(blank=True,null=True)
    Spl_Discount=models.IntegerField(default=0,blank=True,null=True)
    ScheduledSalesOrder_Details=models.JSONField(blank=True,null=True)
    isSchedule = models.BooleanField(default=False)
    isScheduleClosed = models.BooleanField(default=False)
    Schedule_Status=models.CharField(max_length=1000)
    StatusTrack =models.CharField(max_length=1000,blank=True,null=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(User, on_delete=models.CASCADE,related_name="createdSalesOrder")
    Created_Date = models.DateField(default=date.today())
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE,related_name="updatedSalesOrder")
    Updated_Date = models.DateField(default=date.today())


    class Meta:
        db_table ='UserSales'
        ordering = ['-id']
class Project(models.Model):
    UserSales_Id= models.ForeignKey(UserSales, on_delete = models.CASCADE, blank=True, null=True)
    project_id = models.CharField(unique=True,max_length=255)
    project_name = models.CharField(max_length=255)
    Customer_Name = models.CharField(max_length=255,blank=True,null=True)
    Project_Iniit_No = models.CharField(max_length=255,blank=True,null=True)
    Project_Cost = models.FloatField(default=0.0,blank=True,null=True)
    project_description = models.TextField()
    project_duration = models.CharField(max_length=255)
    project_owner_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    project_owner=models.CharField(max_length=255,blank=True,null=True)
    Status = models.CharField(max_length=255,blank=True,null=True)
    project_estimation_start_date = models.DateTimeField(default=timezone.now)
    project_estimation_end_date = models.DateTimeField(default=timezone.now)
    Is_Deleted=models.BooleanField(default=False)
    Completion_Date = models.DateTimeField(blank=True, null=True)
    Created_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    Created_Date = models.DateTimeField(default=timezone.now())
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_projects')
    Updated_Date = models.DateTimeField(default=timezone.now())
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    class Meta:
        db_table = 'Project'
        ordering = ['-id']

#Task and Ticket Management

def Nonproject_TaskManagement_I():
    Task= Nonproject_TaskManagement.objects.all().order_by('id').last()
    if not Task:
        return "NPT" + "000000001"
    Tasking = Task.Nonproject_TaskManagement_Id
    Taski=int(Tasking[4:])
    Tas= Taski + 1
    Configur = "NPT" + str(Tas).zfill(9)
    return Configur

class Nonproject_TaskManagement(models.Model):
    Nonproject_TaskManagement_Id = models.CharField(max_length=100,blank=True,null=True,unique=True,default=Nonproject_TaskManagement_I)
    Project_Id = models.ForeignKey(Project, on_delete=models.CASCADE,blank=True, null=True)
    Project_Name = models.CharField(max_length=255,blank=True,null=True)
    TASK_STATUS_CHOICES = [('Non-Project', 'Non-Project'),('Project', 'Project')]
    Task_Type = models.CharField(max_length=255, choices=TASK_STATUS_CHOICES, default='Non-Project')
    Task_Name= models.CharField(max_length=255,blank=True,null=True)
    Task_Category= models.CharField(max_length=500,blank=True,null=True)
    Label = models.CharField(max_length=255,blank=True,null=True)
    Sprint = models.CharField(max_length=500,blank=True,null=True)
    Branch = models.CharField(max_length=500,blank=True,null=True)
    Priority = models.CharField(max_length=255,blank=True,null=True)
    Completion_Date = models.DateTimeField(default=timezone.now, blank=True,null=True)
    Closed_Date= models.DateTimeField(default=timezone.now, blank=True,null=True)
    Start_Date= models.DateTimeField(default=timezone.now, blank=True,null=True)
    Closed_Hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    Estimation_Hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    Completion_Hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    Assigned_To = models.ForeignKey(User, on_delete=models.CASCADE,related_name="Assignednametask" ,blank=True,null=True)
    Assigned_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='Assignedbynametask',blank=True,null=True)
    Reviewed_By = models.ForeignKey(User,on_delete=models.CASCADE,related_name='Reviewednametask',blank=True,null=True)
    STATUS_CHOICES = [('New', 'New'),('In Progress', 'In Progress'), ('Pending', 'Pending'), ('Completed', 'Completed')]
    Status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='New')
    # SprintBacklog_Id= models.ForeignKey(SprintBacklog, on_delete=models.CASCADE,blank=True,null=True)
    Severity = models.CharField(max_length=255,blank=True,null=True)
    Environment= models.CharField(max_length=255,blank=True,null=True)
    Steps_To_Reproduce= models.TextField(blank=True, null=True)
    Expected_Result= models.TextField(blank=True, null=True)
    Actual_Result= models.TextField(blank=True, null=True)
    Remarks = models.CharField(max_length=10000,  blank=True, null=True)
    Attachment= models.ManyToManyField(UserFilesandUrls,blank=True,null=True, related_name='task_files_attachments')
    Description = models.TextField(blank=True, null=True)
    Child_Task = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='Parent_task')
    Developer_Action_Flag= models.BooleanField(default=False)
    Assigned_History = models.JSONField(default=dict, blank=True, null= True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True,related_name='CreatedNonproject_TaskManagement')
    Created_Date = models.DateField(default=date.today())
    Updated_By = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True,related_name='UpdatedNonproject_TaskManagement')
    Updated_Date = models.DateField(default=date.today())

    class Meta:
        db_table = "Nonproject_TaskManagement"
        ordering = ['-id']



class TicketManagement(models.Model):

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)  #ITCRM
    Email_UID = models.CharField(max_length=255, blank=True, null=True, unique=True)
    TicketManagement_Id=models.CharField(unique=True,max_length=100)   #ITCRM
    Related_Module=models.CharField(max_length=1000,blank=True,null=True)   #ITCRM- Ticket title
    Mail_Id=models.EmailField(blank=True,null=True)
    STATUS_CHOICES = [('New', 'New'),('Open', 'Open'),('In Progress', 'In Progress'), ('Pending', 'Pending'), ('Testing', 'Testing'),('Fixed', 'Fixed'),('Reopen', 'Reopen')]
    Ticket_Status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='New')   #ITCRM
    Assigned_Person=models.CharField(max_length=1000,blank=True,null=True)    #ITCRM
    PRIORITY_STATUS_CHOICES= [('P0-Critical', 'P0-Critical'), ('P1-High', 'P1-High'), ('P2-Medium', 'P2-Medium'), ('P3-Low', 'P3-Low')]
    Priority=models.CharField(max_length=1000,choices=PRIORITY_STATUS_CHOICES)    #ITCRM
    Name=models.CharField(max_length=1000,blank=True,null=True)
    Order_Number=models.CharField(max_length=1000,blank=True,null=True)
    Remarks=models.CharField(max_length=1000,blank=True,null=True)   #ITCRM
    Completion_Date = models.DateTimeField(default=timezone.now, blank=True,null=True) #added 03-04    #ITCRM
    Start_Date= models.DateTimeField(default=timezone.now, blank=True,null=True)  #added 03-04    #ITCRM
    Estimation_Hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  #added 03-04    #ITCRM
    Completion_Hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  #added 03-04    #ITCRM
    Closed_Hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  #added 03-04    #ITCRM
    Attachment= models.ManyToManyField(UserFilesandUrls,blank=True,null=True, related_name='ticketmanagement_files_attachments')  #added 03-04   #ITCRM
    Due_Date=models.DateField(default=date.today(),blank=True,null=True)
    File=models.FileField(blank=True,null=True)
    Ticket_Description=models.CharField(max_length=100000)    #ITCRM
    Instance=models.CharField(max_length=1000,blank=True,null=True)
    # Type = models.ForeignKey(TicketTypeSupportConfiguration,on_delete=models.CASCADE, null=True, blank=True) # payment ,account,lead
    Type_Name = models.CharField(max_length=100, blank=True, null=True)    #ITCRM
    Category = models.CharField(max_length=250, blank=True, null=True)   #ITCRM
    Ticket_Level = models.CharField(max_length=100, blank=True, null=True)
    Allocated_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Closed_Date = models.DateTimeField(blank=True, null=True)    #ITCRM
    Assigned_History= models.JSONField(default=dict, blank=True, null= True)    #ITCRM
    Assigned_To=models.ForeignKey(User, on_delete=models.CASCADE,related_name="updatedTicketManagement",blank=True,null=True )    #ITCRM
    Is_Deleted = models.BooleanField(default=False)    #ITCRM
    Created_By = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True)   #ITCRM
    Created_Date = models.DateTimeField(default=timezone.now)   #ITCRM
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE,related_name="updatedUserTicketManagement",blank=True,null=True)   #ITCRM
    Updated_Date = models.DateTimeField(default=timezone.now)   #ITCRM
    Partner_Id = models.ForeignKey('partner.Partner', on_delete=models.CASCADE,related_name="PartnerTicketManagement",blank=True,null=True )
    PartnerTeamMember_Id = models.ForeignKey('partner.PartnerTeamMember', on_delete=models.CASCADE,related_name="PartnerTeamMemberTicketManagement",blank=True,null=True )

    class Meta:
        db_table ='TicketManagement'
        ordering = ['-id']







# audit history model
class AuditHistory(models.Model):
    Audit_Id = models.CharField(max_length=64, unique=True, blank=True, null=True)
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.SET_NULL, blank=True, null=True, related_name='audit_organization')
    User_Id = models.ForeignKey(UserAdmin, on_delete=models.SET_NULL, blank=True, null=True, related_name='audit_user')
    Module_Name = models.CharField(max_length=100)
    Table_Name = models.CharField(max_length=100)
    Record_Id = models.CharField(max_length=100)
    Action = models.CharField(max_length=50)
    Old_Data = models.JSONField(blank=True, null=True)
    New_Data = models.JSONField(blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    IP_Address = models.GenericIPAddressField(blank=True, null=True)
    User_Agent = models.CharField(max_length=500, blank=True, null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.SET_NULL, blank=True, null=True, related_name='audit_created_by')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.SET_NULL, blank=True, null=True, related_name='audit_updated_by')
    Updated_Date = models.DateTimeField(blank=True, null=True)
    Action_Status = models.CharField(max_length=50, blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'AuditHistory'
        ordering = ['-id']
        indexes = [
            models.Index(fields=['Table_Name', 'Record_Id']),
            models.Index(fields=['Organization_Id', 'Created_Date']),
            models.Index(fields=['User_Id', 'Created_Date']),
            models.Index(fields=['Is_Deleted']),
        ]

