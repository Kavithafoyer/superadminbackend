from django.db import models
from email.policy import default
from enum import unique
from random import choices
from secrets import choice
from django.utils import timezone
from django.contrib.auth import get_user_model
UserAdmin = get_user_model()
from django.contrib.auth.models import Group,Permission
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import date


def Address_i():
    Address_I = Useraddress.objects.all().order_by('Address_Id').last()
    if not Address_I:
        return 'ADD' + '000000001'
    addres_id = Address_I.Address_Id
    addre_id = int(addres_id[4:])
    addr_id = addre_id + 1
    new_addressid = 'ADD' + str(addr_id).zfill(9)
    return new_addressid


def Address_I():
    Address_I = Communication_Address.objects.all().order_by('Address_Id').last()
    if not Address_I:
        return 'ADD' + '000000001'
    addres_id = Address_I.Address_Id
    addre_id = int(addres_id[4:])
    addr_id = addre_id + 1
    new_addressid = 'ADD' + str(addr_id).zfill(9)
    return new_addressid


def Businesshours_i():
    Businesshours_I = Business_Hours.objects.all().order_by('Businesshours_Id').last()
    if not Businesshours_I:
        return 'BUS' + '000000001'
    addres_id = Businesshours_I.Businesshours_Id
    addre_id = int(addres_id[4:])
    addr_id = addre_id + 1
    new_addressid = 'BUS' + str(addr_id).zfill(9)
    return new_addressid

def Calendar_I():
    Calendar_I = Financial_Calendar_Details.objects.all().order_by('Calendar_Id').last()
    if not Calendar_I:
        return 'CAL' + '000000001'
    addres_id = Calendar_I.Calendar_Id
    addre_id = int(addres_id[4:])
    addr_id = addre_id + 1
    new_addressid = 'CAL' + str(addr_id).zfill(9)
    return new_addressid

def organization_i():
    Organization = Userorganizationmaster.objects.all().order_by('Organization_Id').last()
    if not Organization:
        return 'ORG' + '000000001'
    organizationsid = Organization.Organization_Id
    organizationid_int = int(organizationsid[4:])
    organizationsid_int = organizationid_int + 1
    new_organizationid = 'ORG' + str(organizationsid_int).zfill(9)
    return new_organizationid


def BusinessHours_I():
    Sale_Item_I = CRMBusinessHours.objects.all().order_by('BusinessHours_Id').last()
    if not Sale_Item_I:
        return 'BUS' + '000000001'
    salesit_id = Sale_Item_I.BusinessHours_Id
    sale_id = int(salesit_id[4:])
    sa_id = sale_id + 1
    new_salesid = 'BUS' + str(sa_id).zfill(9)
    return new_salesid


def Company_I():
    Organizatio=Company.objects.all().order_by('Company_Id').last()
    if not Organizatio:
        return "CMP" +"000000001"
    Organizati = Organizatio.Company_Id
    Organizat=int(Organizati[4:])
    Organiza=Organizat + 1
    Configur = "CMP" + str(Organiza).zfill(9)
    return Configur


def RoleI():
    Price_I = Userrole.objects.all().order_by('RoleId').last()
    if not Price_I:
        return 'ROL' + '000000001'
    Price_Id = Price_I.RoleId
    pric_id = int(Price_Id[4:])
    pri_id = pric_id + 1
    pr_id = 'ROL' + str(pri_id).zfill(9)
    return pr_id


def TicketI():
    ticket = Ticket.objects.all().order_by('TktNo').last()
    if not ticket:
        return "TKT" + "000000001"
    ticket_id = int(ticket.TktNo[4:]) + 1
    return str("TKT").upper() + str(ticket_id).zfill(9)

def Ticketresponse_i():
    Ticketresponse=TicketResponse.objects.all().order_by("Ticketresponseid").last()
    if not Ticketresponse:
        return 'RES' + '000000001'
    Ticketrespons =Ticketresponse.Ticketresponseid
    print(Ticketrespons)
    Ticketrespon = int(Ticketrespons[4:])
    Ticketrespo = Ticketrespon + 1
    Ticketresp = 'RES' + str(Ticketrespo).zfill(9)
    return Ticketresp


def UserI():
    Packageplan_Price_I = UserAdmin.objects.all().order_by('User_Id').last()
    if not Packageplan_Price_I:
        return 'USE' + '000000001'
    packageplan = Packageplan_Price_I.User_Id
    packplan_id = int(packageplan[4:])
    packpl = packplan_id + 1
    new_pack = 'USE' + str(packpl).zfill(9)
    return new_pack


def Transactionalseries_i():
    Transactionalseries = TransactionalSeries.objects.all().order_by('Transactionalseriesid').last()
    if not Transactionalseries:
        return 'TRN' + '000000001'
    Transactionalserie = Transactionalseries.Transactionalseriesid
    Transactionalseri = int(Transactionalserie[4:])
    Transactionalser = Transactionalseri + 1
    Transactionalse = 'TRN' + str(Transactionalser).zfill(9)
    return Transactionalse


def NotificationI():
    Domain_Process_Detail_I = Notification.objects.all().order_by('NotificationId').last()
    print(Domain_Process_Detail_I.NotificationId)
    if not Domain_Process_Detail_I:
        return 'NOT' + '000000001'
    domainpro_id = Domain_Process_Detail_I.NotificationId
    domain_id = int(domainpro_id[4:])
    do_id = domain_id + 1
    new_Domain_Process_Id = 'NOT' + str(do_id).zfill(9)
    return new_Domain_Process_Id

def TemplateI():
    Module_Package_I = Template.objects.all().order_by('TemplateId').last()
    if not Module_Package_I:
        return 'TEM' + '000000001'
    Module_Package_Id = Module_Package_I.TemplateId
    module_id = int(Module_Package_Id[4:])
    modu_id = module_id + 1
    new_Module_Package_Id = 'TEM' + str(modu_id).zfill(9)
    return new_Module_Package_Id

def Lookup_i():
    Subscription_I = Userlookup.objects.all().order_by('Lookupid').last()
    if not Subscription_I:
        return 'LOO' + '000000001'
    subscrip_id = Subscription_I.Lookupid
    subscript_id = int(subscrip_id[4:])
    subsc_id = subscript_id + 1
    new_sub = 'LOO' + str(subsc_id).zfill(9)
    return new_sub


def TaskI():
    Tas=Taskuser.objects.all().order_by('TaskId').last()
    if not Tas:
        return 'TAS'+'000000001'
    Task_id=Tas.TaskId
    Tasl_=int(Task_id[4:])
    Tasks=Tasl_+1
    Ta='TAS'+str(Tasks).zfill(9)
    return Ta


# def AddonRequest_I():
#     Tas=AddonRequest.objects.all().order_by('AddonRequest_Id').last()
#     if not Tas:
#         return 'ADR'+'000000001'
#     Task_id=Tas.AddonRequest_Id
#     Tasl_=int(Task_id[4:])
#     Tasks=Tasl_+1
#     Ta='ADR'+str(Tasks).zfill(9)
#     return Ta



