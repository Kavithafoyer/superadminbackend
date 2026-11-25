from rest_framework import serializers
from authapp.models import (
    User,
    Menu,
    RoleMaster,
    PermissionMaster,
    RolePermissionMapping,
    UserRoleMapping,
)


# ==============================================================================
# MENU SERIALIZERS
# ==============================================================================

class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'


class MenuSerializers(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'
        depth = 1


# ==============================================================================
# PERMISSION MASTER SERIALIZERS
# ==============================================================================

class PermissionMasterSerializer(serializers.ModelSerializer):
    Permission_Id = serializers.CharField(required=False, allow_blank=True, max_length=64)

    class Meta:
        model = PermissionMaster
        fields = '__all__'


class PermissionMasterSerializers(serializers.ModelSerializer):
    class Meta:
        model = PermissionMaster
        fields = '__all__'
        depth = 1


# ==============================================================================
# ROLE PERMISSION MAPPING SERIALIZERS
# ==============================================================================

class RolePermissionMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermissionMapping
        fields = '__all__'


class RolePermissionMappingSerializers(serializers.ModelSerializer):
    Permission_Details = PermissionMasterSerializer(source='Permission_Id', read_only=True)

    class Meta:
        model = RolePermissionMapping
        fields = '__all__'
        depth = 1


# ==============================================================================
# ROLE MASTER SERIALIZERS
# ==============================================================================

class RoleMasterSerializer(serializers.ModelSerializer):
    Role_Id = serializers.CharField(required=False, allow_blank=True, max_length=64)

    class Meta:
        model = RoleMaster
        fields = '__all__'


class RoleMasterSerializers(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = RoleMaster
        fields = '__all__'
        depth = 1

    def get_permissions(self, obj):
        mappings = obj.role_permissions.filter(Is_Active=True)
        return RolePermissionMappingSerializers(mappings, many=True).data


# ==============================================================================
# USER ROLE MAPPING SERIALIZERS
# ==============================================================================

class UserRoleMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRoleMapping
        fields = '__all__'


class UserRoleMappingSerializers(serializers.ModelSerializer):
    class Meta:
        model = UserRoleMapping
        fields = '__all__'
        depth = 1
