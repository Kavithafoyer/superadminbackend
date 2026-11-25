from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from django.http import HttpResponse
from django.db.models import Q
from .models import *
from .serializers import *
from rest_framework.generics import ListAPIView
# class RoleCRUD(APIView):
#     """
#     APIView for handling CRUD operations on Role model.
#     """
#     def get(self, request, *args, **kwargs):
#         try:
#             params = request.query_params
#             if 'id' in params:
#                 role = Role.objects.get(id=params['id'])
#                 return HttpResponse(JSONRenderer().render(RoleSerializer(role).data), content_type='application/json')
#             elif 'code' in params:
#                 role = Role.objects.get(code=params['code'])
#                 return HttpResponse(JSONRenderer().render(RoleSerializer(role).data), content_type='application/json')
#             else:
#                 roles = Role.objects.all()
#                 return HttpResponse(JSONRenderer().render(RoleSerializer(roles, many=True).data), content_type='application/json')
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
#                                 status=status.HTTP_417_EXPECTATION_FAILED)

#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:
#                 raise TypeError("Empty payload")
#             serializer = RoleSerializer(data=data)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:
#                 raise TypeError("Empty payload")
#             role = Role.objects.get(id=data['id'])
#             serializer = RoleSerializer(role, data=data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return HttpResponse(JSONRenderer().render(serializer.data), content_type='application/json')
#             return HttpResponse(JSONRenderer().render(serializer.errors), content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
#                                 status=status.HTTP_417_EXPECTATION_FAILED)

#     def patch(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:
#                 raise TypeError("Empty payload")
#             role = Role.objects.get(id=data['id'])
#             serializer = RoleSerializer(role, data=data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return HttpResponse(JSONRenderer().render(serializer.data), content_type='application/json')
#             return HttpResponse(JSONRenderer().render(serializer.errors), content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
#                                 status=status.HTTP_417_EXPECTATION_FAILED)

#     def delete(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data or 'id' not in data:
#                 raise TypeError("Please provide a valid ID to delete")
#             role = Role.objects.get(id=data['id'])
#             role.delete()
#             return HttpResponse(JSONRenderer().render({"message": f"Role {data['id']} is deleted"}), content_type='application/json')
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
#                                 status=status.HTTP_417_EXPECTATION_FAILED)

# from rest_framework.generics import ListAPIView
# from django.db.models import Q
# # from .models import Role
# # from .serializers import RoleSerializer

# class RoleList(ListAPIView):
#     # queryset = Role.objects.all()
#     # serializer_class = RoleSerializers

#     def get_queryset(self):
#         try:
#             data = self.request.query_params

#             role = Role.objects.filter(
#                 Q(Is_Deleted=False)
#             ).order_by('-id')

#             return role

#         except Exception as e:
#             raise Exception(f"Error while fetching Role: {str(e)}")


# class RoleWithoutPagination(APIView):

#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params

#             role = Role.objects.filter(
#                 Q(Is_Deleted=False)
#             ).order_by('-id')
#             serializer = RoleSerializers(role, many=True)
#             output = JSONRenderer().render(serializer.data)

#             return HttpResponse(
#                 output,
#                 content_type="application/json",
#                 status=status.HTTP_200_OK
#             )

#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(
#                 output,
#                 content_type="application/json",
#                 status=status.HTTP_400_BAD_REQUEST
#             )