# def Licensereq_id():
#     Tas=UserAddorcancellicense.objects.all().order_by('Licensereqid').last()
#     if not Tas:
#         return 'LIC'+'000000001'
#     Task_id=Tas.Licensereqid
#     Tasl_=int(Task_id[4:])
#     Tasks=Tasl_+1
#     Ta='LIC'+str(Tasks).zfill(9)
#     return Ta


# def Cancelplan_I():
#     Tas=Cancelplan.objects.all().order_by('Cancelplan_Id').last()
#     if not Tas:
#         return 'CNL'+'000000001'
#     Task_id=Tas.Cancelplan_Id
#     Tasl_=int(Task_id[4:])
#     Tasks=Tasl_+1
#     Ta='CNL'+str(Tasks).zfill(9)
#     return Ta



# def UserRenewalRequest_I():
#     Tas=UserRenewalRequest.objects.all().order_by('Renewal_Id').last()
#     if not Tas:
#         return 'REN'+'000000001'
#     Task_id=Tas.Renewal_Id
#     Tasl_=int(Task_id[4:])
#     Tasks=Tasl_+1
#     Ta='REN'+str(Tasks).zfill(9)
#     return Ta

# def Role_I():
#     Organizatio=Group.objects.all().order_by('Role_Id').last()
#     if not Organizatio:
#         return "ROL" + "000000001"
#     Organizati = Organizatio.Role_Id
#     Organizat=int(Organizati[4:])
#     Organiza=Organizat + 1
#     Configur = "ROL" + str(Organiza).zfill(9)
#     return Configur

def Formmaster_I():
    Organizatio=FormMaster.objects.all().order_by('FormmasterId').last()
    if not Organizatio:
        return "FMO" + "000000001"
    Organizati = Organizatio.FormmasterId
    Organizat=int(Organizati[4:])
    Organiza=Organizat + 1
    Configur = "FMO" + str(Organiza).zfill(9)
    return Configur

def Form_I():
    Salesorder_I = FormPermission.objects.all().order_by('FormId').last()
    if not Salesorder_I:
        return 'FOR' + '000000001'
    salesord_id = Salesorder_I.FormId
    Sale_Id = int(salesord_id[4:])
    sale_id = Sale_Id + 1
    new_Salesorderid = 'FOR' + str(sale_id).zfill(9)
    return new_Salesorderid

def Module_Id():
    Module_I = CRMModules.objects.all().order_by('ModuleId').last()
    if not Module_I:
        return 'MOD' + '000000001'
    Module_Id = Module_I.ModuleId
    modul_id = int(Module_Id[4:])
    mod_id = modul_id + 1
    new_Module_Id = 'MOD' + str(mod_id).zfill(9)
    return new_Module_Id

def Rolepermission_I():
    Organizatio=RolePermission.objects.all().order_by('Rolepermission_Id').last()
    if not Organizatio:
        return "RPE" + "000000001"
    Organizati = Organizatio.Rolepermission_Id
    Organizat=int(Organizati[4:])
    Organiza=Organizat + 1
    Configur = "RPE" + str(Organiza).zfill(9)
    return Configur

# def Addonsubscription_id():
#     Subscription_Trans_I = Addonsubscription.objects.all().order_by('Addonsubscriptionid').last()
#     if not Subscription_Trans_I:
#         return 'ADS' + '000000001'
#     subscription_id = Subscription_Trans_I.Addonsubscriptionid
#     subscript_id = int(subscription_id[4:])
#     sub_id = subscript_id + 1
#     new_Subscription_Id = 'ADS' + str(sub_id).zfill(9)
#     return new_Subscription_Id

def Attachment_I():
    Attachmen=Imageattachment.objects.all().order_by('Attachment_Id').last()
    if not Attachmen:
        return "ATT" + "000000001"
    Attachme=Attachmen.Attachment_Id
    Attachm = int(Attachme[4:])
    Attach = Attachm + 1
    Attac = "ATT" + str(Attach).zfill(9)
    return Attac


# Note: Dynamic field additions commented out because they are now defined statically in authapp.User
# UserAdmin.add_to_class("Organization_Id", models.IntegerField(default=1,blank=False))
# UserAdmin.add_to_class("UserId", models.CharField(unique=False, max_length=20, default='', blank=True))
# UserAdmin.add_to_class("User_OldPassword", models.CharField(max_length=20, default='', blank=True))
# UserAdmin.add_to_class("Designation", models.CharField(max_length=20, default='', blank=True))
# UserAdmin.add_to_class("User_PwdUpdatedate", models.DateField(default=timezone.now))
# UserAdmin.add_to_class("User_Login_Status", models.BooleanField(default=True, blank=True))
# UserAdmin.add_to_class("Password_Status", models.BooleanField(default=False))
# UserAdmin.add_to_class("Navigate_Status", models.BooleanField(default=False))
# UserAdmin.add_to_class("User_Photo", models.FileField(max_length=100000, default='default.png', blank=True))
# UserAdmin.add_to_class("PhoneNo", models.CharField(max_length=20, default='', blank=True))
# UserAdmin.add_to_class("BuildingHuseNo", models.IntegerField(default=0))
# UserAdmin.add_to_class("Street", models.CharField(max_length=100, default='', blank=True))
# UserAdmin.add_to_class("Area", models.CharField(max_length=100, default='', blank=True))
# UserAdmin.add_to_class("City", models.CharField(max_length=100, default='', blank=True))
# UserAdmin.add_to_class("State", models.CharField(max_length=50, default='', blank=True))
# UserAdmin.add_to_class("Country", models.CharField(max_length=50, default='', blank=True))
# Choice = (("SuperAdmin", "SuperAdmin"), ("Admin", "Admin"), ("User", "User"))
# UserAdmin.add_to_class("UserType", models.CharField(max_length=50, default='Admin'))
# UserAdmin.add_to_class("Url", models.CharField(max_length=1000, default='', blank=True))
# UserAdmin.add_to_class("is_Tenantactive", models.BooleanField(default=True))
# UserAdmin.add_to_class("Roll_Name", models.CharField(max_length=50,blank=True))



