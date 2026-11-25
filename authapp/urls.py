from django.urls import path
from .views import *

urlpatterns = [
    # path('roleCRUD/', RoleCRUD.as_view()),
    path('menuCRUD/', MenuCRUD.as_view()),
    # path('rolePermissionCRUD/', RolePermissionCRUD.as_view()),
    # path('RoleList/',RoleList.as_view()),
    # path('RoleWithoutPagination/',RoleWithoutPagination.as_view()),
    path('MenuList/',MenuList.as_view()),
    path('MenuWithoutPagination/',MenuWithoutPagination.as_view()),
    path('MenuListproduct/',MenuListproduct.as_view()),
    path('MenuListproductwithoutpagination/',MenuListproductwithoutpagination.as_view()),
    # path('RolePermissionList/',RolePermissionList.as_view()),
    # path('RolePermissionWithoutPagination/',RolePermissionWithoutPagination.as_view())
    path('MenuProductDropdown/', MenuProductDropdown.as_view()),

    # Role Master
    path('RoleMasterCRUD/', RoleMasterCRUD.as_view()),
    path('RoleMasterList/', RoleMasterList.as_view()),
    path('RoleMasterWithoutPagination/', RoleMasterWithoutPagination.as_view()),

    # Permission Master
    path('PermissionMasterCRUD/', PermissionMasterCRUD.as_view()),
    path('PermissionMasterList/', PermissionMasterList.as_view()),
    path('PermissionMasterWithoutPagination/', PermissionMasterWithoutPagination.as_view()),

    # Role & Permission Assignment
    path('AssignPermissionsToRole/', AssignPermissionsToRole.as_view()),
    path('AssignRoleToUser/', AssignRoleToUser.as_view()),
    path('GetUserPermissions/', GetUserPermissions.as_view()),

]
