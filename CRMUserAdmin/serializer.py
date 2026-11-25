from rest_framework import serializers
import time

from .models import *



class Userserializer(serializers.ModelSerializer):
    class Meta:
        model = UserAdmin
        fields = '__all__'

class Userserializers(serializers.ModelSerializer):
    class Meta:
        model = UserAdmin
        fields = '__all__'
        depth=1

class UserAdminMailConfigurationSerializer(serializers.ModelSerializer):

    class Meta:
        model=UserAdminMailConfiguration
        fields='__all__'

class UseraddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Useraddress
        fields = '__all__'

class UseraddressSerializers(serializers.ModelSerializer):

    class Meta:
        model = Useraddress
        fields = '__all__'
        depth = 1

class UserroleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Userrole
        fields = '__all__'



class UserroleSerializers(serializers.ModelSerializer):

    class Meta:
        model = Userrole
        fields = '__all__'
        depth = 1



class CRMUsersSerializer(serializers.ModelSerializer):

    class Meta:
        model = CRMUsers
        fields = '__all__'



class CRMUsersSerializers(serializers.ModelSerializer):

    class Meta:
        model = CRMUsers
        fields = '__all__'
        depth = 1


class UserorganizationmasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Userorganizationmaster
        fields = '__all__'

    

class UserorganizationmasterSerializers(serializers.ModelSerializer):

    class Meta:
        model = Userorganizationmaster
        fields = '__all__'
        depth = 1


class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        # model = Ticket
        fields = '__all__'



class TicketSerializers(serializers.ModelSerializer):

    class Meta:
        # model = Ticket
        fields = '__all__'  
        depth = 1    


class TicketResponseSerializer(serializers.ModelSerializer):

    class Meta:
        # model = TicketResponse
        fields = '__all__'


class TicketResponseSerializers(serializers.ModelSerializer):

    class Meta:
        # model = TicketResponse
        fields = '__all__'
        depth = 1


class CRMBusinessHoursSerializer(serializers.ModelSerializer):

    class Meta:
        model = CRMBusinessHours
        fields = '__all__'


class CRMBusinessHoursSerializers(serializers.ModelSerializer):

    class Meta:
        model = CRMBusinessHours
        fields = '__all__'
        depth = 1


class TransactionalSeriesSerializer(serializers.ModelSerializer):

    class Meta:
        # model = TransactionalSeries
        fields = '__all__'


class TransactionalSeriesSerializers(serializers.ModelSerializer):

    class Meta:
        # model = TransactionalSeries
        fields = '__all__'
        depth = 1


class TemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Template
        fields = '__all__'

        

class TemplateSerializers(serializers.ModelSerializer):

    class Meta:
        model = Template
        fields = '__all__'
        depth = 1

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = '__all__'