class CRMBusinessHours(models.Model):
    BusinessHours_Id = models.CharField(max_length=20, unique=True, default=BusinessHours_I)
    MonChekbox = models.BooleanField(default=True)
    MonStartTime = models.DateTimeField(default=timezone.now)
    MonEndTime = models.DateField(default=timezone.now)
    TueChekbox = models.BooleanField(default=True)
    TueStartTime = models.DateTimeField(default=timezone.now)
    TueEndTime = models.DateField(default=timezone.now)
    WedChekbox = models.BooleanField(default=True)
    WedStartTime = models.DateTimeField(default=timezone.now)
    WedEndTime = models.DateField(default=timezone.now)
    ThuChekbox = models.BooleanField(default=True)
    ThuStartTime = models.DateTimeField(default=timezone.now)
    ThuEndTime = models.DateField(default=timezone.now)
    FriChekbox = models.BooleanField(default=True)
    FriStartTime = models.DateTimeField(default=timezone.now)
    FriEndTime = models.DateField(default=timezone.now)
    SatChekBox = models.BooleanField(default=True)
    SatStartTime = models.DateTimeField(default=timezone.now)
    SatEndTime = models.DateField(default=timezone.now)
    SunChekBox = models.BooleanField(default=True)
    SunStartTime = models.DateTimeField(default=timezone.now)
    SunEndTime = models.DateField(default=timezone.now)
    Is_Deleted = models.BooleanField(default=False)
    # Created_By = models.IntegerField(blank=True,default=1)
    Created_Date = models.DateTimeField(default=timezone.now)
    # Updated_By = models.IntegerField(blank=True,default=1)
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'CRMBusinessHours'


# Create your models here.

class Useraddress(models.Model):
    Address_Id = models.CharField(default=Address_i, max_length=20,unique=True)
    Address_Line1 = models.CharField(max_length=250)
    Address_Line2 = models.CharField(max_length=250)
    Address_Line3 = models.CharField(max_length=250)
    City = models.CharField(max_length=250)
    State = models.CharField(max_length=250)
    Country = models.CharField(max_length=250)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.IntegerField(default=1,blank=True)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.IntegerField(default=1,blank=True)
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'Useraddress'


class UserPermission(models.Model):
    PermissionId = models.CharField(max_length=25)
    PermissionFor = models.CharField(max_length=50)
    PermissionName = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'UserPermission'


# Forms Model
class UserForms(models.Model):
    FormId = models.CharField(max_length=25)
    FormName = models.CharField(max_length=50, unique=True)
    FormFor = models.CharField(max_length=50)
    Permissions = models.ManyToManyField(UserPermission)

    class Meta:
        db_table = 'UserForms'


# Module ModelF
class UserModules(models.Model):
    ModuleId = models.CharField(max_length=25)
    ModuleName = models.CharField(max_length=50, unique=True)
    ModueFor = models.CharField(max_length=50)
    Forms = models.ManyToManyField(UserForms)

    class Meta:
        db_table = 'UserModules'