class MenuCRUD(APIView):
    """
    APIView for handling CRUD operations on Menu model.
    """
    def get(self, request, *args, **kwargs):
        try:
            params = request.query_params
            if 'id' in params:
                menu = Menu.objects.get(id=params['id'])
                return HttpResponse(JSONRenderer().render(MenuSerializer(menu).data), content_type='application/json')
            elif 'code' in params:
                menu = Menu.objects.get(code=params['code'])
                return HttpResponse(JSONRenderer().render(MenuSerializer(menu).data), content_type='application/json')
            else:
                top_level_only = params.get('top_level', 'false').lower() == 'true'
                if top_level_only:
                    menus = Menu.objects.filter(parent__isnull=True)
                else:
                    menus = Menu.objects.all()
                return HttpResponse(JSONRenderer().render(MenuSerializer(menus, many=True).data), content_type='application/json')
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Empty payload")
            serializer = MenuSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Empty payload")
            menu = Menu.objects.get(id=data['id'])
            serializer = MenuSerializer(menu, data=data)
            if serializer.is_valid():
                serializer.save()
                return HttpResponse(JSONRenderer().render(serializer.data), content_type='application/json')
            return HttpResponse(JSONRenderer().render(serializer.errors), content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Empty payload")
            menu = Menu.objects.get(id=data['id'])
            serializer = MenuSerializer(menu, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return HttpResponse(JSONRenderer().render(serializer.data), content_type='application/json')
            return HttpResponse(JSONRenderer().render(serializer.errors), content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data or 'id' not in data:
                raise TypeError("Please provide a valid ID to delete")
            menu = Menu.objects.get(id=data['id'])
            menu.delete()
            return HttpResponse(JSONRenderer().render({"message": f"Menu {data['id']} is deleted"}), content_type='application/json')
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)

from .models import Menu
from .serializers import MenuSerializer

class MenuList(ListAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializers

    def get_queryset(self):
        try:
            data = self.request.query_params

            menu = Menu.objects.filter(
                Q(Is_Deleted=False)
            ).order_by('display_order', 'id')

            return menu

        except Exception as e:
            raise Exception(f"Error while fetching Menu: {str(e)}")

class MenuWithoutPagination(APIView):

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params

            menu = Menu.objects.filter(
                Q(Is_Deleted=False)
            ).order_by('display_order', 'id')

            serializer = MenuSerializers(menu, many=True)
            output = JSONRenderer().render(serializer.data)

            return HttpResponse(
                output,
                content_type="application/json",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(
                output,
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

from django.db.models import Q
from rest_framework.generics import ListAPIView

class MenuListproduct(ListAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializers

    def get_queryset(self):
        try:
            data = self.request.query_params

            product = data.get("product")

            menu = Menu.objects.filter(
                Is_Deleted=False,
                is_active=True
            )

            if product:
                menu = menu.filter(product__icontains=product)

            menu = menu.order_by("display_order", "id")

            return menu

        except Exception as e:
            raise Exception(f"Error while fetching Menu: {str(e)}")
        
from rest_framework.generics import ListAPIView

class MenuListproductwithoutpagination(ListAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializers
    pagination_class = None
    def get_queryset(self):
        try:
            data = self.request.query_params

            product = data.get("product")

            menu = Menu.objects.filter(
                Is_Deleted=False,
                is_active=True
            )

            if product:
                menu = menu.filter(product__icontains=product)

            menu = menu.order_by("display_order", "id")

            return menu

        except Exception as e:
            raise Exception(f"Error while fetching Menu: {str(e)}")


from rest_framework.response import Response
class MenuProductDropdown(APIView):
    def get(self, request, *args, **kwargs):
        products = (
            Menu.objects.filter(
                Is_Deleted=False,
                is_active=True
            )
            .exclude(product__isnull=True)
            .exclude(product="")
            .values_list("product", flat=True)
        )

        # Remove duplicates while preserving order
        unique_products = list(dict.fromkeys(p.strip() for p in products if p))

        data = [{"name": p} for p in unique_products]

        return Response(data)
# class RolePermissionCRUD(APIView):
#     """
#     APIView for handling CRUD operations on RolePermission model.
#     """
#     def get(self, request, *args, **kwargs):
#         try:
#             params = request.query_params
#             if 'id' in params:
#                 permission = RolePermission.objects.get(id=params['id'])
#                 return HttpResponse(JSONRenderer().render(RolePermissionSerializer(permission).data), content_type='application/json')
#             elif 'role_id' in params:
#                 permission = RolePermission.objects.get(role_id=params['role_id'])
#                 return HttpResponse(JSONRenderer().render(RolePermissionSerializer(permission).data), content_type='application/json')
#             else:
#                 permissions = RolePermission.objects.all()
#                 return HttpResponse(JSONRenderer().render(RolePermissionSerializer(permissions, many=True).data), content_type='application/json')
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
#                                 status=status.HTTP_417_EXPECTATION_FAILED)

#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:
#                 raise TypeError("Empty payload")
#             serializer = RolePermissionSerializer(data=data)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:
#                 raise TypeError("Empty payload")
#             permission = RolePermission.objects.get(id=data['id'])
#             serializer = RolePermissionSerializer(permission, data=data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return HttpResponse(JSONRenderer().render(serializer.data), content_type='application/json')
#             return HttpResponse(JSONRenderer().render(serializer.errors), content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
#                                 status=status.HTTP_417_EXPECTATION_FAILED)

#     def patch(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:
#                 raise TypeError("Empty payload")
#             permission = RolePermission.objects.get(id=data['id'])
#             serializer = RolePermissionSerializer(permission, data=data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return HttpResponse(JSONRenderer().render(serializer.data), content_type='application/json')
#             return HttpResponse(JSONRenderer().render(serializer.errors), content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
#                                 status=status.HTTP_417_EXPECTATION_FAILED)

#     def delete(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data or 'id' not in data:
#                 raise TypeError("Please provide a valid ID to delete")
#             permission = RolePermission.objects.get(id=data['id'])
#             permission.delete()
#             return HttpResponse(JSONRenderer().render({"message": f"RolePermission {data['id']} is deleted"}), content_type='application/json')
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
#                                 status=status.HTTP_417_EXPECTATION_FAILED)


# # from .models import RolePermission
# # from .serializers import RolePermissionSerializer

# class RolePermissionList(ListAPIView):
#     # queryset = RolePermission.objects.all()
#     # serializer_class = RolePermissionSerializers

#     def get_queryset(self):
#         try:
#             data = self.request.query_params

#             permission = RolePermission.objects.filter(
#                 Q(Is_Deleted=False)
#             ).select_related(
#                 'role'
#             ).order_by('-id')

#             return permission

#         except Exception as e:
#             raise Exception(f"Error while fetching Role Permission: {str(e)}")

# class RolePermissionWithoutPagination(APIView):

#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params

#             permission = RolePermission.objects.filter(
#                 Q(Is_Deleted=False)
#             ).select_related(
#                 'role'
#             ).order_by('-id')

#             serializer = RolePermissionSerializers(permission, many=True)
#             output = JSONRenderer().render(serializer.data)

#             return HttpResponse(
#                 output,
#                 content_type="application/json",
#                 status=status.HTTP_200_OK
#             )

#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(
#                 output,
#                 content_type="application/json",
#                 status=status.HTTP_400_BAD_REQUEST
#             )


# ==============================================================================
# ROLE MASTER CRUD & LIST VIEWS
# ==============================================================================

class RoleMasterCRUD(APIView):
    """
    CRUD APIView for RoleMaster.
    Supports Create, Read, Update, and Soft-Delete for roles per tenant.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy() if hasattr(request.data, 'copy') else request.data
            if hasattr(request, 'user') and getattr(request.user, 'id', None):
                if not data.get('Created_By'):
                    data['Created_By'] = request.user.id
                if not data.get('Updated_By'):
                    data['Updated_By'] = request.user.id
                if not data.get('Organization_Id') and hasattr(request.user, 'Organization_Id'):
                    data['Organization_Id'] = request.user.Organization_Id

            serializer = RoleMasterSerializer(data=data)
            if serializer.is_valid():
                role = serializer.save()
                return Response(
                    {
                        "status": True,
                        "message": "Role created successfully",
                        "data": RoleMasterSerializers(role).data
                    },
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {
                    "status": False,
                    "message": "Validation error",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            params = request.query_params
            pk = params.get('id')
            role_id = params.get('Role_Id')
            org_id = params.get('Organization_Id')

            if pk:
                role = RoleMaster.objects.get(id=pk, Is_Deleted=False)
                return Response(
                    {
                        "status": True,
                        "message": "Role fetched successfully",
                        "data": RoleMasterSerializers(role).data
                    },
                    status=status.HTTP_200_OK
                )
            elif role_id:
                role = RoleMaster.objects.get(Role_Id=role_id, Is_Deleted=False)
                return Response(
                    {
                        "status": True,
                        "message": "Role fetched successfully",
                        "data": RoleMasterSerializers(role).data
                    },
                    status=status.HTTP_200_OK
                )
            else:
                queryset = RoleMaster.objects.filter(Is_Deleted=False).order_by('-id')
                if org_id:
                    queryset = queryset.filter(Organization_Id=org_id)
                serializer = RoleMasterSerializers(queryset, many=True)
                return Response(
                    {
                        "status": True,
                        "message": "Roles fetched successfully",
                        "count": queryset.count(),
                        "data": serializer.data
                    },
                    status=status.HTTP_200_OK
                )
        except RoleMaster.DoesNotExist:
            return Response({"status": False, "message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            pk = data.get('id') or request.query_params.get('id')
            role_id = data.get('Role_Id') or request.query_params.get('Role_Id')

            if pk:
                role = RoleMaster.objects.get(id=pk, Is_Deleted=False)
            elif role_id:
                role = RoleMaster.objects.get(Role_Id=role_id, Is_Deleted=False)
            else:
                return Response({"status": False, "message": "id or Role_Id is required"}, status=status.HTTP_400_BAD_REQUEST)

            if hasattr(request, 'user') and getattr(request.user, 'id', None):
                data = data.copy() if hasattr(data, 'copy') else data
                data['Updated_By'] = request.user.id

            serializer = RoleMasterSerializer(instance=role, data=data, partial=True)
            if serializer.is_valid():
                updated_role = serializer.save()
                return Response(
                    {
                        "status": True,
                        "message": "Role updated successfully",
                        "data": RoleMasterSerializers(updated_role).data
                    },
                    status=status.HTTP_200_OK
                )
            return Response({"status": False, "message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except RoleMaster.DoesNotExist:
            return Response({"status": False, "message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.data if request.data else request.query_params
            pk = data.get('id')
            role_id = data.get('Role_Id')

            if pk:
                role = RoleMaster.objects.get(id=pk, Is_Deleted=False)
            elif role_id:
                role = RoleMaster.objects.get(Role_Id=role_id, Is_Deleted=False)
            else:
                return Response({"status": False, "message": "id or Role_Id is required"}, status=status.HTTP_400_BAD_REQUEST)

            if role.Is_System_Role:
                return Response({"status": False, "message": "System roles cannot be deleted"}, status=status.HTTP_400_BAD_REQUEST)

            role.Is_Deleted = True
            role.save()
            return Response({"status": True, "message": f"Role '{role.Role_Name}' soft-deleted successfully"}, status=status.HTTP_200_OK)
        except RoleMaster.DoesNotExist:
            return Response({"status": False, "message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RoleMasterList(ListAPIView):
    """
    Paginated list view for RoleMaster with search and filters.
    """
    serializer_class = RoleMasterSerializers

    def get_queryset(self):
        queryset = RoleMaster.objects.filter(Is_Deleted=False).order_by('-id')
        params = self.request.query_params
        org_id = params.get('Organization_Id')
        scope = params.get('Data_Scope')
        search = params.get('search')

        if org_id:
            queryset = queryset.filter(Organization_Id=org_id)
        if scope:
            queryset = queryset.filter(Data_Scope__iexact=scope)
        if search:
            queryset = queryset.filter(
                Q(Role_Name__icontains=search) |
                Q(Role_Id__icontains=search) |
                Q(Role_Description__icontains=search)
            )
        return queryset


class RoleMasterWithoutPagination(APIView):
    """
    Unpaginated list of active roles for rapid dropdowns.
    """
    def get(self, request, *args, **kwargs):
        try:
            org_id = request.query_params.get('Organization_Id')
            queryset = RoleMaster.objects.filter(Is_Deleted=False, Is_Active=True).order_by('Role_Name')
            if org_id:
                queryset = queryset.filter(Organization_Id=org_id)

            serializer = RoleMasterSerializers(queryset, many=True)
            return Response(
                {
                    "status": True,
                    "message": "Roles fetched successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==============================================================================
# PERMISSION MASTER VIEWS
# ==============================================================================

class PermissionMasterCRUD(APIView):
    """
    CRUD APIView for PermissionMaster catalog.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PermissionMasterSerializer(data=data)
            if serializer.is_valid():
                perm = serializer.save()
                return Response(
                    {
                        "status": True,
                        "message": "Permission created successfully",
                        "data": PermissionMasterSerializers(perm).data
                    },
                    status=status.HTTP_201_CREATED
                )
            return Response({"status": False, "message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            params = request.query_params
            pk = params.get('id')
            code = params.get('Permission_Code')
            module = params.get('Module_Name')

            if pk:
                perm = PermissionMaster.objects.get(id=pk)
                return Response({"status": True, "data": PermissionMasterSerializers(perm).data}, status=status.HTTP_200_OK)
            elif code:
                perm = PermissionMaster.objects.get(Permission_Code=code)
                return Response({"status": True, "data": PermissionMasterSerializers(perm).data}, status=status.HTTP_200_OK)
            else:
                queryset = PermissionMaster.objects.filter(Is_Active=True).order_by('Module_Name', 'Permission_Code')
                if module:
                    queryset = queryset.filter(Module_Name__iexact=module)
                return Response({"status": True, "count": queryset.count(), "data": PermissionMasterSerializers(queryset, many=True).data}, status=status.HTTP_200_OK)
        except PermissionMaster.DoesNotExist:
            return Response({"status": False, "message": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PermissionMasterList(ListAPIView):
    """
    Paginated list of all system permissions.
    """
    serializer_class = PermissionMasterSerializers

    def get_queryset(self):
        queryset = PermissionMaster.objects.filter(Is_Active=True).order_by('Module_Name', 'Permission_Code')
        module = self.request.query_params.get('Module_Name')
        search = self.request.query_params.get('search')
        if module:
            queryset = queryset.filter(Module_Name__iexact=module)
        if search:
            queryset = queryset.filter(
                Q(Permission_Code__icontains=search) |
                Q(Module_Name__icontains=search) |
                Q(Description__icontains=search)
            )
        return queryset


class PermissionMasterWithoutPagination(APIView):
    """
    Unpaginated list of all permissions, ideal for the Admin Permission Matrix UI.
    """
    def get(self, request, *args, **kwargs):
        try:
            module = request.query_params.get('Module_Name')
            queryset = PermissionMaster.objects.filter(Is_Active=True).order_by('Module_Name', 'Action_Name')
            if module:
                queryset = queryset.filter(Module_Name__iexact=module)
            serializer = PermissionMasterSerializers(queryset, many=True)
            return Response(
                {
                    "status": True,
                    "message": "Permissions fetched successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==============================================================================
# ROLE-PERMISSION ASSIGNMENT & PERMISSION MATRIX
# ==============================================================================

class AssignPermissionsToRole(APIView):
    """
    Bulk assigns or updates permission flags for a role.
    Payload Example:
    {
        "role_id": 1,
        "permissions": [
            {
                "permission_id": 1,
                "can_create": true,
                "can_view": true,
                "can_edit": true,
                "can_delete": false,
                "can_export": false
            }
        ]
    }
    """
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            role_identifier = data.get('role_id') or data.get('Role_Id')
            permissions_data = data.get('permissions', [])

            if not role_identifier:
                return Response({"status": False, "message": "role_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            if str(role_identifier).isdigit():
                role = RoleMaster.objects.get(id=int(role_identifier), Is_Deleted=False)
            else:
                role = RoleMaster.objects.get(Role_Id=str(role_identifier), Is_Deleted=False)

            assigned_mappings = []
            for perm_item in permissions_data:
                perm_id = perm_item.get('permission_id') or perm_item.get('Permission_Id')
                if not perm_id:
                    continue

                if str(perm_id).isdigit():
                    perm = PermissionMaster.objects.filter(id=int(perm_id)).first()
                else:
                    perm = PermissionMaster.objects.filter(Permission_Code=str(perm_id)).first() or \
                           PermissionMaster.objects.filter(Permission_Id=str(perm_id)).first()

                if not perm:
                    continue

                mapping, created = RolePermissionMapping.objects.update_or_create(
                    Role_Id=role,
                    Permission_Id=perm,
                    defaults={
                        'Can_Create': perm_item.get('can_create', False),
                        'Can_View': perm_item.get('can_view', False),
                        'Can_Edit': perm_item.get('can_edit', False),
                        'Can_Delete': perm_item.get('can_delete', False),
                        'Can_Export': perm_item.get('can_export', False),
                        'Is_Active': perm_item.get('is_active', True),
                    }
                )
                assigned_mappings.append(mapping)

            return Response(
                {
                    "status": True,
                    "message": f"Successfully mapped {len(assigned_mappings)} permissions to role '{role.Role_Name}'",
                    "data": RoleMasterSerializers(role).data
                },
                status=status.HTTP_200_OK
            )
        except RoleMaster.DoesNotExist:
            return Response({"status": False, "message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==============================================================================
# USER ROLE ASSIGNMENT & PERMISSIONS INTROSPECTION
# ==============================================================================

class AssignRoleToUser(APIView):
    """
    Assigns a primary role to a user.
    Payload: { "user_id": 1, "role_id": 1 }
    """
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            user_id = data.get('user_id')
            role_id = data.get('role_id')

            if not user_id or not role_id:
                return Response({"status": False, "message": "Both user_id and role_id are required"}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(id=user_id)
            if str(role_id).isdigit():
                role = RoleMaster.objects.get(id=int(role_id), Is_Deleted=False)
            else:
                role = RoleMaster.objects.get(Role_Id=str(role_id), Is_Deleted=False)

            user.role = role
            user.Roll_Name = role.Role_Name
            user.save()

            # Also maintain UserRoleMapping record
            UserRoleMapping.objects.update_or_create(
                User_Id=user,
                Role_Id=role,
                defaults={
                    'Organization_Id': getattr(user, 'Organization_Id', 1),
                    'Is_Active': True
                }
            )

            return Response(
                {
                    "status": True,
                    "message": f"Role '{role.Role_Name}' assigned to user '{user.username}' successfully",
                    "data": {
                        "user_id": user.id,
                        "username": user.username,
                        "role": RoleMasterSerializers(role).data
                    }
                },
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response({"status": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except RoleMaster.DoesNotExist:
            return Response({"status": False, "message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetUserPermissions(APIView):
    """
    Returns the complete permissions matrix for the logged-in user (or specified user_id).
    Used by the frontend to conditionally show/hide sidebar menus, action buttons, and routes.
    """
    def get(self, request, *args, **kwargs):
        try:
            user_id = request.query_params.get('user_id')
            if user_id:
                user = User.objects.get(id=user_id)
            elif hasattr(request, 'user') and getattr(request.user, 'id', None):
                user = request.user
            else:
                user = User.objects.first()

            if not user:
                return Response({"status": False, "message": "User not identified"}, status=status.HTTP_400_BAD_REQUEST)

            # Superusers have bypass access
            if user.is_superuser:
                return Response(
                    {
                        "status": True,
                        "is_superuser": True,
                        "role": "SuperAdmin",
                        "data_scope": "All",
                        "all_permissions": True,
                        "permissions": []
                    },
                    status=status.HTTP_200_OK
                )

            role = user.role
            if not role:
                return Response(
                    {
                        "status": True,
                        "is_superuser": False,
                        "role": None,
                        "data_scope": "Own",
                        "permissions": []
                    },
                    status=status.HTTP_200_OK
                )

            mappings = RolePermissionMapping.objects.filter(Role_Id=role, Is_Active=True).select_related('Permission_Id')
            permissions_list = []
            for m in mappings:
                permissions_list.append({
                    "module": m.Permission_Id.Module_Name,
                    "code": m.Permission_Id.Permission_Code,
                    "can_view": m.Can_View,
                    "can_create": m.Can_Create,
                    "can_edit": m.Can_Edit,
                    "can_delete": m.Can_Delete,
                    "can_export": m.Can_Export
                })

            return Response(
                {
                    "status": True,
                    "is_superuser": False,
                    "role": {
                        "id": role.id,
                        "Role_Id": role.Role_Id,
                        "Role_Name": role.Role_Name,
                        "Data_Scope": role.Data_Scope
                    },
                    "permissions": permissions_list
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)