class NotificationSerializers(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = '__all__'
        depth = 1


class UserlookupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Userlookup
        fields = '__all__'


class UserlookupSerializers(serializers.ModelSerializer):

    class Meta:
        model = Userlookup
        fields = '__all__'
        depth = 1

class NotificationMulti(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'



class TaskuserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Taskuser
        fields = '__all__'


class TaskuserSerializers(serializers.ModelSerializer):

    class Meta:
        model = Taskuser
        fields = '__all__'
        depth = 1


# class UserAddonRequestSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = AddonRequest
#         fields = '__all__'


# class UserAddonRequestSerializers(serializers.ModelSerializer):

#     class Meta:
#         model = AddonRequest
#         fields = '__all__'
#         depth = 1



# class UserAddStorageSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = UserAddStorage
#         fields = '__all__'


# class UserAddStorageSerializers(serializers.ModelSerializer):

#     class Meta:
#         model = UserAddStorage
#         fields = '__all__'
#         depth = 1

# class UserAddorcancellicenseSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = UserAddorcancellicense
#         fields = '__all__'


# class UserAddorcancellicenseSerializers(serializers.ModelSerializer):

#     class Meta:
#         model = UserAddorcancellicense
#         fields = '__all__'
#         depth = 1

# class UserCancelplanSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = Cancelplan
#         fields = '__all__'


# class UserCancelplanSerializers(serializers.ModelSerializer):

#     class Meta:
#         model = Cancelplan
#         fields = '__all__'
#         depth = 1


# class UserRenewalRequestSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserRenewalRequest
#         fields = '__all__'


# class UserRenewalRequestSerializers(serializers.ModelSerializer):
#     class Meta:
#         model = UserRenewalRequest
#         fields = '__all__'
#         depth = 1

class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = '__all__'


class CompanySerializers(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = '__all__'
        depth = 1

class CRMUserTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CRMUserTemplate
        fields = '__all__'


class CRMUserTemplateSerializers(serializers.ModelSerializer):
    class Meta:
        model = CRMUserTemplate
        fields = '__all__'
        depth = 1

class CRMUserAutoResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CRMUserAutoResponse
        fields = '__all__'


class CRMUserAutoResponseSerializers(serializers.ModelSerializer):
    class Meta:
        model = CRMUserAutoResponse
        fields = '__all__'
        depth = 1

 #  Changes In UserAdmin

class Business_HoursSerialzer(serializers.ModelSerializer):
    class Meta:
        model = Business_Hours
        fields = '__all__'

class Business_HoursSerialzers(serializers.ModelSerializer):
    class Meta:
        model = Business_Hours
        fields = '__all__'
        depth = 1

class Communication_AddressSerialzer(serializers.ModelSerializer):
    class Meta:
        model = Communication_Address
        fields = '__all__'

class Financial_Calendar_DetailsSerialzer(serializers.ModelSerializer):
    class Meta:
        model = Financial_Calendar_Details
        fields = '__all__'


class Financial_Calendar_DetailsSerialzers(serializers.ModelSerializer):
    class Meta:
        model = Financial_Calendar_Details
        fields = '__all__'
        depth = 1


class UserAdminPredictionQuestionsSerializer(serializers.ModelSerializer):

    class Meta:
        # model =UserAdminPredictionQuestions
        fields = '__all__'

class UserAdminPredictionQuestionsSerializers(serializers.ModelSerializer):
    
    class Meta:
        # model =UserAdminPredictionQuestions
        fields = '__all__'
        depth = 1

class UserAdminStatusQuestionsSerializer(serializers.ModelSerializer):

    class Meta:
        model =UserAdminStatusQuestions
        fields = '__all__'

class UserAdminStatusQuestionsSerializers(serializers.ModelSerializer):
    
    class Meta:
        model =UserAdminStatusQuestions
        fields = '__all__'
        depth = 1



class UserAdminScoreQuestionsSerializer(serializers.ModelSerializer):

    class Meta:
        model =UserAdminScoreQuestions
        fields = '__all__'

class UserAdminScoreQuestionsSerializers(serializers.ModelSerializer):
    
    class Meta:
        model =UserAdminScoreQuestions
        fields = '__all__'
        depth = 1



class AdminCallActivityQuestionsSerializer(serializers.ModelSerializer):

    class Meta:
        # model =AdminCallActivityQuestions
        fields = '__all__'

class AdminCallActivityQuestionsSerializers(serializers.ModelSerializer):
    
    class Meta:
        # model =AdminCallActivityQuestions
        fields = '__all__'
        depth = 1

class AdminWebActivityQuestionsSerializer(serializers.ModelSerializer):

    class Meta:
        # model =AdminWebActivityQuestions
        fields = '__all__'
        

class AdminWebActivityQuestionsSerializers(serializers.ModelSerializer):
    
    class Meta:
        # model =AdminWebActivityQuestions
        fields = '__all__'
        depth = 1

class AdminMailActivityQuestionsSerializer(serializers.ModelSerializer):

    class Meta:
        # model =AdminMailActivityQuestions
        fields = '__all__'

class AdminMailActivityQuestionsSerializers(serializers.ModelSerializer):
    
    class Meta:
        # model =AdminMailActivityQuestions
        fields = '__all__'
        depth = 1



class UserAdminDealProbabilitySerializer(serializers.ModelSerializer):

    class Meta:
        # model =UserAdminDealProbability
        fields = '__all__'

class UserAdminDealProbabilitySerializers(serializers.ModelSerializer):
    
    class Meta:
        # model =UserAdminDealProbability
        fields = '__all__'
        depth = 1

class UserAdminDealWeightSetupSerializer(serializers.ModelSerializer):

    class Meta:
        # model =UserAdminDealWeightSetup
        fields = '__all__'

class UserAdminDealWeightSetupSerializers(serializers.ModelSerializer):
    
    class Meta:
        # model =UserAdminDealWeightSetup
        fields = '__all__'
        depth = 1

class UserAdminDealFactorSetupSerializer(serializers.ModelSerializer):

    class Meta:
        # model =UserAdminDealFactorSetup
        fields = '__all__'

class UserAdminDealFactorSetupSerializers(serializers.ModelSerializer):
    
    class Meta:
        # model =UserAdminDealFactorSetup
        fields = '__all__'
        depth = 1

class UserAdminDealPredictionSerializer(serializers.ModelSerializer):

    class Meta:
        # model =UserAdminDealPrediction
        fields = '__all__'

class UserAdminDealPredictionSerializers(serializers.ModelSerializer):
    
    class Meta:
        # model =UserAdminDealPrediction
        fields = '__all__'
        depth = 1


class SystemPreferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model =SystemPreference
        fields = '__all__'

class SystemPreferenceSerializers(serializers.ModelSerializer):
    
    class Meta:
        model =SystemPreference
        fields = '__all__'
        depth = 1

class UserAdminTicketManagementSerializer(serializers.ModelSerializer):

    class Meta:
        model =UserAdminTicketManagement
        fields = '__all__'

class UserAdminTicketManagementSerializers(serializers.ModelSerializer):
    
    class Meta:
        model =UserAdminTicketManagement
        fields = '__all__'
        depth = 1

class SuperAdminTicketManagementSerializer(serializers.ModelSerializer):

    class Meta:
        model =SuperAdminTicketManagement
        fields = '__all__'

class SuperAdminTicketManagementSerializers(serializers.ModelSerializer):
    
    class Meta:
        model =SuperAdminTicketManagement
        fields = '__all__'
        depth = 1

class TicketStatusSerializer(serializers.ModelSerializer):

    class Meta:
        # model =TicketStatus
        fields = '__all__'

class TicketStatusSerializers(serializers.ModelSerializer):
    
    class Meta:
        # model =TicketStatus
        fields = '__all__'
        depth = 1



class UserAdminMailMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model =UserAdminMailMaster
        fields = '__all__'

class UserAdminMailMasterSerializers(serializers.ModelSerializer):
    
    class Meta:
        model =UserAdminMailMaster
        fields = '__all__'
        depth = 1

class UserAdminTaskCalendarSerializer(serializers.ModelSerializer):

    class Meta:
        model =UserAdminTaskCalendar
        fields = '__all__'

class UserAdminTaskCalendarSerializers(serializers.ModelSerializer):
    
    class Meta:
        model =UserAdminTaskCalendar
        fields = '__all__'
        depth = 1

class UserAdminTransactionalseriesSerializer(serializers.ModelSerializer):

    class Meta:
        model =UserAdminTransactionalseries
        fields = '__all__'

class UserAdminTransactionalseriesSerializers(serializers.ModelSerializer):
    
    class Meta:
        model =UserAdminTransactionalseries
        fields = '__all__'
        depth = 1

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'
        

class GroupSerializers(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'
        depth = 1

class FormPermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = FormPermission
        fields = "__all__"

class FormPermissionSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = FormPermission
        fields = "__all__"
        depth = 1

class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = "__all__"

class PermissionSerializers(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = "__all__"

class FormMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = FormMaster
        fields = "__all__"

class FormMasterSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = FormMaster
        fields = "__all__"
        depth = 1

class CallcenterTargetListSerializer(serializers.ModelSerializer):

    class Meta:
        model = CallcenterTargetList
        fields = "__all__"

class CallcenterTargetListSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = CallcenterTargetList
        fields = "__all__"
        depth = 1

# class LeadQualificationPercentageSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = LeadQualificationPercentage
#         fields = "__all__"

# class LeadQualificationPercentageSerializers(serializers.ModelSerializer):
    
#     class Meta:
#         model = LeadQualificationPercentage
#         fields = "__all__"
#         depth = 1

# class LeadDemoGraphicsSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = LeadDemoGraphics
#         fields = "__all__"

# class LeadDemoGraphicsSerializers(serializers.ModelSerializer):
    
#     class Meta:
#         model = LeadDemoGraphics
#         fields = "__all__"
#         depth = 1

# class LeadFirmoGraphicsSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = LeadFirmoGraphics
#         fields = "__all__"

# class LeadFirmoGraphicsSerializers(serializers.ModelSerializer):
    
#     class Meta:
#         model = LeadFirmoGraphics
#         fields = "__all__"
#         depth = 1

# class LeadPositiveGraphicsSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = LeadPositiveGraphics
#         fields = "__all__"

# class LeadPositiveGraphicsSerializers(serializers.ModelSerializer):
    
#     class Meta:
#         model = LeadPositiveGraphics
#         fields = "__all__"
#         depth = 1

# class LeadNegativeGraphicsSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = LeadNegativeGraphics
#         fields = "__all__"

# class LeadNegativeGraphicsSerializers(serializers.ModelSerializer):
    
#     class Meta:
#         model = LeadNegativeGraphics
#         fields = "__all__"
#         depth = 1

# class LeadScoreValuesSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = LeadScoreValues
#         fields = "__all__"

# class LeadScoreValuesSerializers(serializers.ModelSerializer):
    
#     class Meta:
#         model = LeadScoreValues
#         fields = "__all__"
#         depth = 1

# class LeadScoreValuesFirmoSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = LeadScoreValuesFirmo
#         fields = "__all__"

# class LeadScoreValuesFirmoSerializers(serializers.ModelSerializer):
    
#     class Meta:
#         model = LeadScoreValuesFirmo
#         fields = "__all__"
#         depth = 1

# class LeadScoreValuespositiveSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = LeadScoreValuespositive
#         fields = "__all__"

# class LeadScoreValuespositiveSerializers(serializers.ModelSerializer):
    
#     class Meta:
#         model = LeadScoreValuespositive
#         fields = "__all__"
#         depth = 1

# class LeadScoreValuesNegativeSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = LeadScoreValuesNegative
#         fields = "__all__"

# class LeadScoreValuesNegativeSerializers(serializers.ModelSerializer):
    
#     class Meta:
#         model = LeadScoreValuesNegative
#         fields = "__all__"
#         depth = 1


# class Subscriptionserializer(serializers.ModelSerializer):
#     class Meta:
#         model = Subscriptions
#         fields = '__all__'
# class Subscriptionserializers(serializers.ModelSerializer):
#     class Meta:
#         model = Subscriptions
#         fields = '__all__'
#         depth = 1
# class Subscriptionfilterserializer(serializers.ModelSerializer):
#     class Meta:
#         model = Subscriptions
#         fields = '__all__'
#         depth = 1
# class Planserializer(serializers.ModelSerializer):
#     class Meta:
#         model = Plan
#         fields = '__all__'
# class Planserializers(serializers.ModelSerializer):
#     class Meta:
#         model = Plan
#         fields = '__all__'
#         depth = 1

# class AddonsubscriptionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Addonsubscription
#         fields = '__all__'
        
# class AddonsubscriptionSerializers(serializers.ModelSerializer):
#     class Meta:
#         model = Addonsubscription
#         fields = '__all__'
#         depth = 1



class ImageattachmentSerialzer(serializers.ModelSerializer):
    class Meta:
        model = Imageattachment
        fields = '__all__'

class ImageattachmentSerialzers(serializers.ModelSerializer):
    class Meta:
        model = Imageattachment
        fields = '__all__'
        depth = 1

class InvoiceTemplateSerialzer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceTemplate
        fields = '__all__'
        
class InvoiceTemplateSerialzers(serializers.ModelSerializer):
    class Meta:
        model = InvoiceTemplate
        fields = '__all__'
        depth = 1


class UserTransactionalseriesSerializer(serializers.ModelSerializer):

    class Meta:
        model= UserTransactionalseries
        fields='__all__'

class UserTransactionalseriesSerializers(serializers.ModelSerializer):

    class Meta:
        model=UserTransactionalseries
        fields='__all__'
        depth =1
        
class Userorganizationmaster_BankDetailsSerializers(serializers.ModelSerializer):
     class Meta:
        model = Userorganizationmaster_BankDetails
        fields = '__all__'
        depth=1
        
class Userorganizationmaster_BankDetailsSerializer(serializers.ModelSerializer):
     class Meta:
        model = Userorganizationmaster_BankDetails
        fields = '__all__'

class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model= RolePermission
        fields = '__all__'


class RolePermissionSerializers(serializers.ModelSerializer):
    class Meta:
        model= RolePermission
        fields = '__all__'
        depth=1


class RolePermission_updateSerializer(serializers.ModelSerializer):
    class Meta:
        model= RolePermission
        fields = ['id', 'Rolepermission_Id', 'Code', 'App_Label', 'Model_Name', 'Action', 'Description', 'Is_Active']


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     def validate(self, attrs):
#         # -----------------------------------
#         # Validate username/password
#         # -----------------------------------
#         data = super().validate(attrs)
#         user = self.user
#         print('user',user)
#         # -----------------------------------
#         # Roles
#         # -----------------------------------
#         roles = []

#         groups = Group.objects.filter(Is_Deleted=False)
#         print('groups',groups)
#         for group in groups:
#             userdata = UserAdmin.objects.get(username=user)
#             if group.name == userdata.Designation:
#                 roles.append({
#                     "id": group.id,
#                     "name": group.name
#                 })
#         # -----------------------------------
#         # Permissions
#         # -----------------------------------
#         permissions = []
#         for group in groups:
#             role_permissions = group.RolePermissions.filter(
#                 Is_Deleted=False,
#                 Is_Active=True
#             )
#             print('role_permissions',role_permissions)
#             for perm in role_permissions:
#                 permission_name = (
#                     f"{perm.App_Label}."
#                     f"{perm.Model_Name}."
#                     f"{perm.Action}"
#                 )
#                 permissions.append(permission_name)
#         # Remove duplicates
#         permissions = list(set(permissions))
#         # -----------------------------------
#         # Final Response
#         # -----------------------------------
#         return {

#             "access_token": data["access"],

#             "refresh_token": data["refresh"],

#             "token_type": "bearer",

#             "user": {
#                 "id": str(user.id),
#                 "email": user.email,
#                 "username": user.username,
#                 "user_code": user.UserId,
#                 "designation": user.Designation,
#                 "phone_no": user.PhoneNo,
#                 "building_no": user.BuildingHuseNo,
#                 "street": user.Street,
#                 "area": user.Area,
#                 "city": user.City,
#                 "state": user.State,
#                 "country": user.Country,
#                 "date_joined": user.date_joined,
#                 "is_active": user.is_active,
#                 "roles": roles,
#                 "permissions": permissions,
#                 "user_photo": (
#                     user.User_Photo.url
#                     if user.User_Photo else None)}}
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):

        # -----------------------------------
        # Authenticate user
        # -----------------------------------
        data = super().validate(attrs)

        user = self.user

        # -----------------------------------
        # Fetch user's groups
        # -----------------------------------
        groups = Group.objects.filter(
            name=user.Designation,
            Is_Deleted=False
        )
        print('groups',groups)
        # -----------------------------------
        # Roles
        # -----------------------------------
        roles = [
            {
                "id": group.id,
                "name": group.name
            }
            for group in groups
        ]

        # -----------------------------------
        # Permissions
        # -----------------------------------
        permissions = set()

        for group in groups:

            role_permissions = group.RolePermissions.filter(
                Is_Deleted=False,
                Is_Active=True
            )
            print('role_permissions',role_permissions)
            for perm in role_permissions:

                permissions.add(
                    f"{perm.App_Label}."
                    f"{perm.Model_Name}."
                    f"{perm.Action}"
                )

        # -----------------------------------
        # Response
        # -----------------------------------
        return {

            "access_token": data["access"],

            "refresh_token": data["refresh"],

            "token_type": "bearer",

            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "user_code": user.UserId,
                "designation": user.Designation,
                "phone_no": user.PhoneNo,
                "building_no": user.BuildingHuseNo,
                "street": user.Street,
                "area": user.Area,
                "city": user.City,
                "state": user.State,
                "country": user.Country,
                "date_joined": user.date_joined,
                "is_active": user.is_active,

                "roles": roles,

                "permissions": list(permissions),

                "user_photo": (
                    user.User_Photo.url
                    if user.User_Photo else None
                )
            }
        }