class Userrole(models.Model):
    Organization_Id = models.IntegerField()
    RoleId = models.CharField(default=RoleI, max_length=20, blank=True)
    Rolename = models.CharField(max_length=100)
    Description = models.CharField(max_length=1000, blank=True)
    ModulePermissions = models.ManyToManyField(UserModules,blank=True)
    FormPermissions = models.ManyToManyField(UserForms,blank=True)
    Permission = models.ManyToManyField(UserPermission,blank=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.CharField(max_length=100)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.CharField(max_length=100)
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'Userrole'



class CRMUsers(models.Model):
    Organization_Id=models.IntegerField()    
    UserId=models.CharField(default=UserI,unique=True,max_length=20)
    RoleId=models.ForeignKey(Userrole,on_delete=models.CASCADE)
    # ProfileId=models.ForeignKey(Profile,on_delete=models.CASCADE)
    User_Name=models.CharField(max_length=50)
    User_emailId=models.CharField(max_length=50,unique=True)
    User_Password=models.CharField(max_length=1000,unique=True)
    User_OldPassword=models.CharField(max_length=1000)
    User_PwdUpdatedate=models.DateField(default=timezone.now)
    User_Login_Status=models.BooleanField(default=True)
    User_Photo=models.FileField(default='default.png',blank=True)
    PhoneNo=models.CharField(max_length=20)
    BuildingHuseNo=models.IntegerField()
    Street=models.CharField(max_length=100)
    Area=models.CharField(max_length=100)
    City=models.CharField(max_length=100)
    State=models.CharField(max_length=50)
    Country=models.CharField(max_length=50)
    Is_Deleted = models.BooleanField(default=False)
    Is_Archived = models.BooleanField(default=False)
    Created_By = models.IntegerField(default=1,blank=True,null=True)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.IntegerField(default=1,blank=True,null=True)
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table='CRMUsers'


class Communication_Address(models.Model):

    Address_Id=models.CharField(max_length=20,unique=True,default=Address_I)#
    # Organisation_Id=models.ForeignKey(Organization, on_delete=models.CASCADE)#
    Address_Type=models.CharField(max_length=100,blank=True)
    Building_Name=models.CharField(max_length=200,blank=True)
    Building_Street=models.CharField(max_length=200,blank=True)
    Building_Area=models.CharField(max_length=200,blank=True)
    Building_City=models.CharField(max_length=200,blank=True)
    Building_State=models.CharField(max_length=50,blank=True)
    Building_Country=models.CharField(max_length=50,blank=True)
    Zip_Code=models.CharField(max_length=50,blank=True)#
    Active_Status=models.BooleanField(default=True)#
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.IntegerField(blank=True,default=1)
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.IntegerField(blank=True,default=1)
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'Communication_Address'

class Financial_Calendar_Details(models.Model):

    #Organization_Id=models.ForeignKey(Organization, on_delete=models.CASCADE)
    Calendar_Id=models.CharField(max_length=20,unique=True,default=Calendar_I)
    Calendar_MonthName=models.CharField(max_length=20,blank=True)#
    CalendarName=models.CharField(max_length=100,blank=True)
    Calender_Year=models.DateField(default=timezone.now)#
    Calandermonth = models.CharField(max_length=50,blank=True)
    Calendar_FinancialYear=models.DateField(default=timezone.now)#
    Calender_QuarterName=models.CharField(max_length=50,blank=True)#
    Calender_MonthFromDate=models.DateField(default=timezone.now)#
    Calendar_From_Date=models.DateField(default=timezone.now)#
    Calendar_To_Date=models.DateField(default=timezone.now)#
    Calender_MonthTodate=models.DateField(default=timezone.now)#
    Calender_MonthClosedFlag=models.DateField(default=timezone.now)#
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.IntegerField(blank=True,default=1)
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.IntegerField(blank=True,default=1)
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'Financial_Calendar_Details'

class Business_Hours(models.Model):
    Businesshours_Id = models.CharField(max_length=20,unique=True,default=Businesshours_i)
    #Organization_Id=models.ForeignKey(Organization, on_delete=models.CASCADE)
    Monday_Chekbox=models.BooleanField(default=False)#
    Monday_Starttime=models.CharField(max_length=20, blank=True)
    Monday_EndTime=models.CharField(max_length=20, blank=True)
    Tuesday_Chekbox=models.BooleanField(default=False)
    Tuesday_Starttime=models.CharField(max_length=20, blank=True)
    Tuesday_Endtime=models.CharField(max_length=20, blank=True)
    Wednessday_Chekbox=models.BooleanField(default=False)
    Wednessday_Starttime=models.CharField(max_length=20, blank=True)
    Wednessday_Endtime=models.CharField(max_length=20, blank=True)
    Thursday_Chekbox=models.BooleanField(default=False)
    Thursday_Starttime=models.CharField(max_length=20, blank=True)
    Thursday_Endtime=models.CharField(max_length=20, blank=True)
    Friday_Chekbox=models.BooleanField(default=False)
    Friday_Starttime=models.CharField(max_length=20, blank=True)
    Friday_Endtime=models.CharField(max_length=20, blank=True)
    Saturday_Chekbox=models.BooleanField(default=False)
    Saturday_Starttime=models.CharField(max_length=20, blank=True)
    Saturday_Endtime=models.CharField(max_length=20, blank=True)
    Sunday_Chekbox=models.BooleanField(default=False)
    Sunday_Starttime=models.CharField(max_length=20, blank=True)
    Sunday_Endtime=models.CharField(max_length=20, blank=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.IntegerField(blank=True,default=1)
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.IntegerField(blank=True,default=1)
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'Business_Hours'


class Userorganizationmaster_BankDetails(models.Model):
    Beneficiary_Account_Name = models.CharField(max_length=100,blank=True, null=True)
    Beneficiary_Account_Number = models.CharField(max_length=100,blank=True, null=True)
    Beneficiary_Bank_Name =  models.CharField(max_length=100,blank=True, null=True)
    IFSC_CODE = models.CharField(max_length=100,blank=True, null=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.IntegerField(blank=True,default=1)
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.IntegerField(blank=True,default=1)
    Updated_Date = models.DateField(default=timezone.now)
    class Meta:
        db_table = 'Userorganizationmaster_BankDetails'


class Userorganizationmaster(models.Model):
    Organization_Id=models.CharField(max_length=20,default=organization_i,unique=True)
    Organization_Name = models.CharField(max_length=100,blank=True)
    Organization_Logo= models.FileField(max_length=100000,blank=True,default="default.png")
    Organization_Mail = models.CharField(max_length=50)
    Organization_Contact_Number=models.JSONField(max_length=10000)
    Organization_Address=models.ForeignKey(Communication_Address,on_delete=models.CASCADE,blank=True,null=True)
    Organization_BankDetails =models.ForeignKey(Userorganizationmaster_BankDetails,on_delete=models.CASCADE,null=True,blank=True)
    Organization_GST = models.CharField(max_length=1000,blank=True,null=True)
    DateFormat = models.CharField(max_length=50,blank=True)
    Is_Deleted = models.BooleanField(default=False)
    Fiscal_Year = models.ForeignKey(Financial_Calendar_Details,on_delete=models.CASCADE,blank=True,null=True)
    Business_Hour = models.ForeignKey(Business_Hours,on_delete=models.CASCADE)
    Updated_Date = models.DateField(default=timezone.now)
    Updated_By = models.IntegerField(blank=True,default=1)
    Created_Date = models.DateField(default=timezone.now)
    Created_By = models.IntegerField(blank=True,default=1)
    Currencies = models.CharField(max_length=50,blank=True)
    class Meta:
        db_table='Userorganizationmaster'
        

class CRMModules(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    # ModuleKey = models.IntegerField(primary_key=True, auto_created=True)
    ModuleId = models.CharField(default=Module_Id, max_length=20, unique=True)
    ModuleName = models.CharField(max_length=100)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedcrmmodules')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'CRMModules'

class CRMForms(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    # FormKey = models.IntegerField(primary_key=True, auto_created=True)
    FormId = models.CharField(default=Form_I, max_length=20, unique=True)
    ModuleId = models.ForeignKey(CRMModules, on_delete=models.CASCADE)
    FormName = models.CharField(max_length=100)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedforms')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'CRMForms'

class Role(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE,default=1)
    #Organization_Id=models.ForeignKey(Organization, on_delete=models.CASCADE)# need to clarify
    Role_Id=models.CharField(max_length=20)# need to clarify
    Role_Name=models.CharField(max_length=50,blank=True)
    Role_Description=models.CharField(max_length=500,blank=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='createdRole')
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedRole')
    Updated_Date = models.DateField(default=timezone.now)
    Is_Deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'Role'

class RolePermission(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE,blank=True,null=True)
    Rolepermission_Id=models.CharField(max_length=20,unique=True,default=Rolepermission_I)
    Code = models.CharField(max_length=250,db_index=True,blank=True,null=True)
    App_Label = models.CharField(max_length=100, blank=True, null=True) # Ticket / Defect
    Model_Name= models.CharField(max_length=100,blank=True,null=True)  # Ticket / Defect
    StatusChoice = [('Create', 'Create'), ('View', 'View'), ('Edit', 'Edit'), ('Delete', 'Delete'), ('Import', 'Import'), ('Export', 'Export'),('Approve', 'Approve'), ('Qualify', 'Qualify'), ('Alllist', 'Alllist')]
    Action = models.CharField(max_length=50,blank=True,null=True, choices=StatusChoice) # Create/View/Edit/Delete/Attend/AllList
    Description = models.CharField(max_length=255,blank=True,null=True)
    Is_Active = models.BooleanField(default=True)    
    Role_Id=models.ForeignKey(Role, on_delete=models.CASCADE,blank=True,null=True)
    Form_Id=models.ManyToManyField(CRMForms,blank=True)
    Create_Permission=models.CharField(max_length=50,blank=True)#
    Edit_Permission=models.CharField(max_length=50,blank=True)#
    Remove_Permission=models.CharField(max_length=50,blank=True)#
    AllPermission=models.CharField(max_length=50,blank=True)#
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='createdRolePermission')
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedRolePermission')
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'RolePermission'

#   "Code": "Module.Screen.Action",
#   "App_Label": "Module",
#   "Model_Name": "Screen",
#   "Action": "View"
# }

class FormPermission(models.Model):
   
    FormId = models.CharField(default=Form_I, max_length=20, unique=True)
    Field_Name = models.JSONField(default=dict,blank=True)
    ModuleName = models.CharField(max_length=100,blank=True)
    FormName = models.CharField(max_length=100,blank=True)
    PermissionName = models.JSONField(blank=True, default=dict)
    ModulePermission = models.ManyToManyField(Permission)
    AllPermission = models.BooleanField(default=False)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedpermision')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'FormPermission'


class FormMaster(models.Model):
    FormmasterId = models.CharField(default=Formmaster_I, max_length=20, unique=True)
    ModuleName = models.CharField(max_length=100,blank=True)
    FormId= models.ManyToManyField(FormPermission)
    Is_Deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'FormMaster'

Group.add_to_class("RolePermissions", models.ManyToManyField(RolePermission,blank=True))
Group.add_to_class("FormPermissions",models.ManyToManyField(CRMForms,blank=True))
# Group.add_to_class("Organization_Id", models.ForeignKey(Organization, on_delete=models.CASCADE,blank=True))
Group.add_to_class("Role_Id", models.CharField(unique=True, max_length=20, blank=True))
Group.add_to_class("Role_Name",models.CharField(max_length=50,blank=True))
Group.add_to_class("Description", models.CharField(max_length=1000, blank=True))
Group.add_to_class('Is_Deleted', models.BooleanField(default=False))
Group.add_to_class('Created_By', models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='createdGroupPermission', default=1))
Group.add_to_class('Updated_By',models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedGroupPermission', default=1))
Group.add_to_class("Created_Date",models.DateField(default=timezone.now))
Group.add_to_class("Updated_Date",models.DateField(default=timezone.now))
Group.add_to_class("FormNames",models.ManyToManyField(FormPermission,blank=True))
Group.add_to_class("Modelname",models.ManyToManyField(FormMaster,blank=True))


class UserAdminMailConfiguration(models.Model):
    
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    User_Id = models.OneToOneField(UserAdmin, on_delete=models.CASCADE)
    SMTPHost = models.CharField(max_length=250)
    SMTPPort = models.CharField(max_length=25)
    IMAPHost = models.CharField(max_length=250)
    IMAPPort = models.CharField(max_length=25)
    MailId = models.EmailField()
    MailPassword = models.CharField(max_length=250)
    Created_By = models.ForeignKey(UserAdmin,on_delete=models.CASCADE, related_name='createdMailConfiguration')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin,on_delete=models.CASCADE, related_name='updateMailConfiguration')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'UserAdminMailConfiguration'


class UserAdminMailMaster(models.Model):
    MailId = models.CharField(max_length=25, unique=True)
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    MailConfiguration = models.ForeignKey(UserAdminMailConfiguration, on_delete=models.CASCADE)
    MailSubject = models.CharField(max_length=25000)
    MailBody = models.TextField()
    file=models.CharField(max_length=2500000,null=True)
    RecevierMailId = models.CharField(max_length=250)
    NoofTimesMailOpened = models.IntegerField(default=0)
    NoofTimesMailClicked = models.IntegerField(default=0)
    NoofTimesFileisDownloaded = models.IntegerField(default=0)
    RecevierResponded = models.BooleanField(default=False)
    MailBouned = models.BooleanField(default=False)
    MailReplied = models.BooleanField(default=False)
    MailSentDate = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'UserAdminMailMaster'


class Company(models.Model):
    Organization_Id=models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Company_Id=models.CharField(max_length=20,default=Company_I,unique=True)
    Company_Name = models.CharField(max_length=100,blank=True)
    CompanyLogo= models.FileField(max_length=100000,blank=True,default="default.png")
    CompanyMail = models.CharField(max_length=50)
    Building_Name=models.CharField(max_length=200,blank=True)
    Building_Area=models.CharField(max_length=200,blank=True)
    Building_City=models.CharField(max_length=200,blank=True)
    Building_State=models.CharField(max_length=50,blank=True)
    Building_Country=models.CharField(max_length=50,blank=True)
    DateFormat = models.CharField(max_length=50,blank=True)
    ZipCode = models.CharField(max_length=50,blank=True)
    Is_Deleted = models.BooleanField(default=False)
    Fiscal_startmonth = models.CharField(max_length=250,blank=True)
    Display_Basedon= models.CharField(max_length=100)
    Currencies = models.CharField(max_length=250,blank=True)
    Currency_formate = models.CharField(max_length=100,blank=True)
    MonChekbox = models.BooleanField(default=True)
    MonStartTime = models.DateTimeField(default=timezone.now)
    MonEndTime = models.DateField(default=timezone.now)
    TueChekbox = models.BooleanField(default=True)
    TueStartTime = models.DateTimeField(default=timezone.now)
    TueEndTime = models.DateField(default=timezone.now)
    WedChekbox = models.BooleanField(default=True)
    WedStartTime = models.DateTimeField(default=timezone.now)
    WedEndTime = models.DateField(default=timezone.now)
    ThuChekbox = models.BooleanField(default=True)
    ThuStartTime = models.DateTimeField(default=timezone.now)
    ThuEndTime = models.DateField(default=timezone.now)
    FriChekbox = models.BooleanField(default=True)
    FriStartTime = models.DateTimeField(default=timezone.now)
    FriEndTime = models.DateField(default=timezone.now)
    SatChekBox = models.BooleanField(default=True)
    SatStartTime = models.DateTimeField(default=timezone.now)
    SatEndTime = models.DateField(default=timezone.now)
    SunChekBox = models.BooleanField(default=True)
    SunStartTime = models.DateTimeField(default=timezone.now)
    SunEndTime = models.DateField(default=timezone.now)
    # Business_Hour = models.ForeignKey(CRMBusinessHours,on_delete=models.CASCADE)
    Updated_Date = models.DateField(default=timezone.now)
    Updated_By = models.IntegerField(blank=True,default=1)
    Created_Date = models.DateField(default=timezone.now)
    Created_By = models.IntegerField(blank=True,default=1)

    class Meta:
        db_table='Company'





class TicketGroups(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    TicketGroupId = models.CharField(max_length=50)
    TicketGroupName = models.CharField(max_length=50)
    GroupUsers = models.ManyToManyField(CRMUsers)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='TicketGroupCreated')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='TicketGroupUpdated')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "TicketGroups"


# class Ticket(models.Model):
#     Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE,blank=True)
#     TktNo = models.CharField(max_length=20, default=TicketI,unique=True)
#     TicketGroup = models.ForeignKey(TicketGroups, on_delete=models.CASCADE, blank=True, null=True)
#     OrganizationId = models.CharField(max_length=20,default='1')
#     TktType = models.CharField(max_length=250,blank=True)
#     TkyCategory = models.CharField(max_length=250,blank=True)
#     TktLevel = models.CharField(max_length=250,blank=True)
#     Name = models.CharField(max_length=250,blank=True)
#     AllowcatedDate = models.DateTimeField(default=timezone.now)
#     DeadlineDate = models.DateTimeField(default=timezone.now)
#     Status = models.CharField(max_length=250,blank=True)
#     AssignTo_Users=models.JSONField(blank=True,null=True)
#     AssignTo = models.ForeignKey(UserAdmin,on_delete=models.CASCADE,related_name='ticketasign')
#     Description = models.TextField(blank=True)
#     Progress = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
#     AdditionalDetails = models.JSONField(blank=True)
#     Is_Deleted = models.BooleanField(default=False)
#     Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='TicketsCreatedBy')
#     Created_Date = models.DateTimeField(default=timezone.now)
#     Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='TicketsUpdatedBy')
#     Updated_Date = models.DateTimeField(default=timezone.now)

#     class Meta:
#         db_table = 'Ticket'


# class TicketResponse(models.Model):
#     Ticketresponseid = models.CharField(default=Ticketresponse_i,max_length=20,unique=True)
#     Ticketid = models.ForeignKey(Ticket,on_delete=models.CASCADE)
#     TicketCreatedDate=models.DateField(default=timezone.now)
#     TicketResponseDetailsCustomer = models.CharField(max_length=250)
#     TicketResponseDateTime = models.DateField(default=timezone.now)
#     Response_By=models.CharField(max_length=100,blank=True)
#     Is_Deleted = models.BooleanField(default=False)
#     Created_Date = models.DateField(default=timezone.now)
#     Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
#     Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='TicketUpdatedBy')
#     Updated_Date = models.DateTimeField(default=timezone.now)

#     class Meta:
#         db_table = 'TicketResponse'


# class TransactionalSeries(models.Model):
#     Transactionalseriesid = models.CharField(default=Transactionalseries_i,max_length=20,unique=True)
#     Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
#     AttributeId = models.CharField(max_length=50)
#     Prefix = models.CharField(max_length=20)
#     StartNo = models.CharField(max_length=20)
#     Is_Deleted = models.BooleanField(default=False)
#     Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
#     Created_Date = models.DateField(default=timezone.now)
#     Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedtransactionalseriess')
#     Updated_Date = models.DateField(default=timezone.now)


#     class Meta:
#         db_table = 'TransactionalSeries'


class Template(models.Model):
    TemplateId = models.CharField(default=TemplateI, unique=True, max_length=20)
    TemplateName = models.CharField(max_length=100)
    TemplateRelatesTo = models.CharField(max_length=500)
    Fieldsused = models.JSONField()
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedtemplate')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'Template'



class Notification(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    NotificationId = models.CharField(default=NotificationI, max_length=20, unique=True)
    TemplateId = models.ForeignKey(Template,on_delete=models.CASCADE,blank=True)
    Notificationname = models.CharField(max_length=50)
    NotificationMsg = models.CharField(max_length=500)
    Catagory=[('Contact','Contact'),('Deal','Deal'),('Lead','Lead'),('Accounts','Accounts')]
    Notificationcatagory = models.CharField(choices=Catagory,max_length=50)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatednotifications')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'Notification'


class Userlookup(models.Model):
    Lookupid=models.CharField(default=Lookup_i,max_length=20,unique=True)
    Lookupname = models.CharField(max_length=250,blank=True)
    Values = models.JSONField()
    Defaultvalue = models.CharField(max_length=250,blank=True)
    Purpose = models.CharField(max_length=250,blank=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='userlookupCreatedBy')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='userlookupUpdatedBy')
    Updated_Date = models.DateTimeField(default=timezone.now)
    class Meta:
        db_table = 'Userlookup'


class Taskuser(models.Model):
    TaskId = models.CharField(max_length=20,default=TaskI)
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    TaskType = models.CharField(max_length=250,blank=True)
    Name = models.CharField(max_length=250,blank=True)
    AllowcatedDate = models.DateTimeField(default=timezone.now)
    DeadlineDate = models.DateTimeField(default=timezone.now)
    Status = models.CharField(max_length=250,blank=True)
    AssignTo = models.ManyToManyField(UserAdmin,blank=True)
    Description = models.TextField(blank=True)
    Progress = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    AdditionalDetails = models.JSONField(default=dict)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='TaskuserCreatedBy')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='TaskuserUpdatedBy')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table ='Taskuser'



