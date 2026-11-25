from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime
import random


def Role_Id_I():
    """Generates sequential Role ID: ROL0001, ROL0002, etc."""
    try:
        last = RoleMaster.objects.all().order_by('id').last()
        if not last or not last.Role_Id:
            return "ROL0001"
        digits = ''.join(filter(str.isdigit, str(last.Role_Id)))
        num = int(digits) + 1 if digits else 1
        return f"ROL{num:04d}"
    except Exception:
        return f"ROL{random.randint(1000, 9999)}"


def Permission_Id_I():
    """Generates sequential Permission ID: PER0001, PER0002, etc."""
    try:
        last = PermissionMaster.objects.all().order_by('id').last()
        if not last or not last.Permission_Id:
            return "PER0001"
        digits = ''.join(filter(str.isdigit, str(last.Permission_Id)))
        num = int(digits) + 1 if digits else 1
        return f"PER{num:04d}"
    except Exception:
        return f"PER{random.randint(1000, 9999)}"


class User(AbstractUser):
    """
    Extends Django's AbstractUser.

    CRITICAL NOTE:
    This model maps to the database table "auth_user" via db_table = "auth_user".
    This is because the "auth_user" table already exists in the system and is
    referenced/used globally across the codebase. By extending AbstractUser and
    specifying db_table = "auth_user", we avoid breaking existing code, queries,
    and foreign key relations that already target the standard Django auth_user table.

    Existing fields inherited from AbstractUser:
    - id
    - username
    - password
    - first_name
    - last_name
    - email
    - is_staff
    - is_active
    - is_superuser
    - last_login
    - date_joined
    """

    Organization_Id = models.IntegerField(default=1, blank=False)
    UserId = models.CharField(unique=False, max_length=20, default='', blank=True)
    User_OldPassword = models.CharField(max_length=20, default='', blank=True)
    Designation = models.CharField(max_length=20, default='', blank=True)
    User_PwdUpdatedate = models.DateField(default=timezone.now)
    User_Login_Status = models.BooleanField(default=True, blank=True)
    Password_Status = models.BooleanField(default=False)
    Navigate_Status = models.BooleanField(default=False)
    User_Photo = models.FileField(max_length=100000, default='default.png', blank=True)
    PhoneNo = models.CharField(max_length=20, default='', blank=True)
    BuildingHuseNo = models.IntegerField(default=0)
    Street = models.CharField(max_length=100, default='', blank=True)
    Area = models.CharField(max_length=100, default='', blank=True)
    City = models.CharField(max_length=100, default='', blank=True)
    State = models.CharField(max_length=50, default='', blank=True)
    Country = models.CharField(max_length=50, default='', blank=True)
    Choice = (("SuperAdmin", "SuperAdmin"), ("Admin", "Admin"), ("User", "User"))
    UserType = models.CharField(max_length=50, default='Admin', choices=Choice)
    Url = models.CharField(max_length=1000, default='', blank=True)
    is_Tenantactive = models.BooleanField(default=True)
    Roll_Name = models.CharField(max_length=50, blank=True)
    # role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    #shajitha
    Partner_Id = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, null=True, blank=True, related_name="Partneruser")


    class Meta:
        db_table = "auth_user"

    def __str__(self):
        return self.username


class RoleMaster(models.Model):
    """
    RoleMaster Table:
    Defines the roles available in each tenant/organization for authorization.
    """
    # SCOPE_CHOICES = (
    #     ("All", "All Records (Enterprise)"),
    #     ("Team", "Team / Territory Records"),
    #     ("Own", "Own Records Only"),
    # )

    Role_Id = models.CharField(max_length=64, unique=True, default=Role_Id_I, db_index=True)
    Organization_Id = models.IntegerField(default=1, db_index=True)
    Role_Name = models.CharField(max_length=100)
    Role_Description = models.TextField(blank=True, null=True)
    # Data_Scope = models.CharField(max_length=50, default='Own', choices=SCOPE_CHOICES)
    Is_System_Role = models.BooleanField(default=False)
    Is_Active = models.BooleanField(default=True, db_index=True)
    Is_Deleted = models.BooleanField(default=False, db_index=True)
    Created_By = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_roles')
    Created_Date = models.DateTimeField(default=timezone.now)
    Updated_By = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_roles')
    Updated_Date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "RoleMaster"
       


class Menu(models.Model):
    """
    Menu Table:
    Defines the hierarchical navigation layout (Modules, Sub Modules, and Forms).
    Supports parent-child nested relations.
    """
    MENU_TYPE_CHOICES = (
        ("module", "Module"),
        ("submodule", "Sub Module"),
        ("form", "Form"),
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100 , db_index=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    menu_type = models.CharField(max_length=50, choices=MENU_TYPE_CHOICES)
    product = models.CharField(max_length=100, blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True)
    route = models.CharField(max_length=255, blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    Is_Deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "menus"
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class PermissionMaster(models.Model):
    """
    PermissionMaster Table:
    System-wide catalog of all controllable modules, screens, and actions.
    """
    ACTION_CHOICES = (
        ("View", "View"),
        ("Create", "Create"),
        ("Edit", "Edit"),
        ("Delete", "Delete"),
        ("Export", "Export"),
        ("Import", "Import"),
        ("Approve", "Approve"),
    )

    Permission_Id = models.CharField(max_length=64, unique=True, default=Permission_Id_I, db_index=True)
    Module_Name = models.CharField(max_length=100, db_index=True)
    Screen_Name = models.CharField(max_length=100, blank=True, null=True)
    Action_Name = models.CharField(max_length=50, choices=ACTION_CHOICES, default='View')
    Permission_Code = models.CharField(max_length=100, unique=True, db_index=True)
    Description = models.CharField(max_length=255, blank=True, null=True)
    Is_Active = models.BooleanField(default=True, db_index=True)
    Created_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "PermissionMaster"
       
class RolePermissionMapping(models.Model):
    """
    RolePermissionMapping Table:
    Maps a Role to its granular permissions across each module/screen.
    Includes quick boolean flags for standard CRUD + Export actions.
    """
    Role_Id = models.ForeignKey(RoleMaster, on_delete=models.CASCADE, related_name='role_permissions')
    Permission_Id = models.ForeignKey(PermissionMaster, on_delete=models.CASCADE, related_name='role_mappings')
    Can_Create = models.BooleanField(default=False)
    Can_View = models.BooleanField(default=False)
    Can_Edit = models.BooleanField(default=False)
    Can_Delete = models.BooleanField(default=False)
    Can_Export = models.BooleanField(default=False)
    Is_Active = models.BooleanField(default=True)
    Created_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "RolePermissionMapping"
        

class UserRoleMapping(models.Model):
    """
    UserRoleMapping Table:
    Supports assigning multiple roles to a user within an organization context.
    """
    User_Id = models.ForeignKey('User', on_delete=models.CASCADE, related_name='user_role_mappings')
    Role_Id = models.ForeignKey(RoleMaster, on_delete=models.CASCADE, related_name='assigned_users')
    Organization_Id = models.IntegerField(default=1, db_index=True)
    Is_Active = models.BooleanField(default=True)
    Created_Date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "UserRoleMapping"
       