class CRMUserTemplate(models.Model):
    
    UserTemplate_Id = models.CharField(max_length=20, unique=True)
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    subject=models.CharField(max_length=5000,null=True)
    Template_Content = models.CharField(max_length=5000,null=True)
    Template_Name=models.CharField(max_length=1000,null=True)
    Template_Type = models.CharField(max_length=1000,null=True)
    Is_Deleted = models.BooleanField(default=False)
    Open_flg = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedUserTemplate')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'CRMUserTemplate'

class CRMUserAutoResponse(models.Model):

    AutoResponse_Id = models.CharField(max_length=20, unique=True)
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    AutoResponse=models.BooleanField(default=True)
    Response_Name = models.CharField(max_length=5000,null=True)
    Record_Type=models.CharField(max_length=1000,null=True)
    Applied_To= models.CharField(max_length=1000,null=True)
    Type=models.CharField(max_length=1000,unique=True)
    No_Of_Days_After=models.CharField(max_length=1000,null=True)
    No_End_Date=models.CharField(max_length=1000,null=True)
    Recur_EveryDay=models.CharField(max_length=1000,null=True)
    Recur_EveryDays=models.CharField(max_length=1000,null=True)
    Folloup_Scheduler=models.JSONField(default=dict,null=True)
    Start_Date=models.DateTimeField(default=timezone.now)
    End_Date=models.DateTimeField(default=timezone.now)
    Template_Id=models.ManyToManyField(CRMUserTemplate)
    Is_Deleted = models.BooleanField(default=False)
    Open_flg = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedCRMUserAutoResponse')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'CRMUserAutoResponse'


# Lead Scoring Models

class UserAdminPredictionQuestions(models.Model):
    ScoreRange = models.JSONField()
    # statuschoice = [('Cool', 'Cool'), ('Warm', 'Warm'), ('Hot', 'Hot')]
    prediction = models.CharField(max_length=30)
    Recommended_Action=models.CharField(max_length=100000)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='predictionQuestion')
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'UserAdminPredictionQuestions'

class UserAdminStatusQuestions(models.Model):
    ScoreRange = models.JSONField()
    # statuschoice = [('Cool', 'Cool'), ('Warm', 'Warm'), ('Hot', 'Hot')]
    Status = models.CharField(max_length=30)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='statusQuestion')
    Updated_Date = models.DateField(default=timezone.now)
    class Meta:
        db_table = 'UserAdminStatusQuestions'


class UserAdminScoreQuestions(models.Model):
    Question = models.JSONField()
    score = models.IntegerField(default=0)
    Logical_Value=models.CharField(max_length=100,blank=True)
    Value=models.CharField(max_length=100,blank=True)
    Operation=models.CharField(max_length=100,blank=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UserAdminupdatedscore')
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'UserAdminScoreQuestions'

#  System Preference For Date Format

class SystemPreference(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE,blank=True, null=True)
    DateFormat = models.CharField(max_length=100,blank=True, null=True) # Stores date format
    Password = models.CharField(max_length=30,blank=True, null=True)  # Stores default or policy password
    ResetPassword = models.BooleanField(default=False) # If True, admin can reset user passwords
    ForcePasswordChange = models.BooleanField(default=False)  # If True, user must change password on next login
    PasswordExpiryDays = models.IntegerField(default=90,blank=True, null=True)  # Number of days after which password expires
    LoginValidityType = models.CharField(max_length=100,default='DATE',blank=True, null=True)# Defines whether login is date-based or unlimited
    ValidFrom = models.DateField(null=True, blank=True)
    ValidTo = models.DateField(null=True, blank=True)
    LockAfterFailedAttempts = models.IntegerField(default=3,blank=True, null=True)  # Number of failed login attempts after which account is locked
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='CreatedSystemPreference',blank=True, null=True)
    Created_Date = models.DateField(default=date.today)
    hide_display_negative_sentiment = models.BooleanField(default=False)
    hide_display_inactive_leads = models.BooleanField(default=False)
    hide_display_inactive_users = models.BooleanField(default=False)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UpdatedSystemPreference',blank=True, null=True)
    Updated_Date = models.DateField(default=date.today)
    Is_Deleted = models.BooleanField(default=False)
    class Meta:
        db_table = 'SystemPreference'


# Create Ticket Response

class UserAdminTicketManagement(models.Model):

    TicketRelatesto = models.CharField(max_length=100)
    AssigntoUser = models.JSONField()
    Assignto=models.ManyToManyField(CRMUsers)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name='CreatedTicketManagement')
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UpdatedTicketManagement')
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'UserAdminTicketManagement'

#  Ticket For the Super Admin

class SuperAdminTicketManagement(models.Model):

    TicketRelatesto = models.CharField(max_length=100)
    Ticket_Id=models.CharField(max_length=20,unique=True)
    Details = models.CharField(max_length=1000)
    Severity=models.CharField(max_length=100)
    RisedBy=models.CharField(max_length=100,null=True, blank=True)
    AllowcatedDate = models.DateTimeField(default=timezone.now)
    DeadlineDate = models.DateTimeField(default=timezone.now)
    Status=models.CharField(blank=True,null=True,max_length=100)
    AssignTo=models.JSONField(blank=True,null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name='CreatedSuperAdminTicketManagement')
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UpdatedSuperAdminTicketManagement')
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'SuperAdminTicketManagement'


# class TicketStatus(models.Model):

#     TicketNo=models.CharField(max_length=100)
#     Relatesto = models.CharField(max_length=100)
#     AssigntoUser = models.JSONField()
#     Assignto = models.ManyToManyField(CRMUsers)
#     Allowcated_Date=models.DateField(default=timezone.now)
#     DeadLine_Date=models.DateField(default=timezone.now)
#     Status=models.CharField(max_length=100)
#     Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name='CreatedTicketStatus')
#     Created_Date = models.DateField(default=timezone.now)
#     Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UpdatedTicketStatus')
#     Updated_Date = models.DateField(default=timezone.now)

#     class Meta:
#         db_table = 'TicketStatus'


class UserAdminTaskCalendar(models.Model):

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Task_Id = models.CharField(max_length=20, unique=True)
    Task_Type=models.CharField(max_length=1000)
    Task_Name=models.CharField(max_length=1000)
    Assign_toUsers=models.JSONField(null=True,blank=True)
    Assign_To=models.ForeignKey(UserAdmin, on_delete=models.CASCADE)
    Start_Time=models.TimeField(default=timezone.now)
    End_Time=models.TimeField(default=timezone.now)
    Description=models.CharField(max_length=10000)
    Allocated_Date=models.DateField(default=timezone.now)
    Deadline_Date=models.DateField(default=timezone.now)
    Status=models.CharField(max_length=100,blank=True,null=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name='createdUserAdminTaskCalendar')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedUserAdminTaskCalendar')
    Updated_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'UserAdminTaskCalendar'


class UserAdminTransactionalseries(models.Model):
    Organization_Id = models.ForeignKey(Userorganizationmaster,on_delete=models.CASCADE)
    Transactionalseries_Id=models.CharField(max_length=20,unique=True)
    Transaction_Name = models.CharField(max_length=250,blank=True)
    Start_No=models.JSONField(null=True,blank=True)
    Suffix=models.JSONField(null=True,blank=True)
    Leads = models.CharField(max_length=20,blank=True)
    Deals = models.CharField(max_length=20,blank=True)
    Customer = models.CharField(max_length=20,blank=True)
    License_Request = models.CharField(max_length=20,blank=True)
    Storage_Request = models.CharField(max_length=20,blank=True)
    Addon_Request = models.CharField(max_length=20,blank=True)
    Ticket_No=models.CharField(max_length=20,blank=True)
    User_Id=models.CharField(max_length=20,blank=True)
    Role_Id=models.CharField(max_length=20,blank=True)
    Territery_Id=models.CharField(max_length=20,blank=True)
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='createdUserAdminTransactionalseries')
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedUserAdminTransactionalseries')
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'UserAdminTransactionalseries'

        

# Call Center Target API Creation


class CallcenterTargetList(models.Model):
    
    Month = models.CharField(max_length=100)
    Weekly_Call_Target = models.CharField(max_length=20,blank=True)
    Weekly_Visit_Target= models.CharField(max_length=20,blank=True)
    Caller_Name=models.CharField(max_length=20,blank=True)
    UserId=models.ForeignKey(UserAdmin,on_delete=models.CASCADE,related_name='UserCallcenterTargetList')
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE,related_name='CreatedCallcenterTargetList')
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UpdatedCallcenterTargetList')
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'CallcenterTargetList'
   


class Imageattachment(models.Model):
    Attachment_Id=models.CharField(max_length=20,unique=True,default=Attachment_I)
    Attachfile=models.FileField(blank=True,null=True)
    filename = models.CharField(max_length=500,blank=True)
    Uploadby=models.CharField(max_length=250,blank=True)
    filetype = models.CharField(max_length=100,blank=True)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='createdattachment')
    Created_Date = models.DateField(default=timezone.now)
    class Meta:
        db_table = 'Imageattachment'
        
class InvoiceTemplate(models.Model):
    HeaderTemplate=models.TextField()
    FooterTemplate=models.TextField()
    Is_Deleted = models.BooleanField(default=False)
    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='createdInvoiceTemplate')
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='UpdatedInvoiceTemplate')
    Updated_Date = models.DateField(default=timezone.now)
    class Meta:
        db_table = 'InvoiceTemplate'


# Tranasaction Series

class UserTransactionalseries(models.Model):

    Organization_Id = models.ForeignKey(Userorganizationmaster, on_delete=models.CASCADE)
    Transactionalseries_Id=models.CharField(max_length=20,unique=True)
    # UserAdmin 
    Addon_subscription=models.JSONField(default=dict,blank=True)
    UserAddor_cancellicense=models.JSONField(default=dict,blank=True)
    Lookup_List=models.JSONField(default=dict,blank=True)
    User_AddStorage=models.JSONField(default=dict,blank=True)
    Addon_Request=models.JSONField(default=dict,blank=True)
    Cancel_plan=models.JSONField(default=dict,blank=True)
    UserRenewal_Request=models.JSONField(default=dict,blank=True)
    CRMUser_Template=models.JSONField(default=dict,blank=True)
    CRMUser_AutoResponse=models.JSONField(default=dict,blank=True)
    UserAdminTask_Calendar=models.JSONField(default=dict,blank=True)
    LeadDemo_Graphics=models.JSONField(default=dict,blank=True)
    LeadDemo_Graphics1=models.JSONField(default=dict,blank=True)
    LeadFirmo_Graphics=models.JSONField(default=dict,blank=True)
    LeadPositive_Graphics=models.JSONField(default=dict,blank=True)
    LeadNegative_Graphics=models.JSONField(default=dict,blank=True)
    LeadScore_Values=models.JSONField(default=dict,blank=True)
    LeadScoreValues_Firmo=models.JSONField(default=dict,blank=True)
    LeadScoreValues_positive=models.JSONField(default=dict,blank=True)
    LeadScoreValues_Negative=models.JSONField(default=dict,blank=True)
    #Contact
    Contact = models.JSONField(default=dict,blank=True)
    Contact_Meeting = models.JSONField(default=dict,blank=True)
    Contact_Activities = models.JSONField(default=dict,blank=True)
    Contact_Notes = models.JSONField(default=dict,blank=True)
    UserMail_Master = models.JSONField(default=dict,blank=True)
    Update_records= models.JSONField(default=dict,blank=True)
    # CallcenterActivity
    Callcenter_Activity= models.JSONField(default=dict,blank=True)
    UserContact_List=models.JSONField(default=dict,blank=True)
    UserCallCenter_List=models.JSONField(default=dict,blank=True)
    # UserQualified Leads
    Leads=models.JSONField(default=dict,blank=True)
    UserLead_Meeting=models.JSONField(default=dict,blank=True)
    UserLeadNotes=models.JSONField(default=dict,blank=True)
    UserLeadMail_Master=models.JSONField(default=dict,blank=True)
    UserQualified_Activities=models.JSONField(default=dict,blank=True)
    UserLeadfrom_contacts=models.JSONField(default=dict,blank=True)
    UserLeadfrom_enquiry=models.JSONField(default=dict,blank=True)
    UserLeadfrom_SocialMedia=models.JSONField(default=dict,blank=True)
    UserLeadfrom_Campaign=models.JSONField(default=dict,blank=True)
    UserUpload_Leads=models.JSONField(default=dict,blank=True)
    Lead_Demo=models.JSONField(default=dict,blank=True)
    UserQualifiedLeads_History=models.JSONField(default=dict,blank=True)
    LeadQualify_Questions=models.JSONField(default=dict,blank=True)
    # Account CRUD 
    Account=models.JSONField(default=dict,blank=True)
    Account_Notes=models.JSONField(default=dict,blank=True)
    Account_Meeting=models.JSONField(default=dict,blank=True)
    Account_MailMaster=models.JSONField(default=dict,blank=True)
    Account_Activities=models.JSONField(default=dict,blank=True)
    Account_History=models.JSONField(default=dict,blank=True)
    # Deal CRUD
    Deal=models.JSONField(default=dict,blank=True)
    Deal_Notes=models.JSONField(default=dict,blank=True)
    Deal_Meeting=models.JSONField(default=dict,blank=True)
    Deal_MailMaster=models.JSONField(default=dict,blank=True)
    Deal_Activities=models.JSONField(default=dict,blank=True)
    Deal_History=models.JSONField(default=dict,blank=True)
    # Sales
    Store_Master=models.JSONField(default=dict,blank=True)
    Product_Category=models.JSONField(default=dict,blank=True)
    ProductItem_Group=models.JSONField(default=dict,blank=True)
    SalesProduct_Master=models.JSONField(default=dict,blank=True)
    Supplier=models.JSONField(default=dict,blank=True)
    Product_Catague=models.JSONField(default=dict,blank=True)
    Discount_Setup=models.JSONField(default=dict,blank=True)
    Product_Inward=models.JSONField(default=dict,blank=True)
    Product_ManagePrice=models.JSONField(default=dict,blank=True)
    Product_Enquiry=models.JSONField(default=dict,blank=True)
    Product_Offer=models.JSONField(default=dict,blank=True)
    User_Sales=models.JSONField(default=dict,blank=True)
    Sales_Schedule=models.JSONField(default=dict,blank=True)
    Sales_Shipment=models.JSONField(default=dict,blank=True)
    Sales_Invoice=models.JSONField(default=dict,blank=True)
    Sales_Payment=models.JSONField(default=dict,blank=True)
    Sales_Expense=models.JSONField(default=dict,blank=True)
    # UserGroupChatMaster
    UserGroup_ChatMaster=models.JSONField(default=dict,blank=True)
    # Territory Management 
    Territory_Management=models.JSONField(default=dict,blank=True)
    Sales_Target=models.JSONField(default=dict,blank=True)
    Sales_PersonTarget=models.JSONField(default=dict,blank=True)
    SalesPerson_Performance=models.JSONField(default=dict,blank=True)
   # UserNotification
    Notification_Id=models.JSONField(default=dict,blank=True)
    # Task Managemnt 
    WorkFlow_Rule=models.JSONField(default=dict,blank=True)
   # UserFeedBackTemplate
    UserFeedBack_Template =models.JSONField(default=dict,blank=True)
   # Task Management 
    NewTask_Managemnt =models.JSONField(default=dict,blank=True)
    Social_Campaign=models.JSONField(default=dict,blank=True)

    # Project CRUD
    Project=models.JSONField(default=dict,blank=True)
    Milestone=models.JSONField(default=dict,blank=True)
    Deliverable=models.JSONField(default=dict,blank=True)
    Projecttask=models.JSONField(default=dict,blank=True)
    Resource=models.JSONField(default=dict,blank=True)
    Task=models.JSONField(default=dict,blank=True)
    Assign_Task=models.JSONField(default=dict,blank=True)
    User_Campaign=models.JSONField(default=dict,blank=True)
    Task_Update=models.JSONField(default=dict,blank=True)
    

    # Super Admin Models
    
    Addons=models.JSONField(default=dict,blank=True)
    Plan=models.JSONField(default=dict,blank=True)
    Subscriptions=models.JSONField(default=dict,blank=True)
    Storagemaster=models.JSONField(default=dict,blank=True)
    Invoice=models.JSONField(default=dict,blank=True)
    Payments=models.JSONField(default=dict,blank=True)
    Addonsubscription=models.JSONField(default=dict,blank=True)
    AddStorage=models.JSONField(default=dict,blank=True)
    Renewal=models.JSONField(default=dict,blank=True)
    Cancelplans=models.JSONField(default=dict,blank=True)
    InstanceRequest=models.JSONField(default=dict,blank=True)

    Created_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='createdtransactionsereries')
    Created_Date = models.DateField(default=timezone.now)
    Updated_By = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, related_name='updatedtransactionsereries')
    Updated_Date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'UserTransactionalseries'

from django.contrib.auth import get_user_model
User = get_user_model()

class UserSession(models.Model):

    user = models.ForeignKey(User,on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    logout_time = models.DateTimeField(null=True,blank=True)
    is_logged_in = models.BooleanField(default=True)
    # DEVICE DETAILS
    device_name = models.CharField(max_length=255,null=True,blank=True)
    browser = models.CharField(max_length=255,null=True,blank=True)
    os = models.CharField(max_length=255,null=True,blank=True)
    ip_address = models.CharField(max_length=255,null=True,blank=True)
    location = models.CharField(max_length=255,null=True,blank=True)
    session_id = models.CharField(max_length=255,unique=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"

# pip install pyyaml ua-parser user-agents









 




























