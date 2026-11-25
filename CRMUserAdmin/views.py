# =========================
# 1. Python Standard Library
# =========================
import os
import json
import base64
import smtplib
import ssl
import imaplib
import imapclient
import email
import email.utils
from urllib import response
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================
# 2. Third-Party Libraries
# =========================
from validate_email import validate_email

# LangChain / AI
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.vectorstores import FAISS
# from langchain.prompts import PromptTemplate
# from langchain.chains.question_answering import load_qa_chain
# from langchain_google_genai import (GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI)

# =========================
# 3. Django Imports
# =========================
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.files.base import ContentFile
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from django.db.models import Q, Max, F, Sum

from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password

# =========================
# 4. Django REST Framework
# =========================
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated

# from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from CRMSuperAdmin.models import *
from CRMSuperAdmin.serializer import *
# =========================
# 5. Project Settings
# =========================
from CRM import settings
from CRM.settings import DATABASES, REST_FRAMEWORK

from .models import (
    Useraddress, Userrole, CRMUsers, Userorganizationmaster,
      CRMBusinessHours, Template, Notification, Userlookup
)

# from .models import(
#     Ticket , TicketResponse , TransactionalSeries
# )

from .models import *
from .serializer import *

from .serializer import (
    UseraddressSerializer, UseraddressSerializers,
    UserroleSerializer, UserroleSerializers,
    CRMUsersSerializer, CRMUsersSerializers,
    UserorganizationmasterSerializer, UserorganizationmasterSerializers,
    TicketSerializer, TicketSerializers,
    TicketResponseSerializer, TicketResponseSerializers,
    CRMBusinessHoursSerializer, CRMBusinessHoursSerializers,
    TransactionalSeriesSerializer, TransactionalSeriesSerializers,
    TemplateSerializer, TemplateSerializers,
    NotificationSerializer, NotificationSerializers,
    UserlookupSerializer, UserlookupSerializers,
    NotificationMulti, CRMUserTemplate, CRMUserAutoResponse,
    Financial_Calendar_DetailsSerialzer,
    Communication_AddressSerialzer,
    Business_HoursSerialzer
)

# =========================
# 7. Multi-Tenant Utilities
# =========================
from utils.threadlocal import get_current_tenant
from django_multitenant.utils import set_current_tenant


# =========================
# 8. Environment Variables
# =========================
os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY_HERE"
Tenant = get_current_tenant()

# Base_URL = f'https://backend.crmfarm.in/{Tenant}'
Base_URL = f'https://127.0.0.1:8000'


# for automatic id generation with string value

def ID(model,serializer, db,id):
    last = model.objects.all().order_by(id).last()
    if not last:
        return "000000001"
    serializer = serializer(last)
    output = json.loads(JSONRenderer().render(serializer.data))
    intid = int(output[id][4:]) + 1
    return str(intid).zfill(9)

def MailId3():
    mailId = UserAdminMailMaster.objects.order_by('MailId').last()
    if not mailId:
        return "MAA" + "000000001"
    serializer =UserAdminMailMasterSerializer(mailId)
    output = json.loads(JSONRenderer().render(serializer.data))
    mailI = int(output["MailId"][4:]) + 1
    return 'MAA' + str(mailI).zfill(9)


def Transaction_Series(orgId, module1, key, anotherkey,id):
    print("inside", anotherkey)
    uniquekey = anotherkey

    # Retrieve the configuration for the organization
    module = UserTransactionalseries.objects.get(Organization_Id=orgId)
    serialize = UserTransactionalseriesSerializer(module)
    prefix = JSONRenderer().render(serialize.data)
    pre = json.loads(prefix)

    print("pre", pre)
    print("key", key, module)

    out = pre[key]
    print("out", out)

    # Get the last record for the module
    Organizatio = module1.objects.all().order_by('id').last()
    print("Organizatio", Organizatio)

    if Organizatio is None:
        last_unique_key = None
    else:
        last_unique_key = getattr(Organizatio, uniquekey, None)

    print("last_unique_key", last_unique_key)

    if out['Type'] == "Automatic":
        if Organizatio is None:
            Journals = f"{out['Prefix']}{out['Start_Number']}00001{out['Suffix']}"
            UniqueId = Journals
            print("UniqueId1", UniqueId)
        else:
            if last_unique_key is not None:
                Organizat = last_unique_key[3:8]
                Organiza = int(Organizat) + 1
                Configur = f"{out['Prefix']}{out['Start_Number']}{str(Organiza).zfill(5)}{out['Suffix']}"
                UniqueId = Configur
                print("UniqueId2", UniqueId)
            else:
                print(f"Error: The last record does not have an attribute named '{uniquekey}'")
                return None
    else:
        UniqueId = id
        print("UniqueId3", UniqueId)

    return UniqueId


# request
def requestpost(serializer, data):
    try:
        serializer = serializer(data=data)
        # print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return HttpResponse(JSONRenderer().render(serializer.data), content_type='application/json')
        # print(serializer.errors)
        return HttpResponse(JSONRenderer().render(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # print(e)
        return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                            status=status.HTTP_400_BAD_REQUEST)


def requestget(model, serializer, data, page, Operator) -> object:
    try:
        print('requestget')
        startval = (int(page) - 1) * REST_FRAMEWORK['PAGE_SIZE']
        endval = int(page) * REST_FRAMEWORK['PAGE_SIZE']
        if Operator == "and":
            count = model.objects.filter(**data).count()
            models = model.objects.filter(**data)[startval:endval]
        elif Operator == "or":
            count = model.objects.filter(data).count()
            models = model.objects.filter(data)[startval:endval]
        else:
            return HttpResponse(JSONRenderer().render({"Error": "Please send perfect Operator"}),
                                content_type='applicatiom/json',
                                status=status.HTTP_400_BAD_REQUEST)
        results = json.loads(JSONRenderer().render(serializer(models, many=True).data))
        return HttpResponse(JSONRenderer().render({"count": count, "page": page, "results": results}),
                            content_type='application/json')
    except Exception as e:
        return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='applicatiom/json',
                            status=status.HTTP_400_BAD_REQUEST)


def requestput(model, serializers, data, filterdata):
    try:
        # print(filterdata)
        models = model.objects.get(**filterdata)
        # print(models)
        serializer = serializers(models, data=data)
        if serializer.is_valid():
            serializer.save()
            return HttpResponse(JSONRenderer().render(serializer.data), content_type='application/json')
        # print(serializer.errors)
        return HttpResponse(JSONRenderer().render(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                            status=status.HTTP_400_BAD_REQUEST)


def requestpatch(model, serializers, data, filterdata):
    try:
        models = model.objects.get(**filterdata)
        # print(models)
        serializer = serializers(models, data=data, partial=True)
        # print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return HttpResponse(JSONRenderer().render(serializer.data), content_type='application/json')
        # print(serializer.errors)
        return HttpResponse(JSONRenderer().render(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                            status=status.HTTP_400_BAD_REQUEST)


def requestdelete(model, serializer, data, filterdata):
    try:
        models = model.objects.get(**filterdata)
        serializer = serializer(models, data, partial=True)
        # print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
        output = JSONRenderer().render(serializer.data)
        return HttpResponse(output, content_type='application/json')
    except Exception as e:
        output = JSONRenderer().render({"Error": str(e)})
        return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class UserCRUD_mailid(ListAPIView):
    queryset = User.objects.all()
    serializer_class = Userserializer
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            email = data['email']
            user = User.objects.get(email=email)
            print("user:",user)
            return HttpResponse(JSONRenderer().render(Userserializers(user).data), content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_400_BAD_REQUEST)
        
@method_decorator(csrf_exempt, name='dispatch')
class UserCRUD_GET(ListAPIView):
    queryset = User.objects.all()
    serializer_class = Userserializer
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            print("data:",data)
            username = data['username']
            print("username:",username)
            user = User.objects.get(username=username)
            print("user:",user)
            return HttpResponse(JSONRenderer().render(Userserializers(user).data), content_type='application/json')
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_400_BAD_REQUEST)
    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:  # Check if data is empty
                raise TypeError("Request data cannot be empty")
            is_Tenantactive = data['is_Tenantactive']
            print("is_Tenantactive:",is_Tenantactive)
            # Update all instances of YourModel to set is_Tenantactive to False
            module =User.objects.all().update(is_Tenantactive=is_Tenantactive)
            return Response("Updated Successfully", status=status.HTTP_200_OK)
        except Subscriptions.DoesNotExist:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# This APIs for the CRUD operations of the User.
# Shanath
@method_decorator(csrf_exempt, name='dispatch')
class UserCRUD(ListAPIView):
    queryset = User.objects.all()
    serializer_class = Userserializer
    

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            username = data['username']
            user = User.objects.get(username=username)
            return HttpResponse(JSONRenderer().render(Userserializers(user).data), content_type='application/json')
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='applicatiom/json',
                                status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            Userorganizationmaster.objects.get(id=data['Organization_Id'])
            if data['User_Photo'] != '':
                decoded_data = base64.b64decode((data['User_Photo']))
                data['User_Photo'] = ContentFile(decoded_data, name=data['User_Photo_Name'])
                del data['User_Photo_Name']
            else:
                del data['User_Photo']
                del data['User_Photo_Name']
            validate_password(password=data['password'], user=User)
            data['password'] = make_password(data['password'])
            # return HttpResponse("OK")
            return requestpost(serializer=Userserializer, data=data)
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            if data['User_Photo'] != '':
                decoded_data = base64.b64decode((data['User_Photo']))
                data['User_Photo'] = ContentFile(decoded_data, name=data['User_Photo_Name'])
                del data['User_Photo_Name']
            else:
                del data['User_Photo']
                del data['User_Photo_Name']
            validate_password(password=data['password'], user=User)
            data['password'] = make_password(data['password'])
            return requestput(model=User, serializers=Userserializer, data=data,
                              filterdata={'username': data['username']})
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            # print('User_Photo' in data.keys())
            if 'User_Photo' in data.keys():
                if data['User_Photo'] != '':
                    decoded_data = base64.b64decode((data['User_Photo']))
                    data['User_Photo'] = ContentFile(decoded_data, name=data['User_Photo_Name'])
                    del data['User_Photo_Name']
                else:
                    del data['User_Photo']
                    del data['User_Photo_Name']
            if 'password' in data.keys():
                validate_password(password=data['password'], user=User)
                data['password'] = make_password(data['password'])
            print(data)
            return requestpatch(model=User, serializers=Userserializer, data=data,
                                filterdata={'username': data['username']})
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            if data == '' or data == {}:
                raise TypeError("Give the perfect Payload")
            user = User.objects.get(username=data['username'])
            serializer = Userserializer(user, data={"is_active": False}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return HttpResponse(JSONRenderer().render({"Message": str(data['username']) + " Deleted Successfully"}),
                                    content_type='application/json')
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_400_BAD_REQUEST)




# This APIs for the List, Filter and Search operations of the User.
# Shanath
# 12/07/2022
class UserAdditional(ListAPIView):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = Userserializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    # List API
    def get_queryset(self):
        try:
            data = self.request.GET.get('is_active')
            # print(data)
            Organization_Id = self.request.GET.get('Organization_Id')
            # data = True
            user = User.objects.filter(is_active__exact=data, Organization_Id=Organization_Id).order_by('-date_joined')
            return user
        except:
            return User.objects.none()

    # Filter API
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            data1 = {"username__icontains": data['username'], "first_name__icontains": data['first_name'],
                     "last_name__icontains": data['last_name'], "email__icontains": data['email'],
                     "is_active": data['is_active'], "date_joined__range": data['daterange'],
                     "Organization_Id": data['Organization_Id']}
            return requestget(model=User, serializer=Userserializer, data=data1, page=data['page'], Operator='and')
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)

    # Search API
    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            d = Q()
            d |= Q(**{"username__icontains": data['search']})
            d |= Q(**{"first_name__icontains": data['search']})
            d |= Q(**{"last_name__icontains": data['search']})
            d |= Q(**{"email__icontains": data['search']})
            d &= Q(**{"is_active__exact": data['is_active']})
            d &= Q(**{"Organization_Id": data['Organization_Id']})
            return requestget(model=User, serializer=Userserializer, data=d, page=data['page'], Operator='or')
            # user = User.objects.filter(Q(username__icontains=data['search']) | Q(first_name__icontains=data['search']) |
            #                            Q(last_name__icontains=data['search']) | Q(email__icontains=data['search']),
            #                            is_active__exact=data['is_active'])
            # return HttpResponse(JSONRenderer().render(Userserializer(user, many=True).data),
            #                     content_type='application/json')
            # data = request
            user = User.objects.filter(Q(username__icontains=data['search']) | Q(first_name__icontains=data['search']) |
                                       Q(last_name__icontains=data['search']) | Q(email__icontains=data['search']),
                                       is_active__exact=data['is_active'])
            return HttpResponse(JSONRenderer().render(Userserializer(user, many=True).data),
                                content_type='application/json')
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)
        

# Active Users List

class UserActiveList(ListAPIView):

    queryset = User.objects.all()
    serializer_class = Userserializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id=data['id']
            # data = request
            print("data",data)
            module=User.objects.filter(Q(User_Login_Status=True)).exclude(id=id)
            seri=Userserializer(module,many=True)
            output=JSONRenderer().render(seri.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)
        
# Active Users List

class UsersList(ListAPIView):

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            module=User.objects.filter(Q(is_active=True))
            seri=Userserializer(module,many=True)
            output=JSONRenderer().render(seri.data)
            return HttpResponse(output, content_type='application/json')
        
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)
        


class Formpermastercrud(ListAPIView):
    queryset = FormMaster.objects.all()
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serialize = FormMasterSerializer(data=data)
            if serialize.is_valid():
                serialize.save()
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = FormMaster.objects.get(id=id)
            serialize = FormMasterSerializers(module)
            output = JSONRenderer().render(serialize.data)
            da=json.loads(output)
            print("da",da)
            data1=da['FormId']
            permision=[]
            for i in data1:
                permision.append(i['ModulePermission'])
            per = []
            for i in permision:
                for y in i:
                    per.append(y)
            output1= JSONRenderer().render(per)
            return HttpResponse(output1,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = FormMaster.objects.get(id=id)
            serialize = FormMasterSerializer(instance=module, data=request.data, partial=True)
            if serialize.is_valid():
                serialize.save()
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class Formmasterlist(APIView):
    
    queryset = FormMaster.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self,request,*args,**kwargs):
        module = FormMaster.objects.all()
        serialize = FormMasterSerializers(module,many=True)
        output = JSONRenderer().render(serialize.data)
        return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
    
# Getting the All Permission List

class Allpermission(ListAPIView):
    queryset = Permission.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get(self,request,*args,**kwargs):
        module = Permission.objects.all()
        serialize = PermissionSerializer(module,many=True)
        output = JSONRenderer().render(serialize.data)
        data=json.loads(output)
        per=[]
        for i in data:
            per.append(i['id'])
        output=JSONRenderer().render(per)
        return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)

class PermissionList(ListAPIView):
    queryset = Permission.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get(self,request,*args,**kwargs):
        module = Permission.objects.all()
        serialize = PermissionSerializer(module,many=True)
        output = JSONRenderer().render(serialize.data)
        return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
    
# Form Master CRUD Operations

class Formpermissioncrud(ListAPIView):
    queryset = FormPermission.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serialize = FormPermissionSerializer(data=data)
            if serialize.is_valid():
                serialize.save()
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = FormPermission.objects.get(id=id)
            serialize = FormPermissionSerializers(module)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = FormPermission.objects.get(id=id)
            serialize = FormPermissionSerializer(instance=module, data=request.data)
            if serialize.is_valid():
                serialize.save()
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class Formpermisionlist(ListAPIView):
    queryset = FormPermission.objects.all()
    serializer_class = FormPermissionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        module = FormPermission.objects.all()
        return module


class Formpermisionlists(ListAPIView):
    queryset = FormPermission.objects.all()
    serializer_class = FormPermissionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get(self,request,*args,**kwargs):
        module = FormPermission.objects.all()
        serialize = FormPermissionSerializer(module,many=True)
        output = JSONRenderer().render(serialize.data)
        return HttpResponse(output,content_type='application/json')


class Formpermissionfilter(ListAPIView):
    queryset = FormPermission.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    # filter api
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            module = FormPermission.objects.filter(
                Q(ModuleName__icontains=data['ModuleName']))
            serialize = FormPermissionSerializer(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



# For Role CRUD Operations
class RoleCRUD(ListAPIView):
    queryset = Group.objects.all()
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [DjangoModelPermissions]

    def post(self,request,*args,**kwargs):
        try:
            data = request.data
            Organizatio=Group.objects.all().order_by('Role_Id').last()
            if not Organizatio:
                data['Role_Id'] = "ROL000000001"
            else:
                Organizati = Organizatio.Role_Id
                Organizat = int(Organizati[4:])
                Organiza = Organizat + 1
                Configur = "ROL" + str(Organiza).zfill(9)
                data['Role_Id'] = Configur
            items = Group.objects.filter(Q(name__exact=data['name']))
            for item in items:
                print(item)
                return HttpResponse(JSONRenderer().render({"Error": data['name'] + " is already exists"}), content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            serialize = GroupSerializer(data=data)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            return HttpResponse(JSONRenderer().render(serialize.errors), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        

    def get(self,request,*args,**kwargs):
        try:
            data=request.query_params
            id=data['Role_Id']
            module = Group.objects.get(Role_Id=id)
            serialize = GroupSerializers(module)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output=JSONRenderer().render({"error":str(e)})
            return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)


    def put(self,request,*args,**kwargs):
        try:
            data=request.data
            id=data['Role_Id']
            module=Group.objects.get(Role_Id=id)
            serialize = GroupSerializer(instance=module,data=data)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
            return HttpResponse(JSONRenderer().render(serialize.errors), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)


    def delete(self,request,*args,**kwargs):
        try:
            data=request.query_params
            id=data['Role_Id']
            module=Group.objects.get(Role_Id=id)
            serialize = GroupSerializer(module,{"Is_Deleted":True},partial=True)
            if serialize.is_valid():
                serialize.save()
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output=JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)


class RoleAdditionalCRUD(ListAPIView):
    queryset = Group.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    # filter api
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            module = Group.objects.filter(
                Q(name__icontains=data['name']), Q(Is_Deleted=False))
            serialize = GroupSerializer(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    # search api
    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            module = Group.objects.filter(Q(name__icontains=data['Search']) | Q(
                Role_Id__icontains=data['Search']), Q(Is_Deleted=False))
            serialize = GroupSerializer(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class userrolesearch(ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def get_queryset(self):
        data=self.request.GET.get('search')
        module = Group.objects.filter((Q(name__icontains=data) | Q(
                Role_Id__icontains=data))&Q(Is_Deleted=False))
        return module
    
class Rolelist(ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        module=Group.objects.filter(Is_Deleted=False)
        return module

class Rolelistwithpagination(APIView):
    def get(self,request,*args,**kwargs):
        data=request.query_params
        module=Group.objects.filter(Is_Deleted=False)
        serialize=GroupSerializer(module,many=True)
        output=JSONRenderer().render(serialize.data)
        return HttpResponse(output,content_type='application/json')



class CRMUserCRUD(ListAPIView):
    queryset =UserAdmin.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            data['RoleId'] = Userrole.objects.get(id=data['RoleId'])
            # data = request
            data['UserId'] = 'USE' + str(ID(CRMUsers,CRMUsersSerializer,db['db'],'UserId'))
            decoded_data = base64.b64decode((data['User_Photo']))
            data['User_Photo'] = ContentFile(decoded_data,name=data['User_Photo_Name'])
            del data['User_Photo_Name']
            validate_password(password=data['User_Password'], user=CRMUsers)
            data['User_Password'] = make_password(data['User_Password'])
            module =UserAdmin.objects.create(**data)
            output = JSONRenderer().render("User created successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data=request.headers
            # data = request
            id = data['UserId']
            module =UserAdmin.objects.get(UserId=id)
            serializer = CRMUsersSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['UserId']
            decoded_data = base64.b64decode((data['User_Photo']))
            data['User_Photo'] = ContentFile(decoded_data)
            validate_password(password=data['User_Password'], user=CRMUsers)
            data['User_Password'] = make_password(data['User_Password'])
            module =UserAdmin.objects.filter(UserId=id).update(**data)
            # serialize = UserroleSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data=request.headers
            # data = request
            id = data['UserId']
            module =UserAdmin.objects.filter(UserId=id).update(Is_Deleted=True)
            # module = Customers.objects.get(Customer_Id=data)
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class CRMUserarchive(ListAPIView):
    queryset =UserAdmin.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def patch(self, request, *args, **kwargs):
        try:
            data=request.headers
            # data = request
            id = data['UserId']
            module =UserAdmin.objects.filter(UserId=id).update(Is_Archived=True)
            # module=Customers.objects.get(Customer_Id=data)
            # serializer = CRMUsersSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Archived Sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class CRMUserlist(ListAPIView):
    queryset =UserAdmin.objects.all()
    authentication_classes = [JWTAuthentication]
    serializer_class = CRMUsersSerializers
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        data=self.request.headers
        print(data)
        module =UserAdmin.objects.filter(Is_Deleted=False, Is_Archived=False).order_by('-Created_Date')
        return module
        # return output




class Userrolelist(ListAPIView):
    queryset = Userrole.objects.all()
    authentication_classes = [JWTAuthentication]
    serializer_class = UserroleSerializer
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        data=self.request.headers
        module = Userrole.objects.filter(Is_Deleted=False).order_by('-Created_Date')
        # serializer = UserroleSerializers(module, many=True)
        # output = JSONRenderer().render(serializer.data)
        # return HttpResponse(output, content_type='application/json')
        return module



class Templatelist(ListAPIView):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializers
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        data=self.request.headers
        module = Template.objects.filter(Is_Deleted=False).order_by('-Created_Date')
        # serializer = TemplateSerializers(module, many=True)
        # output = JSONRenderer().render(serializer.data)
        # return HttpResponse(output, content_type='application/json')
        return module




class NotificationCRUD(ListAPIView):
    queryset = Notification.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            data['NotificationId'] = 'NOT' + str(ID(Notification,NotificationSerializers,db['db'],'NotificationId'))
            data['TemplateId'] = Template.objects.get(id=data['TemplateId'])
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module=Notification.objects.create(**data)
            # serialize = NotificationMulti(data=data)
            # # serializer = NotificationMulti(data=data)
            # print(serialize.is_valid())
            # if serialize.is_valid():
            #     serialize.save(using=DATABASES['crmuseradmin'])
            output = JSONRenderer().render("Notification Created successfully")
            return HttpResponse(output, content_type='application/json')
            # return HttpResponse(JSONRenderer().render(module.data))
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data=request.headers
            # data = request
            id = data['NotificationId']
            module = Notification.objects.get(NotificationId=id)
            serializer = NotificationSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['NotificationId']
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            data['TemplateId'] = Template.objects.get(id=data['TemplateId'])
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module = Notification.objects.filter(NotificationId=id).update(**data)
             # serialize = UserroleSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data=request.headers
            # data = request
            id = data['NotificationId']
            module = Notification.objects.filter(NotificationId=id).update(Is_Deleted=True)
            # module = Customers.objects.get(Customer_Id=data)
            # serializer = NotificationSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



class Notificationlist(ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializers
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        data=self.request.headers
        module = Notification.objects.filter(Is_Deleted=False).order_by('-Created_Date')
        # serializer = NotificationSerializers(module, many=True)
        # output = JSONRenderer().render(serializer.data)
        # return HttpResponse(output, content_type='application/json')
        return module

# class NotificationMultiList(APIView):
#     def get(self, request, *args, **kwargs):
#         module = Notification.objects.db_manager('crmuseradmin').filter().order_by('-Created_Date')
#         serializer = NotificationMulti(module, many=True)
#         output = JSONRenderer().render(serializer.data)
#         return HttpResponse(output, content_type='application/json')



class TicketCRUD(ListAPIView):
    # queryset = Ticket.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            # data = request
            data['TktNo'] = "TKT" + str(ID(Ticket,TicketSerializer,db['db'],'TktNo'))
            data['AssignTo'] =UserAdmin.objects.get(id=data['AssignTo'])
            # lis=[]
            # for i in Asign:
            #     AssignTo =UserAdmin.objects.get(id=i)
            #     serializer=CRMUsersSerializer(AssignTo)
            #     Assign =serializer.data
            #     lis.append(Assign['id'])
            # data['AssignTo']=Ticket.AssignTo(lis)
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])

            serializer = Ticket.objects.create(**data)
            # print(data)
            # print(serializer)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Ticket Created Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data=request.headers
            # data = request
            id = data['TktNo']
            module = Ticket.objects.get(TktNo=id)
            serializer = TicketSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['TktNo']
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module = Ticket.objects.filter(TktNo=id).update(**data)
             # serialize = UserroleSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['TktNo']
            module = Ticket.objects.filter(TktNo=id).update(Is_Deleted=True)
            # module = Customers.objects.get(Customer_Id=data)
            # serializer = TicketSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



class Ticketlist(ListAPIView):
    # queryset = Ticket.objects.all()
    # serializer_class = TicketSerializers
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        data=self.request.headers
        module = Ticket.objects.filter(Is_Deleted=False).order_by('-Created_Date')
        # serializer = TicketSerializers(module, many=True)
        # output = JSONRenderer().render(serializer.data)
        # return HttpResponse(output, content_type='application/json')
        return module



class TicketResponseCRUD(ListAPIView):
    # queryset = TicketResponse.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            data['Ticketresponseid'] = 'RES' + str(ID(TicketResponse,TicketResponseSerializer,db['db'],'Ticketresponseid'))
            data['Ticketid'] = Ticket.objects.get(id=data['Ticketid'])
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            serializer = TicketResponse.objects.create(**data)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Ticket Response Done")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data=request.headers
            # data = request
            id = data['Ticketresponseid']
            module = TicketResponse.objects.get(Ticketresponseid=id)
            serializer = TicketResponseSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['Ticketresponseid']
            data['TktNo'] = Ticket.objects.get(id=data['TktNo'])
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module = TicketResponse.objects.filter(Ticketresponseid=id).update(**data)
             # serialize = UserroleSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.quer
            # data = request
            id = data['Ticketresponseid']
            module = TicketResponse.objects.filter(Ticketresponseid=id).update(Is_Deleted=True)
            # module = Customers.objects.get(Customer_Id=data)
            # serializer = TicketResponseSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



class TicketResponselist(ListAPIView):
    # queryset = TicketResponse.objects.all()
    # serializer_class = TicketResponseSerializers
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        data=self.request.headers
        module = TicketResponse.objects.filter(Is_Deleted=False).order_by('-Created_Date')
        # serializer = TicketResponseSerializers(module, many=True)
        # output = JSONRenderer().render(serializer.data)
        # return HttpResponse(output, content_type='application/json')
        return module


def SendMail(subject, From, To,Cc, Body, Host, Port, Password):
    # #print(Password)
    mail = MIMEMultipart('mixed')
    mail['subject'] = subject
    mail['From'] = From
    mail['To'] =  ', '.join(To)
    mail['Cc'] = ', '.join(Cc)
    mail['Disposition-Notification-To'] = From
    mail['Return-Receipt-To'] = From
    body = MIMEText(Body, 'html')
    mail.attach(body)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(Host, Port, context=context) as server:
        server.login(From, Password)
        recipients = To +Cc
        status = server.sendmail(From,recipients, mail.as_string())
        server.close()
    if status == {}:
        return True
    else:
        return False
    

# def SendMailOTP(subject, From, To, Body, Host, Port, Password):
#     print("Password:", Password)
#     mail = MIMEMultipart('mixed')
#     mail['subject'] = subject
#     mail['From'] = From
#     mail['To'] = To
#     mail['Disposition-Notification-To'] = From
#     mail['Return-Receipt-To'] = From
#     body = MIMEText(Body, 'html')
#     mail.attach(body)
#     context = ssl.create_default_context()
#     # context.check_hostname = False
#     # context.verify_mode = ssl.CERT_NONE
#     print("SSL context configured")
 
#     with smtplib.SMTP_SSL(Host, Port, context=context) as server:
#             print("Connected to the server")
#             server.login(From, Password)
#             print("Logged in to the server")
#             status = server.sendmail(From, To, mail.as_string())
#             server.close()
#             print("Email sent, server closed")
    
#     if status == {}:
#         return True
#     else:
#         return False
    
def SendMailOTP(subject, From, To, Body, Host, Port, Password, retries=3):
    mail = MIMEMultipart('mixed')
    mail['subject'] = subject
    mail['From'] = From
    mail['To'] = To
    mail['Disposition-Notification-To'] = From
    mail['Return-Receipt-To'] = From
    body = MIMEText(Body, 'html')
    mail.attach(body)
    context = ssl.create_default_context()

    while retries > 0:
        try:
            with smtplib.SMTP_SSL(Host, Port, context=context) as server:
                server.login(From, Password)
                status = server.sendmail(From, To, mail.as_string())
                server.close()

            if status == {}:
                return True
        except smtplib.SMTPException as e:
            print(f"SMTPException: {e}")
            retries -= 1
            if retries == 0:
                raise
        except Exception as e:
            print(f"Exception: {e}")
            retries -= 1
            if retries == 0:
                raise

    return False


def SendMailC(subject, From, To,  Body, Host, Port, Password):
    print("again check")
    mail = MIMEMultipart('mixed')
    mail['subject'] = subject
    mail['From'] = From
    mail['To'] = ', '.join(To)  # Join multiple recipients with comma and space
    mail['Disposition-Notification-To'] = From
    mail['Return-Receipt-To'] = From
    body = MIMEText(Body, 'html')
    mail.attach(body)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(Host, Port, context=context) as server:
        print("test")
        server.login(From, Password)
        recipients = To   # Combine To and CC recipients
        print("recipients",)
        status = server.sendmail(From, recipients, mail.as_string())
        print("test1")
        server.close()
    if status == {}:
        return True
    else:
        return False

class UserlookupCRUD(ListAPIView):
    queryset = Userlookup.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            # data = request
            data['Lookupid']= 'LOO' + str(ID(Userlookup,UserlookupSerializer,db['db'],'Lookupid'))
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            serializer = Userlookup.objects.create(**data)
            # print(data)
            # print(serializer)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("User Lookup Created Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data=request.headers
            # data = request
            id = data['Lookupid']
            module = Userlookup.objects.get(Lookupid=id)
            serializer = UserlookupSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['Lookupid']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module = Userlookup.objects.filter(Lookupid=id).update(**data)
             # serialize = UserroleSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module = Userlookup.objects.get(id=id).delete()
            # module = Customers.objects.get(Customer_Id=data)
            # serializer = UserlookupSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



class Userlookuplist(ListAPIView):
    queryset = Userlookup.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get(self,request,*args,**kwargs):
        db=self.request.headers
        module = Userlookup.objects.filter(Is_Deleted=False).order_by('-id')
        serializer = UserlookupSerializer(module, many=True)
        output = JSONRenderer().render(serializer.data)
        return HttpResponse(output, content_type='application/json')

class Userlookuplistwithpagination(ListAPIView):
    queryset = Userlookup.objects.all()
    serializer_class=UserlookupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.GET.get('db')
        module = Userlookup.objects.filter(Is_Deleted=False).order_by('-id')
        return module    

class Userlookupsearch(ListAPIView):
    queryset = Userlookup.objects.all()
    serializer_class= UserlookupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def get_queryset(self):
        data=self.request.GET.get('search')
        module=Userlookup.objects.filter((Q(Lookupid__icontains=data)|Q(Lookupname__icontains=data)|
                                          Q(Defaultvalue__icontains=data)|Q(Purpose__icontains=data))&Q(Is_Deleted=False))
        return module



class CRMBusinessHoursCRUD(ListAPIView):
    queryset = CRMBusinessHours.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            data['BusinessHours_Id'] = 'BUS' + str(ID(CRMBusinessHours,CRMBusinessHoursSerializer,db['db'],'BusinessHours_Id'))
            # data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            # data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            # data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            serializer = CRMBusinessHours.objects.create(**data)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("BusinessHours Created Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data=request.headers
            # data = request
            id = data['BusinessHours_Id']
            module = CRMBusinessHours.objects.get(BusinessHours_Id=id)
            serializer = CRMBusinessHoursSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['BusinessHours_Id']
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module = CRMBusinessHours.objects.filter(BusinessHours_Id=id).update(**data)
             # serialize = UserroleSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data=request.headers
            # data = request
            id = data['BusinessHours_Id']
            module = CRMBusinessHours.objects.filter(BusinessHours_Id=id).update(Is_Deleted=True)
            # module = Customers.objects.get(Customer_Id=data)
            # serializer = CRMBusinessHoursSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



class CRMBusinessHourslist(ListAPIView):
    queryset = CRMBusinessHours.objects.all()
    serializer_class = CRMBusinessHoursSerializers
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        data=self.request.headers
        module = CRMBusinessHours.objects.filter(Is_Deleted=False).order_by('-Created_Date')
        # serializer = CRMBusinessHoursSerializer(module, many=True)
        # output = JSONRenderer().render(serializer.data)
        # return HttpResponse(output, content_type='application/json')
        return module



class UserroleCRUD(ListAPIView):
    queryset = Userrole.objects.all()
    serializer_class = UserroleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    # def get_queryset(self):
    #     try:
    #         headers = self.request.headers
    #         data = self.request.GET.get('RoleId')
    #         return Userrole.objects.db_manager(headers['company']).filter(id=data)
    #     except:
    #         return Userrole.objects.none()

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db = request.headers
            data['RoleId'] = 'ROL' + str(ID(Userrole, UserroleSerializer, db['db'], 'RoleId'))
            # data['Created_By'] =UserAdmin.objects.get(id=data['Created_By'])
            # data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            # CRMUsers.objects.get(id=data['Created_By'])
            # CRMUsers.objects.get(id=data['Updated_By'])
            # modules = data['ModulePermissions']
            # forms = data['FormPermissions']
            # permissions = data['Permission']
            # del data['ModulePermissions']
            # del data['FormPermissions']
            # del data['Permission']
            print("data",data)
            serializer = Userrole.objects.create(**data)
            # serializer.ModulePermissions.set(modules)
            # serializer.FormPermissions.set(forms)
            # serializer.Permission.set(permissions)
            output = JSONRenderer().render("User Role Created Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            if serializer:
                serializer.delete()
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.headers
            id = request.GET.get('Id')
            # data = request
            # id = data['RoleId']
            module = Userrole.objects.get(id=id)  # RoleId=id
            serializer = UserroleSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db = request.headers
            id = data['id']
            # data['Created_By'] = User.objects.get(id=data['Created_By'])
            # data['Updated_By'] = User.objects.get(id=data['Updated_By'])
            CRMUsers.objects.get(id=data['Created_By'])
            CRMUsers.objects.get(id=data['Updated_By'])
            modules = data['ModulePermissions']
            forms = data['FormPermissions']
            permissions = data['Permission']
            del data['ModulePermissions']
            del data['FormPermissions']
            del data['Permission']
            role = Userrole.objects.get(id=id)
            Userrole.objects.filter(id=id).update(**data)
            role.ModulePermissions.set(modules)
            role.FormPermissions.set(forms)
            role.Permission.set(permissions)
            # serialize = UserroleSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            headers = request.headers
            data = request.data
            id = data['id']
            module = Userrole.objects.filter(id=id).update(Is_Deleted=True)
            # module = Customers.objects.get(Customer_Id=data)
            # serializer = UserroleSerializer(module)
            # if serializer.is_valid():
            #     serializer.save()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class TaskuserCRUD(ListAPIView):
    queryset = Taskuser.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            data['TaskId']='TAS' +str(ID(Taskuser,TaskuserSerializer,db['db'],'TaskId'))
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            data['Created_By'] =UserAdmin.objects.get(id=data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            asign = data['AssignTo']
            del data['AssignTo']
            module = Taskuser.objects.create(**data)
            module.AssignTo.set(asign)
            module.save()
            output = JSONRenderer().render("Task Created Successfully")
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)

    def get(self,request,*args,**kwargs):
        try:
            data=request.query_params
            db=request.headers
            module = Taskuser.objects.get(TaskId=data['TaskId'])
            serialize = TaskuserSerializer(module)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)


    def put (self,request,*args,**kwargs):
        try:
            data=request.data
            db=request.headers
            id=data['TaskId']
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            data['Created_By'] =UserAdmin.objects.get(id=data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            asign = data['AssignTo']
            del data['AssignTo']
            module = Taskuser.objects.filter(TaskId=id).update(**data)
            output = JSONRenderer().render("Task updated Successfully")
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)

    
    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['TaskId']
            module = Taskuser.objects.filter(TaskId=id).update(Is_Deleted=True)
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class Taskuserlist(ListAPIView):
    queryset = Taskuser.objects.all()
    serializer_class=TaskuserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        data=self.request.GET.get('db')
        module =Taskuser.objects.filter(Is_Deleted=False).order_by('Created_Date')
        return module

class Mytaskuserlist(ListAPIView):
    queryset = Taskuser.objects.all()
    serializer_class=TaskuserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.GET.get('db')
        data=self.request.GET.get('Created_By')
        module =Taskuser.objects.filter(Created_By=data,Is_Deleted=False).order_by('Created_Date')
        return module


class CompanyCRUD(ListAPIView):
    queryset = Company.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self,request,*args,**kwargs):
        try:
            data=request.data
            db=request.headers
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            data['Company_Id']='CMP' + str(ID(Company,CompanySerializer,db['db'],'Company_Id'))
            decoded_data = base64.b64decode((data['CompanyLogo']))
            data['CompanyLogo'] = ContentFile(decoded_data,name=data['CompanyLogo_Name'])
            del data['CompanyLogo_Name']
            comp = Company.objects.create(**data)
            output = JSONRenderer().render("Company Created Successfully")
            return HttpResponse(output,content_type = 'application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type='application/json',statu=status.HTTP_400_BAD_REQUEST)

    def get(self,request,*args,**kwargs):
        try:
            data=request.query_params
            db=request.headers
            module = Company.objects.get(Company_Id=data['Company_Id'])
            serialize = CompanySerializer(module)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)


    def put (self,request,*args,**kwargs):
        try:
            data=request.data
            db=request.headers
            id=data['Company_Id']
            decoded_data = base64.b64decode((data['CompanyLogo']))
            data['CompanyLogo'] = ContentFile(decoded_data)
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            module = Company.objects.filter(Company_Id=id).update(**data)
            output = JSONRenderer().render("Company updated Successfully")
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)

    
    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['Company_Id']
            module = Taskuser.objects.filter(Company_Id=id).update(Is_Deleted=True)
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# class Useradmindashboard(APIView):

#     def get(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             id=data['Organization_Id']
#             module = Subscriptions.objects.get(Organization_Id=id)
#             serialize = Subscriptionserializer(module)
#             out=serialize.data
#             module = Plan.objects.get(Plan_Id=out['Plan_Id'])
#             serialize=Planserializer(module)
#             planname=serialize.data
#             Plname=planname['Plan_Name']
#             addon=planname['AllocatedAddons']
#             pl=sum(addon)
#             data1={"Subscription_Id":out['Subscription_Id'],"Storage_Size":out['Storage_Size'],"Plan_Name":Plname,"module":pl}
#             output = JSONRenderer().render(data1)
#             return HttpResponse(output,content_type = 'application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)

#     def put(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             id=data['Organization_Id']
#             module = Renewal.objects.get(Organization_Id=id)
#             serialize = Renewalserializer(module)
#             renewdate=serialize.data
#             data1={"RenewaldueDate":renewdate['RenewaldueDate']}
#             output = JSONRenderer().render(data1)
#             return HttpResponse(output,content_type = 'application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)


class Dashboardticket(APIView):
    def get(self,request,*args,**kwargs):
        try:
            data=request.query_params
            id=data['UserId']
            module = Ticket.objects.filter(Created_By=id).count
            module1 = Ticket.objects.filter(Q(Created_By=id) & Q(Status=False)).count
            module2 = Ticket.objects.filter(Q(Created_By=id) & Q(Status=True)).count
            data1={"Total":module,"Resolved":module1,"Pending":module2}
            output = JSONRenderer().render(data1)
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)


class Dashboardtask(APIView):
    def get(self,request,*args,**kwargs):
        try:
            data=request.query_params
            id=data['UserId']
            module = Taskuser.objects.filter(Created_By=id).count
            module1 = Taskuser.objects.filter(Q(Created_By=id) & Q(Status=False)).count
            module2 = Taskuser.objects.filter(Q(Created_By=id) & Q(Status=True)).count
            data1={"Total":module,"Resolved":module1,"Pending":module2}
            output = JSONRenderer().render(data1)
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)


class Dashboarduser(APIView):
    def get(self,request,*args,**kwargs):
        try:
            data=request.query_params
            id=data['UserId']
            module =UserAdmin.objects.filter(Q(Created_By=id) & Q(Is_Deleted=False))
            serialize = CRMUsersSerializer(module,many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)


# CRM UserAdmin CRUD Operations

class CRMUserTemplateCRUD(ListAPIView):

    queryset = CRMUserTemplate.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            # data['UserTemplate_Id'] = 'TEM' + str(ID(CRMUserTemplate,CRMUserTemplateSerializer,db['db'],'UserTemplate_Id'))
            data['UserTemplate_Id']=Transaction_Series(data['Organization_Id'],CRMUserTemplate,"CRMUser_Template","UserTemplate_Id",data['UserTemplate_Id'])
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            data['Organization_Id'] =Userorganizationmaster.objects.get(id=data['Organization_Id'])
            module = CRMUserTemplate.objects.create(**data)
            output = JSONRenderer().render("created successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            print(id)
            module = CRMUserTemplate.objects.get(id=id)
            serializer = CRMUserTemplateSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            id=data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            modue1=  CRMUserTemplate.objects.get(id=id)
            module = CRMUserTemplate.objects.filter(id=id).update(**data)
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module1 = CRMUserTemplate.objects.get(id=id)
            module = CRMUserTemplate.objects.filter(id=id).update(Is_Deleted=True)
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class CRMUserTemplateAdditional(ListAPIView):
    queryset = CRMUserTemplate.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def get(self,request,*args,**kwargs):
        db=request.headers
        module=CRMUserTemplate.objects.filter(Is_Deleted=False).order_by('-Created_Date')[:10]
        serializer = CRMUserTemplateSerializer(module,many=True)
        output = JSONRenderer().render(serializer.data)
        return HttpResponse(output, content_type='application/json')

class CRMUserCampaignTemplate(ListAPIView):
    queryset = CRMUserTemplate.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def get(self,request,*args,**kwargs):
        db=request.headers
        module=CRMUserTemplate.objects.filter(Q(Is_Deleted=False)&Q(Template_Type="Campaign")).order_by('-Created_Date')
        serializer = CRMUserTemplateSerializer(module,many=True)
        output = JSONRenderer().render(serializer.data)
        return HttpResponse(output, content_type='application/json')

    
# CRUD Operation For the Auto Setup

class CRMUserAutoResponseCRUD(ListAPIView):

    queryset = CRMUserAutoResponse.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            # print("data",data)
            # data['AutoResponse_Id'] = 'AUT' + str(ID(CRMUserAutoResponse,CRMUserAutoResponseSerializer,db['db'],'AutoResponse_Id'))
            data['AutoResponse_Id']=Transaction_Series(data['Organization_Id'],CRMUserAutoResponse,"CRMUser_AutoResponse","AutoResponse_Id",data['AutoResponse_Id'])

            # print("data['AutoResponse_Id']",data['AutoResponse_Id'] )
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            data['Organization_Id'] =Userorganizationmaster.objects.get(id=data['Organization_Id'])

            l=data['Template_Id']
            del data['Template_Id']
            module = CRMUserAutoResponse.objects.create(**data)
            module.Template_Id.set(l)
            output = JSONRenderer().render("created successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            print(id)
            module = CRMUserAutoResponse.objects.get(id=id)
            serializer = CRMUserAutoResponseSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            id=data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            l=data['Template_Id']
            del data['Template_Id']
            module=CRMUserAutoResponse.objects.get(id=id)
            for key, value in data.items():
                setattr(module, key, value)
            module.save()
            module.Template_Id.clear()
            module.Template_Id.set(l)
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module = CRMUserAutoResponse.objects.filter(id=id)
            module1 = CRMUserAutoResponse.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


#  Auto Setup Additional
#  
class CRMUserAutoResponseAdditional(ListAPIView):
    queryset = CRMUserAutoResponse.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def get(self,request,*args,**kwargs):
        db=request.headers
        module=CRMUserAutoResponse.objects.filter(Is_Deleted=False).order_by('-Created_Date')[:10]
        serializer = CRMUserAutoResponseSerializer(module,many=True)
        output = JSONRenderer().render(serializer.data)
        return HttpResponse(output, content_type='application/json')
    
    def post(self,request,*args,**kwargs):
        db=request.headers
        data=request.data
        module=CRMUserAutoResponse.objects.filter(Q(Is_Deleted=False) & Q(Applied_To=data['Applied_To'])  ).order_by('-Created_Date')
        serializer = CRMUserAutoResponseSerializers(module,many=True)
        output = JSONRenderer().render(serializer.data)
        return HttpResponse(output, content_type='application/json')


# CRM  Organization Master Changed Plan

class CRMorganizationCRUD(ListAPIView):

    queryset = Userorganizationmaster.objects.all()
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [DjangoModelPermissions]
    
    def post(self,request,*args,**kwargs):
        try:
            data = request.data
            db=request.headers
            print("data",data['Organization_Logo'])
            decoded_data = base64.b64decode(data['Organization_Logo'])
            data['Organization_Logo'] = ContentFile(decoded_data, name=data['OrganizationLogo_Name'])
            del data['OrganizationLogo_Name']
            # Serialize Communication_Address
            print("again")
            add=data['Address_Id']
            add['Address_Id']='ADD' + str(ID(Communication_Address,Communication_AddressSerialzer,db['db'],'Address_Id'))
            addres = Communication_Address.objects.create(**add)
            ad=addres.pk
            print(ad)
            data['Organization_Address']=Communication_Address.objects.get(id=ad)
            # Serialize Business_Hours
            bus=data['Businesshours_Id']
            bus['Businesshours_Id']='BUS' + str(ID(Business_Hours,Business_HoursSerialzer,db['db'],'Businesshours_Id'))
            business = Business_Hours.objects.create(**bus)
            bd=business.pk
            print(bd)
            data['Business_Hour']=Business_Hours.objects.get(id=bd)
            # Serialize Financial_Calendar_Details
            fin=data['Calendar_Id']
            fin['Calendar_Id']='CAL' + str(ID(Financial_Calendar_Details,Financial_Calendar_DetailsSerialzer,db['db'],'Calendar_Id'))
            fincal= Financial_Calendar_Details.objects.create(**fin)
            fd=fincal.pk
            print(fd)
            data['Fiscal_Year']=Financial_Calendar_Details.objects.get(id=fd)
            # Serialize Company
            del data['Address_Id']
            del data['Businesshours_Id']
            del data['Calendar_Id']
            data['Organization_Id']='ORG' + str(ID(Userorganizationmaster,UserorganizationmasterSerializer,db['db'],'Organization_Id'))
            # data['Created_By']=UserAdmin.objects.get(id=data['Created_By'])
            # data['Updated_By']=UserAdmin.objects.get(id=data['Updated_By'])
            print("data",data)
            serialize = Userorganizationmaster.objects.create(**data)
            output = JSONRenderer().render("Organization Created Successfully")
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            print("chekc")
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, status=status.HTTP_400_BAD_REQUEST)


    def get(self,request,*args,**kwargs):
        try:
            data = request.query_params
            db=request.headers
            # data = request
            id = data['id']
            print("id",id)
            module = Userorganizationmaster.objects.get(id=id)
            serializer = UserorganizationmasterSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


    def put(self,request,*args,**kwargs):
        try:
            data = request.data
            db=request.headers
            CompanyAddress = data['Organization_Address']
            Businesshours_Id = data['Business_Hour']
            Calendar_Id = data['Fiscal_Year']
            # module = Communication_Address.objects.get(id=CompanyAddress['id'])
            module1=Communication_Address.objects.filter(id=CompanyAddress['id']).update(**CompanyAddress)
            module2=Business_Hours.objects.filter(id=Businesshours_Id['id']).update(**Businesshours_Id)
            module3=Financial_Calendar_Details.objects.filter(id=Businesshours_Id['id']).update(**Calendar_Id)
            data['Organization_Address'] = CompanyAddress['id']
            data['Business_Hour'] = Businesshours_Id['id']
            data['Fiscal_Year'] =Calendar_Id['id']
            module4 = Userorganizationmaster.objects.filter(id=data['id']).update(**data)
            output = JSONRenderer().render("Updates Successfully")
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, *args, **kwargs):
            try:
                data=request.query_params
                db=request.headers
                # data = request
                id = data['id']
                module = Userorganizationmaster.objects.filter(id=id).update(Is_Deleted=True)
                output = JSONRenderer().render("Deleted Successfully")
                return HttpResponse(output, content_type='application/json')
            except Exception as e:
                output = JSONRenderer().render({"Error": str(e)})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



#  For Lead Scoring API Creations

@method_decorator(csrf_exempt, name='dispatch')
class UserAdminPredictionQuestionsCRUD(ListAPIView):
    # queryset = UserAdminPredictionQuestions.objects.all()
    # serializer_class = UserAdminPredictionQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            print("data",data)
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module=UserAdminPredictionQuestions.objects.create(**data)
            moduel_dict=module.__dict__
            for key in list(moduel_dict):
                if key.startswith("_"):
                    del moduel_dict[key]
            output = JSONRenderer().render(moduel_dict)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = UserAdminPredictionQuestions.objects.get(id=id)
            serializer = UserAdminPredictionQuestionsSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module2 = UserAdminPredictionQuestions.objects.get(id=id)
            module = UserAdminPredictionQuestions.objects.filter(id=id).update(**data)
            module1= UserAdminPredictionQuestions.objects.get(id=id)
            moduledict=module1.__dict__
            print("moduledict",moduledict)
            for key in list(moduledict.keys()):
                if key.startswith("_"):
                    del moduledict[key]
            output = JSONRenderer().render(moduledict)
            print("output",output)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module1 = UserAdminPredictionQuestions.objects.get(id=id)
            module = UserAdminPredictionQuestions.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class UserAdminPredictionQuestionsAdditional(ListAPIView):
    # queryset = UserAdminPredictionQuestions.objects.all()
    # serializer_class = UserAdminPredictionQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.headers
        module=UserAdminPredictionQuestions.objects.all().order_by('-Created_Date')
        return module
    
@method_decorator(csrf_exempt, name='dispatch')
class UserAdminStatusQuestionsCRUD(ListAPIView):
    queryset = UserAdminStatusQuestions.objects.all()
    serializer_class = UserAdminStatusQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            print("data",data)
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module=UserAdminStatusQuestions.objects.create(**data)
            moduel_dict=module.__dict__
            for key in list(moduel_dict):
                if key.startswith("_"):
                    del moduel_dict[key]
            output = JSONRenderer().render(moduel_dict)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = UserAdminStatusQuestions.objects.get(id=id)
            serializer = UserAdminStatusQuestionsSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module2 = UserAdminStatusQuestions.objects.get(id=id)
            module = UserAdminStatusQuestions.objects.filter(id=id).update(**data)
            module1= UserAdminStatusQuestions.objects.get(id=id)
            moduledict=module1.__dict__
            print("moduledict",moduledict)
            for key in list(moduledict.keys()):
                if key.startswith("_"):
                    del moduledict[key]
            output = JSONRenderer().render(moduledict)
            print("output",output)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            id = data['id']
            module1 = UserAdminStatusQuestions.objects.get(id=id)
            module = UserAdminStatusQuestions.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class UserAdminStatusQuestionsAdditional(ListAPIView):
    queryset = UserAdminStatusQuestions.objects.all()
    serializer_class = UserAdminStatusQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.headers
        module=UserAdminStatusQuestions.objects.all().order_by('-Created_Date')
        return module

# Score Questions CRUD Operation & List
@method_decorator(csrf_exempt, name='dispatch')
class UserAdminScoreQuestionsCRUD(ListAPIView):
    queryset = UserAdminScoreQuestions.objects.all()
    serializer_class = UserAdminScoreQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            print("data",data)
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module=UserAdminScoreQuestions.objects.create(**data)
            moduel_dict=module.__dict__
            for key in list(moduel_dict):
                if key.startswith("_"):
                    del moduel_dict[key]
            output = JSONRenderer().render(moduel_dict)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = UserAdminScoreQuestions.objects.get(id=id)
            serializer = UserAdminScoreQuestionsSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module = UserAdminScoreQuestions.objects.filter(id=id).update(**data)
            module1= UserAdminScoreQuestions.objects.get(id=id)
            moduledict=module1.__dict__
            print("moduledict",moduledict)
            for key in list(moduledict.keys()):
                if key.startswith("_"):
                    del moduledict[key]
            output = JSONRenderer().render(moduledict)
            print("output",output)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module = UserAdminScoreQuestions.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class UserScoreQuestionsAdditional(ListAPIView):
    queryset = UserAdminScoreQuestions.objects.all()
    serializer_class = UserAdminScoreQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.headers
        module=UserAdminScoreQuestions.objects.all().order_by('-Created_Date')
        return module


@method_decorator(csrf_exempt, name='dispatch')
class AdminCallActivityQuestionsCRUD(ListAPIView):
    # queryset = AdminCallActivityQuestions.objects.all()
    # serializer_class = AdminCallActivityQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            print("data",data)
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module=AdminCallActivityQuestions.objects.create(**data)
            moduel_dict=module.__dict__
            for key in list(moduel_dict):
                if key.startswith("_"):
                    del moduel_dict[key]
            output = JSONRenderer().render(moduel_dict)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = AdminCallActivityQuestions.objects.get(id=id)
            serializer = AdminCallActivityQuestionsSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module2=AdminCallActivityQuestions.objects.get(id=id)
            module = AdminCallActivityQuestions.objects.filter(id=id).update(**data)
            module1= AdminCallActivityQuestions.objects.get(id=id)
            moduledict=module1.__dict__
            print("moduledict",moduledict)
            for key in list(moduledict.keys()):
                if key.startswith("_"):
                    del moduledict[key]
            output = JSONRenderer().render(moduledict)
            print("output",output)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            id = data['id']
            module1=AdminCallActivityQuestions.objects.get(id=id)
            module=AdminCallActivityQuestions.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class AdminCallActivityQuestionsAdditional(ListAPIView):
    # queryset = AdminCallActivityQuestions.objects.all()
    # serializer_class = AdminCallActivityQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.headers
        module=AdminCallActivityQuestions.objects.all().order_by('-Created_Date')
        return module


## Lead Mail Activity
@method_decorator(csrf_exempt, name='dispatch')
class AdminMailActivityQuestionsCRUD(ListAPIView):
    # queryset = AdminMailActivityQuestions.objects.all()
    # serializer_class = AdminMailActivityQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            print("data",data)
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module=AdminMailActivityQuestions.objects.create(**data)
            moduel_dict=module.__dict__
            for key in list(moduel_dict):
                if key.startswith("_"):
                    del moduel_dict[key]
            output = JSONRenderer().render(moduel_dict)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = AdminMailActivityQuestions.objects.get(id=id)
            serializer = AdminMailActivityQuestionsSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module2 =AdminMailActivityQuestions.objects.get(id=id)
            module =AdminMailActivityQuestions.objects.filter(id=id).update(**data)
            module1=AdminMailActivityQuestions.objects.get(id=id)
            moduledict=module1.__dict__
            print("moduledict",moduledict)
            for key in list(moduledict.keys()):
                if key.startswith("_"):
                    del moduledict[key]
            output = JSONRenderer().render(moduledict)
            print("output",output)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            id = data['id']
            module1 = AdminMailActivityQuestions.objects.get(id=id)
            module = AdminMailActivityQuestions.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class AdminMailActivityQuestionsAdditional(ListAPIView):
    # queryset = AdminMailActivityQuestions.objects.all()
    # serializer_class = AdminMailActivityQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.headers
        module=AdminMailActivityQuestions.objects.all().order_by('-Created_Date')
        return module
# Lead Web Activity
@method_decorator(csrf_exempt, name='dispatch')
class AdminWebActivityQuestionsCRUD(ListAPIView):
    # queryset =AdminWebActivityQuestions.objects.all()
    # serializer_class = AdminWebActivityQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            print("data",data)
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            
            module=AdminWebActivityQuestions.objects.create(**data)
            moduel_dict=module.__dict__
            for key in list(moduel_dict):
                if key.startswith("_"):
                    del moduel_dict[key]
            output = JSONRenderer().render(moduel_dict)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = AdminWebActivityQuestions.objects.get(id=id)
            serializer = AdminWebActivityQuestionsSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module2 = AdminWebActivityQuestions.objects.get(id=id)
            module = AdminWebActivityQuestions.objects.filter(id=id).update(**data)
            module1= AdminWebActivityQuestions.objects.get(id=id)
            moduledict=module1.__dict__
            print("moduledict",moduledict)
            for key in list(moduledict.keys()):
                if key.startswith("_"):
                    del moduledict[key]
            output = JSONRenderer().render(moduledict)
            print("output",output)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            id = data['id']
            module1 = AdminWebActivityQuestions.objects.get(id=id)
            module = AdminWebActivityQuestions.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class WebActivityQuestionsAdditional(ListAPIView):
    # queryset = AdminWebActivityQuestions.objects.all()
    # serializer_class = AdminWebActivityQuestionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.headers
        module=AdminWebActivityQuestions.objects.all().order_by('-Created_Date')
        return module


# Deal Probability

class UserAdminDealProbabilityCRUD(ListAPIView):
    # queryset = UserAdminDealProbability.objects.all()
    # serializer_class = UserAdminDealProbabilitySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            # print("data",data)
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module=UserAdminDealProbability.objects.create(**data)
            moduel_dict=module.__dict__
            for key in list(moduel_dict):
                if key.startswith("_"):
                    del moduel_dict[key]
            output = JSONRenderer().render(moduel_dict)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = UserAdminDealProbability.objects.get(id=id)
            serializer = UserAdminDealProbabilitySerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module = UserAdminDealProbability.objects.filter(id=id).update(**data)
            module1= UserAdminDealProbability.objects.get(id=id)
            moduledict=module1.__dict__
            print("moduledict",moduledict)
            for key in list(moduledict.keys()):
                if key.startswith("_"):
                    del moduledict[key]
            output = JSONRenderer().render(moduledict)
            print("output",output)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module = UserAdminDealProbability.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class UserAdminDealProbabilityAdditional(ListAPIView):
    # queryset = UserAdminDealProbability.objects.all()
    # serializer_class = UserAdminDealProbabilitySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.headers
        module=UserAdminDealProbability.objects.all().order_by('-Created_Date')
        return module
    
# UserAdminDealFactorSetup

class UserAdminDealFactorSetupCRUD(ListAPIView):
    # queryset = UserAdminDealFactorSetup.objects.all()
    # serializer_class = UserAdminDealFactorSetupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            # print("data",data)
            serialize = UserAdminDealFactorSetupSerializer(data=data)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serialize.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = UserAdminDealFactorSetup.objects.get(id=id)
            serializer = UserAdminDealFactorSetupSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['id']
            module = UserAdminDealFactorSetup.objects.get(id=id)
            serialize = UserAdminDealFactorSetupSerializer(instance=module, data=request.data)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serialize.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module = UserAdminDealFactorSetup.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class UserAdminDealFactorSetupAdditional(ListAPIView):
    # queryset = UserAdminDealFactorSetup.objects.all()
    # serializer_class = UserAdminDealWeightSetupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.headers
        module=UserAdminDealFactorSetup.objects.all().order_by('-Created_Date')
        return module
    
class UserAdminDealFactorSetupFullList(ListAPIView):
    # queryset = UserAdminDealFactorSetup.objects.all()
    serializer_class = UserAdminDealWeightSetupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            module=UserAdminDealFactorSetup.objects.all()
            seri=UserAdminDealWeightSetupSerializer(module,many=True)
            output=JSONRenderer().render(seri.data)
            return HttpResponse(output, content_type='application/json')
        
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)


# UserAdminDealWeightSetup

class UserAdminDealWeightSetupCRUD(ListAPIView):
    # queryset = UserAdminDealWeightSetup.objects.all()
    # serializer_class = UserAdminDealWeightSetupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            # print("data",data)
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module=UserAdminDealWeightSetup.objects.create(**data)
            moduel_dict=module.__dict__
            for key in list(moduel_dict):
                if key.startswith("_"):
                    del moduel_dict[key]
            output = JSONRenderer().render(moduel_dict)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = UserAdminDealWeightSetup.objects.get(id=id)
            serializer = UserAdminDealWeightSetupSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module = UserAdminDealWeightSetup.objects.filter(id=id).update(**data)
            module1= UserAdminDealWeightSetup.objects.get(id=id)
            moduledict=module1.__dict__
            print("moduledict",moduledict)
            for key in list(moduledict.keys()):
                if key.startswith("_"):
                    del moduledict[key]
            output = JSONRenderer().render(moduledict)
            print("output",output)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module = UserAdminDealWeightSetup.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class UserAdminDealWeightSetupAdditional(ListAPIView):
    # queryset = UserAdminDealWeightSetup.objects.all()
    # serializer_class = UserAdminDealWeightSetupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.headers
        module=UserAdminDealWeightSetup.objects.all().order_by('-Created_Date')
        return module
    

# UserAdminDealPrediction


class UserAdminDealPredictionCRUD(ListAPIView):
    # queryset = UserAdminDealPrediction.objects.all()
    # serializer_class = UserAdminDealPredictionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self,request,*args,**kwargs):
        try:
            db=request.headers
            data=request.data
            # print("data",data)
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module=UserAdminDealPrediction.objects.create(**data)
            moduel_dict=module.__dict__
            for key in list(moduel_dict):
                if key.startswith("_"):
                    del moduel_dict[key]
            output = JSONRenderer().render(moduel_dict)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = UserAdminDealPrediction.objects.get(id=id)
            serializer = UserAdminDealPredictionSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id = data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            module = UserAdminDealPrediction.objects.filter(id=id).update(**data)
            module1= UserAdminDealPrediction.objects.get(id=id)
            moduledict=module1.__dict__
            print("moduledict",moduledict)
            for key in list(moduledict.keys()):
                if key.startswith("_"):
                    del moduledict[key]
            output = JSONRenderer().render(moduledict)
            print("output",output)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module = UserAdminDealPrediction.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class UserAdminDealPredictionAdditional(ListAPIView):
    # queryset = UserAdminDealPrediction.objects.all()
    # serializer_class = UserAdminDealPredictionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        db=self.request.headers
        module=UserAdminDealPrediction.objects.all().order_by('-Created_Date')
        return module

##userid must be unique in put method also userid cant able to change
class UserAdminMailConfigurationCRUD(ListAPIView):
    queryset = UserAdminMailConfiguration.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
            try:
                data = request.data
                db=request.headers                
                print("data",data)
                try:
                    with smtplib.SMTP_SSL(data['SMTPHost'], data['SMTPPort'],
                                        context=ssl.create_default_context()) as server:
                        server.login(data['MailId'], data['MailPassword'])
                        server.quit()
                    if data['IMAPHost'] != "":
                        imp = imaplib.IMAP4_SSL(data['IMAPHost'])
                        imp.login(data['MailId'], data['MailPassword'])
                        imp.logout()
                except Exception as e:
                    print(str(e))
                    raise ConnectionAbortedError(str(e))
                serializer = UserAdminMailConfigurationSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    return HttpResponse(JSONRenderer().render(serializer.data), content_type='application/json',
                                    status=status.HTTP_200_OK)
                return HttpResponse(JSONRenderer().render(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                    status=status.HTTP_417_EXPECTATION_FAILED)

    def get(self, request, *args, **kwargs):
            try:
                data=self.request.headers
                UserId = request.GET.get('User_Id')
                print(UserId)
                mail = UserAdminMailConfiguration.objects.get(User_Id=UserId)
                return HttpResponse(JSONRenderer().render(UserAdminMailConfigurationSerializer(mail).data), content_type='application/json')
            except Exception as e:
                return HttpResponse(JSONRenderer().render({"Error": str(e)}), status=status.HTTP_417_EXPECTATION_FAILED)
    
    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            try:
                with smtplib.SMTP_SSL(
                    data['SMTPHost'],
                    int(data['SMTPPort']),
                    context=ssl.create_default_context()
                ) as server:
                    server.login(data['MailId'], data['MailPassword'])
                    print("SMTP SUCCESS")
                # IMAP Check
                imp = imaplib.IMAP4_SSL(
                    data['IMAPHost'],
                    int(data['IMAPPort'])
                )
                imp.login(data['MailId'], data['MailPassword'])
                imp.logout()
                print("IMAP SUCCESS")
            except Exception as e:
                print("CONFIG ERROR:", str(e))  
                return Response(
                    {"Error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model = UserAdminMailConfiguration.objects.get(id=data['id'])
            serializer = UserAdminMailConfigurationSerializer(model, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"Error": str(e)},
                status=status.HTTP_417_EXPECTATION_FAILED
            )
class MailConfigurationAdditional(ListAPIView):
    queryset = UserAdminMailConfiguration.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get(self, request, *args, **kwargs):
            try:
                db=request.headers
                data= request.query_params
                MailId=data['MailId']
                mail = UserAdminMailConfiguration.objects.get(MailId=MailId)
                return HttpResponse(JSONRenderer().render(UserAdminMailConfigurationSerializer(mail).data), content_type='application/json')
            except Exception as e:
                return HttpResponse(JSONRenderer().render({"Error": str(e)}), status=status.HTTP_417_EXPECTATION_FAILED)



# User Signup 
class SignupUsers(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            html = data['mailhtml'].replace('{{url}}',
                                            'https://backend.crmfarm.in/useradmin/UserReg/?email=' + data['email'] + "&Role=" + data['Designation']+ "&UserType=" +
                                            data['UserType']+ "&Url=" + data['Url'] + "&groups=" + str(data['groups']) + "&Created_by=" + str(data['Created_by']))
            mail = UserAdminMailConfiguration.objects.get(User_Id=data['Created_by'])
            mailserializer = eval(JSONRenderer().render(UserAdminMailConfigurationSerializer(mail).data))
            # if not check_password(data['MailPassword'], mail.MailPassword):
            #     return HttpResponse(JSONRenderer().render({"Error": "Please give the valid Mail Password"}),
            #                         content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            RecevierMailIdVaild = validate_email(data['email'], verify=False)
            if RecevierMailIdVaild:
                response = SendMailUser(subject=data['mailsubject'], From=mailserializer['MailId'], To=data['email'],
                                    Body=html, Host=mailserializer['SMTPHost'], Port=mailserializer['SMTPPort'],
                                    Password=data['MailPassword'])
                if response:
                    return HttpResponse(JSONRenderer().render({"Message": "User is Create Successfully"}),
                                        content_type='application/json', status=status.HTTP_200_OK)
                else:
                    return HttpResponse(JSONRenderer().render({"Message": "User Mail id is not valid"}),
                                        content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            else:
                return HttpResponse(JSONRenderer().render({"Message": "User Mail id is not valid"}),
                                    content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if str(e) == "MailConfiguration matching query does not exist.":
                return HttpResponse(JSONRenderer().render({"Message": "Please Setup Mail First"}),
                                    content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)


# def SendMailUser(subject, From, To, Body, Host, Port, Password):
#     print('SendMailUser')
#     mail = MIMEMultipart('mixed')
#     mail['subject'] = subject
#     mail['From'] = From
#     mail['To'] = To
#     # mail['To'] = ', '.join(To)  # Join multiple recipients with comma and space
#     mail['Disposition-Notification-To'] = From
#     mail['Return-Receipt-To'] = From
#     body = MIMEText(Body, 'html')
#     mail.attach(body)
#     context = ssl.create_default_context()
#     print('SendMailUser 123')
#     print('Host:',Host)
#     print('Port:',Port)
#     print('From:',From)
#     print('Password:',Password)

#     with smtplib.SMTP_SSL(Host, Port, context=context) as server:
#         server.login(From, Password)
#         status = server.sendmail(From, To, mail.as_string())
#         server.close()
#     if status == {}:
#         return True
#     else:
#         return False
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def SendMailUser(subject, From, To, Body, Host, Port, Password):
    mail = MIMEMultipart('mixed')
    mail['subject'] = subject
    mail['From'] = From
    mail['To'] = To
    mail['Disposition-Notification-To'] = From
    mail['Return-Receipt-To'] = From
    body = MIMEText(Body, 'html')
    mail.attach(body)

    context = ssl.create_default_context()

    # Use SMTP and STARTTLS for port 587
    with smtplib.SMTP(Host, Port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(From, Password)
        status = server.sendmail(From, To, mail.as_string())
        server.quit()

    if status == {}:
        return True
    else:
        return False



class SystemPreferenceCRUD(ListAPIView):

    queryset =SystemPreference.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self, request, *args, **kwargs):
        try:
            data = request.data

            data['Created_By'] = UserAdmin.objects.get(id=data['Created_By']).id
            data['Updated_By'] = UserAdmin.objects.get(id=data['Updated_By']).id
            serializer = SystemPreferenceSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output,content_type='application/json',status=status.HTTP_201_CREATED)
            return HttpResponse(JSONRenderer().render(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            # #print(id)
            module = SystemPreference.objects.get(id=id)
            serializer = SystemPreferenceSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            db = request.headers
            id = data.get('id')
            if not id:
                output = JSONRenderer().render({"Error": "id is required"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            try:
                module1 = SystemPreference.objects.get(id=id)
            except SystemPreference.DoesNotExist:
                output = JSONRenderer().render({"Error": "Data not found"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)
            if 'Created_By' in data:
                data['Created_By'] = data['Created_By']
            if 'Updated_By' in data:
                data['Updated_By'] = data['Updated_By']
            if 'Organization_Id' in data:
                data['Organization_Id'] = data['Organization_Id']
            serializer = SystemPreferenceSerializer(module1, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
            return HttpResponse(JSONRenderer().render(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            
    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module1 = SystemPreference.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        

class Sytempreferencegetapi(APIView):
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            module = SystemPreference.objects.filter(Q(Is_Deleted=False)&Q(Created_By=data['Created_By']))
            serializer = SystemPreferenceSerializers(module, many=True)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        

class Sytempreferencelist(ListAPIView):
    queryset=SystemPreference.objects.all()
    serializer_class=SystemPreferenceSerializers
    def get_queryset(self):
        try:                
            data=self.request.query_params
            module = SystemPreference.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")
# CRUD Operation for UserAdmin TicketManagement

# class UserAdminTicketManagementCRUD(ListAPIView):

#     queryset =UserAdminTicketManagement.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]
#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             db=request.headers
#             data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
#             data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
#             l=data["Assignto"]
#             del data['Assignto']
#             module = UserAdminTicketManagement.objects.create(**data)
#             module.Assignto.set(l)
#             module.save()
#             # #print("data",data)
#             output = JSONRenderer().render("created successfully")
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             db=request.headers
#             id = data['id']
#             # #print(id)
#             module = UserAdminTicketManagement.objects.filter(id=id)
#             serializer = UserAdminTicketManagementSerializer(module,many=True)
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             # data = request
#             db=request.headers
#             id=data['id']
#             data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
#             data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
#             l=data["Assignto"]
#             del data['Assignto']
#             modue1=  UserAdminTicketManagement.objects.get(id=id)
#             module = UserAdminTicketManagement.objects.get(id=id)
#             for key,value in data.items():
#                 setattr(module,key,value)
#             module.save()
#             module.Assignto.clear()
#             module.Assignto.set(l)
#             output = JSONRenderer().render("Updated sucessfully")
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, *args, **kwargs):
#         try:
#             db=request.headers
#             data=request.query_params
#             # data = request
#             id = data['id']
#             module1 = UserAdminTicketManagement.objects.get(id=id).delete()
#             output = JSONRenderer().render("Deleted Successfully")
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        
# class UserAdminTicketManagementAdditional(ListAPIView):
#     queryset = UserAdminTicketManagement.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]
#     def get(self, request, *args, **kwargs):
#             try:
#                 db=request.headers
#                 data= request.query_params
#                 mail = UserAdminTicketManagement.objects.all()
#                 return HttpResponse(JSONRenderer().render(UserAdminTicketManagementSerializer(mail,many=True).data), content_type='application/json')
#             except Exception as e:
#                 return HttpResponse(JSONRenderer().render({"Error": str(e)}), status=status.HTTP_417_EXPECTATION_FAILED)
            


# # SuperAdmin Ticket CRUD Operation

# class SuperAdminTicketManagementCRUD(ListAPIView):

#     queryset =SuperAdminTicketManagement.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]
#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             db=request.headers
#             data['Ticket_Id'] = 'STA' + str(ID(SuperAdminTicketManagement,SuperAdminTicketManagementSerializer,db['db'],'Ticket_Id'))
#             data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
#             data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
#             # #print("data",data)
#             module = SuperAdminTicketManagement.objects.create(**data)
#             output = JSONRenderer().render("created successfully")
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             db=request.headers
#             id = data['id']
#             # #print(id)
#             module = SuperAdminTicketManagement.objects.get(id=id)
#             serializer = SuperAdminTicketManagementSerializer(module)
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             # data = request
#             db=request.headers
#             id=data['id']
#             data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
#             data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
#             modue1=  SuperAdminTicketManagement.objects.get(id=id)
#             module = SuperAdminTicketManagement.objects.filter(id=id).update(**data)
#             output = JSONRenderer().render("Updated sucessfully")
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, *args, **kwargs):
#         try:
#             db=request.headers
#             data=request.query_params
#             # data = request
#             id = data['id']
#             module1 = SuperAdminTicketManagement.objects.get(id=id).delete()
#             output = JSONRenderer().render("Deleted Successfully")
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# class SuperAdminTicketManagementAdditional(ListAPIView):
#     queryset = SuperAdminTicketManagement.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get(self, request, *args, **kwargs):
#             try:
#                 db=request.headers
#                 data= request.query_params
#                 mail = SuperAdminTicketManagement.objects.all()
#                 return HttpResponse(JSONRenderer().render(SuperAdminTicketManagementSerializer(mail,many=True).data), content_type='application/json')
#             except Exception as e:
#                 return HttpResponse(JSONRenderer().render({"Error": str(e)}), status=status.HTTP_417_EXPECTATION_FAILED)


# #UserAdmin Ticket Status CRUD Operation

# class TicketStatusCRUD(ListAPIView):

#     queryset =TicketStatus.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]
#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             db=request.headers
#             data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
#             data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
#             l=data["Assignto"]
#             del data['Assignto']
#             module = TicketStatus.objects.create(**data)
#             module.TicketStatus.set(l)
#             module.save()
#             # #print("data",data)
#             output = JSONRenderer().render("created successfully")
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             db=request.headers
#             id = data['id']
#             # #print(id)
#             module = TicketStatus.objects.get(id=id)
#             serializer = TicketStatusSerializer(module)
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             # data = request
#             db=request.headers
#             id=data['id']
#             data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
#             data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
#             l=data["Assignto"]
#             del data['Assignto']
#             modue1=  TicketStatus.objects.get(id=id)
#             module = TicketStatus.objects.get(id=id)
#             for key,value in data.items():
#                 setattr(module,key,value)
#             module.save()
#             module.Assignto.clear()
#             module.Assignto.set(l)
#             output = JSONRenderer().render("Updated sucessfully")
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, *args, **kwargs):
#         try:
#             db=request.headers
#             data=request.query_params
#             # data = request
#             id = data['id']
#             module1 = TicketStatus.objects.get(id=id).delete()
#             output = JSONRenderer().render("Deleted Successfully")
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# class TicketStatusAdditional(ListAPIView):
#     queryset = TicketStatus.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get(self, request, *args, **kwargs):
#             try:
#                 db=request.headers
#                 data= request.query_params
#                 mail = TicketStatus.objects.all()
#                 return HttpResponse(JSONRenderer().render(TicketStatusSerializer(mail,many=True).data), content_type='application/json')
#             except Exception as e:
#                 return HttpResponse(JSONRenderer().render({"Error": str(e)}), status=status.HTTP_417_EXPECTATION_FAILED)
            

class UserAdminMailMasterCRUD(ListAPIView):
    queryset = UserAdminMailMaster.objects.all()
    serializer_class = UserAdminMailMasterSerializer
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [DjangoModelPermissions]
    def post(self, request, *args, **kwargs):
        try:
            db=request.headers
            data = request.data
            # #print(data)
            mail = UserAdminMailConfiguration.objects.get(User_Id=data['UserId'])
            serializer = eval(JSONRenderer().render(UserAdminMailConfigurationSerializer(mail).data))
            data['MailConfiguration'] = serializer['id']
            # #print(data['MailConfiguration'])
            data['MailId'] = MailId3()
            To = [data["RecevierMailId"]]  # Create a list with the receiver's email address
            Cc = data["Cc"]
            RecevierMailIdVaild = validate_email(data['RecevierMailId'], verify=False)
            if RecevierMailIdVaild:
                url = 'https://backend.crmfarm.in/media/' + data['file']
                # #print("url",url)
                mail = SendMail(data['MailSubject'], serializer['MailId'],To,Cc,
                                data['MailBody'].replace('{{url}}', url),
                                serializer['SMTPHost'],
                                serializer['SMTPPort'], serializer['MailPassword'])
                module = UserAdminMailMaster.objects.create(
                    MailId=data["MailId"],
                    Organization_Id=Userorganizationmaster.objects.get(id=data['Organization_Id']),
                    MailSubject=data["MailSubject"],
                    MailConfiguration=UserAdminMailConfiguration.objects.get(id=serializer['id']),
                    MailBody=data['MailBody'],
                    file=data['file'],
                    RecevierMailId=data['RecevierMailId']
                )
                # #print("module",module)
                
                if mail:
                    return HttpResponse(JSONRenderer().render({"Message": "Mail send Successfully"}),
                                        content_type='application/json', status=status.HTTP_201_CREATED)
                else:
                    mail = UserAdminMailMaster.objects.get(MailId=data['MailId'])
                    data['MailBouned'] = True
                    return HttpResponse(JSONRenderer().render({"Error": "Mail not Sent"}),
                                        content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            else:
                return HttpResponse(JSONRenderer().render({"Error": "Receiver Mail id is not valid"}),
                                    content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)

    def get(self, request, *args, **kwargs):
        try:
            data=request.query_params
            # data = request
            id=data['id']
            module = UserAdminMailMaster.objects.get(id=id)
            serializer = UserAdminMailMasterSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data

            # 🔍 Get existing record
            obj = UserAdminMailMaster.objects.get(MailId=data['MailId'])
            serializer = UserAdminMailMasterSerializer(obj, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"Message": "Mail Master Updated Successfully", "data": serializer.data},
                    status=status.HTTP_200_OK
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except UserAdminMailMaster.DoesNotExist:
            return Response({"Error": "MailId not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_417_EXPECTATION_FAILED)

#Deal Mail List API
class UserAdminMailMasterListAdditional(ListAPIView):
    queryset = UserAdminMailMaster.objects.all()
    serializer_class = UserAdminMailMasterSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get(self,request,*args,**kwargs):
        try:
            data=request.query_params
            db=request.headers
            module=UserAdminMailMaster.objects.all()
            serialize=UserAdminMailMasterSerializer(module,many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class UserAdminTaskCalendarCRUD(ListAPIView):

    queryset =UserAdminTaskCalendar.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            data['Task_Id'] = 'TSK' + str(ID(UserAdminTaskCalendar,UserAdminTaskCalendarSerializer,db['db'],'Task_Id'))
            print("chekc")
            data['Assign_To']=UserAdmin.objects.get(id= data['Assign_To'])
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            # #print("data",data)
            module = UserAdminTaskCalendar.objects.create(**data)
            output = JSONRenderer().render("created successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            # #print(id)
            module = UserAdminTaskCalendar.objects.get(id=id)
            serializer = UserAdminTaskCalendarSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id=data['id']
            data['Assign_To']=UserAdmin.objects.get(id= data['Assign_To'])
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            modue1=  UserAdminTaskCalendar.objects.get(id=id)
            module = UserAdminTaskCalendar.objects.filter(id=id).update(**data)
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module1 = UserAdminTaskCalendar.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class UserAdminTaskCalendarAdditional(ListAPIView):
    queryset = UserAdminTaskCalendar.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get(self, request, *args, **kwargs):
            try:
                db=request.headers
                data= request.query_params
                mail = UserAdminTaskCalendar.objects.all()
                return HttpResponse(JSONRenderer().render(UserAdminTaskCalendarSerializer(mail,many=True).data), content_type='application/json')
            except Exception as e:
                return HttpResponse(JSONRenderer().render({"Error": str(e)}), status=status.HTTP_417_EXPECTATION_FAILED)
            


class UserAdminTransactionalseriesCRUD(ListAPIView):

    queryset =UserAdminTransactionalseries.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            data['Transactionalseries_Id'] = 'TSK' + str(ID(UserAdminTransactionalseries,UserAdminTransactionalseriesSerializer,db['db'],'Transactionalseries_Id'))
            print("chekc")
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            # #print("data",data)
            module = UserAdminTransactionalseries.objects.create(**data)
            output = JSONRenderer().render("created successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            # #print(id)
            module = UserAdminTransactionalseries.objects.get(id=id)
            serializer =UserAdminTransactionalseriesSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id=data['id']
            data['Created_By'] =UserAdmin.objects.get(id= data['Created_By'])
            data['Updated_By'] =UserAdmin.objects.get(id=data['Updated_By'])
            data['Organization_Id'] = Userorganizationmaster.objects.get(id=data['Organization_Id'])
            modue1=  UserAdminTransactionalseries.objects.get(id=id)
            module = UserAdminTransactionalseries.objects.filter(id=id).update(**data)
            output = JSONRenderer().render("Updated sucessfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module1 = UserAdminTransactionalseries.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        

class UserAdminTransactionalseriesAdditional(ListAPIView):
    
    queryset = UserAdminTransactionalseries.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def get(self, request, *args, **kwargs):
            try:
                db=request.headers
                data= request.query_params
                mail = UserAdminTransactionalseries.objects.all()
                return HttpResponse(JSONRenderer().render(UserAdminTransactionalseriesSerializer(mail,many=True).data), content_type='application/json')
            except Exception as e:
                return HttpResponse(JSONRenderer().render({"Error": str(e)}), status=status.HTTP_417_EXPECTATION_FAILED)
            

class UserAdminMailsendingSpecifiedEvent(ListAPIView):

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db = request.headers
            mail = UserAdminMailConfiguration.objects.get(id=data['id'])
            serializer = eval(JSONRenderer().render(UserAdminMailConfigurationSerializer(mail).data))
            SendMailC(subject=data['subject'], From=serializer['MailId'], To=data['Recipients'], Body=data['body'], Host=serializer['SMTPHost'], Port=serializer['SMTPPort'], Password=serializer['MailPassword'])
            output = JSONRenderer().render("Sent successfully")
            return HttpResponse(output, content_type='application/json')

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        

class GenerateOTP(APIView):

    def post(self,request,*args,**kwargs):

        try:
            data=request.data
            print("data",data['username'])
            user=User.objects.filter(username=data['username'])
            module=Userserializer(user,many=True)
            output=JSONRenderer().render(module.data)
            output1=json.loads(output)
            mail=output1[0]['email']
            print("output1[0]['id']",output1[0]['id'])
            mail = UserMailConfiguration.objects.get(id=1)
            mailserializer = eval(JSONRenderer().render(UserMailConfigurationSerializer(mail).data))
            print("mailserializer",mailserializer)
            Mail=SendMailOTP(subject=data["subject"],From=mailserializer['MailId'],To=output1[0]['email'],Body=data['MailContent'],Host=mailserializer['SMTPHost'],Port=mailserializer['SMTPPort'],Password=mailserializer['MailPassword'])
            print("Mail",Mail)
            check=JSONRenderer().render("OTP Sent Successfully")
            return HttpResponse(check,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:
            if str(e) == "MailConfiguration matching query does not exist.":
                return HttpResponse(JSONRenderer().render({"Message": "Please Setup Mail First"}),
                                    content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)
        


# For Invite User 

# @csrf_exempt
# @method_decorator(csrf_exempt, name='dispatch')
# def userupdate(request):
#     try:
#         user = {}
#         print("request1", request.POST.get('user_permissions'))
#         user['Organization_Id'] = request.POST.get('Organization_Id')
#         user['UserType'] = request.POST.get('UserType')
#         user['Url'] = request.POST.get('Url')
#         groups = request.POST.get('groups')
#         print("groups",groups)
#         user_permissions=request.POST.get('user_permissions')
#         print("user_permissions",user_permissions)
#         user['user_permissions']=eval(user_permissions)
#         user['groups'] = eval(groups)
#         user['username'] = request.POST.get('username')
#         user['Created_by'] = request.POST.get('Created_by')
#         user['firstname'] = request.POST.get('firstname')
#         user['last_name'] = request.POST.get('lastname')
#         user['username'] = request.POST.get('username')
#         user['Designation'] = request.POST.get('Designation')
#         user['email'] = request.POST.get('email')
#         user['PhoneNo'] = request.POST.get('phone')
#         user['BuildingHuseNo'] = request.POST.get('HNo')
#         user['Street'] = request.POST.get('Street')
#         user['Area'] = request.POST.get('Area')
#         user['City'] = request.POST.get('City')
#         user['State'] = request.POST.get('State')
#         user['Country'] = request.POST.get('Country')
#         user['is_staff'] = False
#         user['is_active'] = True
#         user['User_Login_Status'] = False
#         print("user",user)
#         print("user_permissions",user_permissions)
#         psw = request.POST.get('psw')
#         pswrepeat = request.POST.get('pswrepeat')
#         if psw == pswrepeat:
#             validate_password(password=psw, user=User)
#             user['password'] = make_password(psw)
#         else:
#             messages.warning(request, 'The Password and Re_type Password are not same')
#             return render(request, 'Register.html', {"user": user})
#         email = User.objects.filter(email__exact=user['email'])
#         if email:
#             messages.warning(request, 'Already a user is created with this mail id')
#             return render(request, 'Register.html', {"user": user})
#         print("check also")
#         print("user",user)
#         serializer = Userserializer(data=user)
#         if serializer.is_valid():
#             serializer.save()
#             print("chekc")
#             return redirect(user['Url'])
#         else:
#             print("serializererror",serializer.errors)
#             for name, error in serializer.errors.items():
#                 messages.warning(request, error[0])
#             return render(request, 'Register.html', {"user": user})
#     except Exception as e:
#         print("exception")
#         errors = e.args[0]
#         if type(errors) == type(''):
#             messages.warning(request, errors)
#             return render(request, 'Register.html', {"user": user})
#         for error in errors:
#             messages.warning(request, error)
#         return render(request, 'Register.html', {"user": user})

# @method_decorator(csrf_exempt, name='dispatch')
# def userupdate(request, *args, **kwargs):
#     try:
#         user = {}
#         print("chekc")
#         user['UserType'] = request.POST.get('UserType')
#         user['Url'] = request.POST.get('Url')
#         groups = request.POST.get('groups')
#         user['groups'] = eval(groups)
#         user['username'] = request.POST.get('username')
#         user['Created_by'] = request.POST.get('Created_by')
#         user['firstname'] = request.POST.get('firstname')
#         user['last_name'] = request.POST.get('lastname')
#         user['username'] = request.POST.get('username')
#         user['Designation'] = request.POST.get('Designation')
#         user['email'] = request.POST.get('email')
#         user['User_emailId'] = request.POST.get('email')
#         user['PhoneNo'] = request.POST.get('phone')
#         user['BuildingHuseNo'] = request.POST.get('HNo')
#         user['Street'] = request.POST.get('Street')
#         user['Area'] = request.POST.get('Area')
#         user['City'] = request.POST.get('City')
#         user['State'] = request.POST.get('State')
#         user['Country'] = request.POST.get('Country')
#         user['is_staff'] = False
#         user['is_active'] = True
#         user['User_Login_Status'] = False
#         psw = request.POST.get('psw')
#         pswrepeat = request.POST.get('pswrepeat')
#         print("check1")
#         if psw == pswrepeat:
#             validate_password(password=psw, user=User)
#             user['password'] = make_password(psw)
#         else:
#             messages.warning(request, 'The Password and Re_type Password are not same')
#             return render(request, 'Register.html', {"user": user})
#         email = UserAdmin.objects.filter(email__exact=user['email'])
#         if email:
#             messages.warning(request, 'Already a user is created with this mail id')
#             return render(request, 'Register.html', {"user": user})
#         serializer = UserAdmin.objects.create(**user)
#         if serializer:
#             return redirect(user['Url'])
#         else:
#             print("serializererror")
#             return render(request, 'Register.html', {"user": user})
#     except Exception as e:
#         print(str(e))
#         errors = e.args[0]
#         if type(errors) == type(''):
#             messages.warning(request, errors)
#             return render(request, 'Register.html', {"user": user})
#         for error in errors:
#             messages.warning(request, error)
#         return render(request, 'Register.html', {"user": user})


from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core import signing
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import smtplib
import logging
import json

logger = logging.getLogger(__name__)


from urllib.parse import urlencode
import json

from django.core import signing
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from urllib.parse import urlencode
import json

class UserCreate(APIView):

    def post(self, request, *args, **kwargs):

        try:

            data = request.data

            Tenant = get_current_tenant()

            Userorganizationmaster.objects.get(
                id=data['Organization_Id']
            )

            data['username'] = data['email']

            # -----------------------------------
            # Create secure payload
            # -----------------------------------
            invite_payload = {
                "Organization_Id": data['Organization_Id'],
                "email": data['email'],
                "UserType": data['UserType'],
                "Url": data['Url'],
                "groups": data.get('groups', []),
                "user_permissions": data.get('user_permissions', []),
                "Created_by": data['Created_by'],
                "Tenant": Tenant,
                "CounselorCourse": data.get("CounselorCourse", []),
                "Designation": data.get('Designation', ''),
                "role": data.get("role", "User")
            }

            # -----------------------------------
            # Generate signed token
            # -----------------------------------
            token = signing.dumps(
                invite_payload,
                salt="invite-user"
            )
            # -----------------------------------
            # Registration URL
            # -----------------------------------
            # registration_link = (
            #     f"https://backend.crmfarm.app/"
            #     f"{Tenant}/useradmin/UserReg/?token={token}" 
            # )
            frontend_url = data.get("Url")

            registration_link = (
                f"{frontend_url}?token={token}"
            )

            # -----------------------------------
            # Replace URL in mail template
            # -----------------------------------
            html = data['mailhtml'].replace(
                '{{url}}',registration_link
            )

            # -----------------------------------
            # Mail configuration
            # -----------------------------------
            mail = UserMailConfiguration.objects.get(
                User_Id=data['Created_by']
            )

            mailserializer = (
                UserMailConfigurationSerializer(mail).data
            )

            # -----------------------------------
            # Validate receiver email
            # -----------------------------------
            RecevierMailIdVaild = validate_email(
                data['email'],
                verify=False
            )

            if not RecevierMailIdVaild:

                return Response(
                    {"Message": "User Mail id is not valid"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # -----------------------------------
            # Send mail
            # -----------------------------------
            response = SendMailUser(
                subject=data['mailsubject'],
                From=mailserializer['MailId'],
                To=data['email'],
                Body=html,
                Host=mailserializer['SMTPHost'],
                Port=mailserializer['SMTPPort'],
                Password=mailserializer['MailPassword']
            )

            if response:

                return Response(
                    {
                        "Message": "User invitation sent successfully"
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {"Message": "Mail sending failed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:

            if str(e) == (
                "MailConfiguration matching query does not exist."
            ):

                return Response(
                    {"Message": "Please Setup Mail First"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {"Error": str(e)},
                status=status.HTTP_417_EXPECTATION_FAILED
            )
# User Registration View (token decode + render form)
def userreg(request, *args, **kwargs):
    try:
        print("Incoming request for user registration")

        token = request.GET.get('token')

        if not token:
            return HttpResponseBadRequest("Missing token")

        try:
            # ✅ Decode token (valid for 24 hrs)
            data = signing.loads(token, salt="invite-user", max_age=86400)
        except signing.SignatureExpired:
            return HttpResponseBadRequest("Invite link expired")
        except signing.BadSignature:
            return HttpResponseBadRequest("Invalid invite link")

        # ✅ Prepare user data for frontend
        user = {
            "Organization_Id": data['Organization_Id'],
            "email": data['email'],
            "UserType": data['UserType'],
            "Tenant": data.get('Tenant'),
            "Created_by": data['Created_by'],
            "role": data.get("role", "User")
        }
        print("Decoded user data:", user)
        return render(request, 'Register.html', {'user': user})
    except Exception as e:
        print("Error in userreg:", str(e))
        return HttpResponseBadRequest("Something went wrong")


# ✅ User Update View (form submission + user creation)
# def userupdate(request, *args, **kwargs):
#     if request.method != "POST":
#         return HttpResponseNotAllowed(['POST'], "Only POST method is allowed.")
#     user = {}
#     try:
#         print("check")
#         user['UserType']         = request.POST.get('UserType')
#         user['Url']              = request.POST.get('Url')
#         user['username']         = request.POST.get('username')
#         user['first_name']       = request.POST.get('firstname')
#         user['last_name']        = request.POST.get('lastname')
#         user['Designation']      = request.POST.get('Designation')
#         user['email']            = request.POST.get('email')
#         user['PhoneNo']          = request.POST.get('phone')
#         user['BuildingHuseNo']   = request.POST.get('HNo')
#         user['Street']           = request.POST.get('Street')
#         user['Area']             = request.POST.get('Area')
#         user['City']             = request.POST.get('City')
#         user['State']            = request.POST.get('State')
#         user['Country']          = request.POST.get('Country')
#         user['is_staff']         = False
#         user['is_active']        = True
#         user['User_Login_Status'] = False
#         # ✅ Parse groups safely
#         group_ids = []
#         groups = request.POST.get('groups')
#         if groups:
#             try:
#                 group_ids = json.loads(groups)
#             except json.JSONDecodeError:
#                 messages.warning(request, "Invalid format for groups.")
#                 return render(request, 'Register.html', {"user": user})
#         psw = request.POST.get('psw')
#         pswrepeat = request.POST.get('pswrepeat')
#         print("check1")

#         # ✅ Password match check
#         if psw != pswrepeat:
#             messages.warning(request, 'The Password and Re-type Password do not match.')
#             return render(request, 'Register.html', {"user": user})

#         # ✅ Fixed: pass user=None instead of user=User (class)
#         # Passing the model class was causing '' is not a valid function error
#         validate_password(password=psw, user=None)
#         user['password'] = make_password(psw)

#         print("check2")

#         # ✅ Check for existing email (duplicate removed)
#         if UserAdmin.objects.filter(email__exact=user['email']).exists():
#             messages.warning(request, 'A user with this email already exists.')
#             return render(request, 'Register.html', {"user": user})

#         # ✅ Remove non-model fields before create
#         user_data = {k: v for k, v in user.items() if k != 'groups'}
#         print('user_data:...........', user_data)

#         new_user = UserAdmin.objects.create(**user_data)
#         print('group_ids:', group_ids)

#         # ✅ Set the groups after user creation
#         if group_ids:
#             new_user.groups.set(group_ids)
#         else:
#             print("No group_ids provided or group_ids is empty")

#         return JsonResponse({"message": "User registered successfully"}, status=201)
#     except Exception as e:
#         print(str(e))
#         errors = e.args[0]
#         if isinstance(errors, str):
#             messages.warning(request, errors)
#         else:
#             for error in errors:
#                 messages.warning(request, error)
#         return render(request, 'Register.html', {"user": user})

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.http import Http404
import json

class UserUpdate(APIView):

    def post(self, request, *args, **kwargs):
        """
        Create User
        """

        try:

            data = request.data

            user_data = {}

            user_data['UserType'] = data.get('UserType')
            user_data['Url'] = data.get('Url')
            user_data['username'] = data.get('username')
            user_data['first_name'] = data.get('firstname')
            user_data['last_name'] = data.get('lastname')
            user_data['Designation'] = data.get('Designation')
            user_data['email'] = data.get('email')
            user_data['PhoneNo'] = data.get('phone')
            user_data['BuildingHuseNo'] = data.get('HNo')
            user_data['Street'] = data.get('Street')
            user_data['Area'] = data.get('Area')
            user_data['City'] = data.get('City')
            user_data['State'] = data.get('State')
            user_data['Country'] = data.get('Country')

            user_data['is_staff'] = False
            user_data['is_active'] = True
            user_data['User_Login_Status'] = False

            # -----------------------------
            # Groups Parsing
            # -----------------------------
            group_ids = []

            groups = data.get('groups')

            if groups:

                try:

                    if isinstance(groups, str):
                        group_ids = json.loads(groups)
                    else:
                        group_ids = groups

                except json.JSONDecodeError:

                    return Response(
                        {"error": "Invalid format for groups"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # -----------------------------
            # Password Validation
            # -----------------------------
            psw = data.get('psw')
            pswrepeat = data.get('pswrepeat')

            if psw != pswrepeat:

                return Response(
                    {"error": "Password and Re-type Password do not match"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            validate_password(password=psw, user=None)

            user_data['password'] = make_password(psw)

            # -----------------------------
            # Duplicate Email Check
            # -----------------------------
            if UserAdmin.objects.filter(
                email__exact=user_data['email']
            ).exists():

                return Response(
                    {"error": "A user with this email already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # -----------------------------
            # Create User
            # -----------------------------
            new_user = UserAdmin.objects.create(**user_data)

            # -----------------------------
            # Assign Groups
            # -----------------------------
            if group_ids:
                new_user.groups.set(group_ids)

            return Response(
                {
                    "message": "User registered successfully",
                    "user_id": new_user.id
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:

            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request, *args, **kwargs):
        """
        Update User
        """

        try:

            data = request.data

            user_id = data.get('id')

            if not user_id:

                return Response(
                    {"error": "id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = UserAdmin.objects.get(id=user_id)

            except UserAdmin.DoesNotExist:

                raise Http404("User not found")

            # -----------------------------
            # Update Fields
            # -----------------------------
            update_fields = [
                'UserType',
                'Url',
                'username',
                'Designation',
                'email',
                'PhoneNo',
                'Street',
                'Area',
                'City',
                'State',
                'Country'
            ]

            for field in update_fields:

                if field in data:

                    setattr(user, field, data.get(field))

            # firstname → first_name
            if 'firstname' in data:
                user.first_name = data.get('firstname')

            # lastname → last_name
            if 'lastname' in data:
                user.last_name = data.get('lastname')

            # HNo → BuildingHuseNo
            if 'HNo' in data:
                user.BuildingHuseNo = data.get('HNo')

            # -----------------------------
            # Password Update (Optional)
            # -----------------------------
            psw = data.get('psw')
            pswrepeat = data.get('pswrepeat')

            if psw and pswrepeat:

                if psw != pswrepeat:

                    return Response(
                        {"error": "Password mismatch"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                validate_password(password=psw, user=user)

                user.password = make_password(psw)

            # -----------------------------
            # Groups Update
            # -----------------------------
            groups = data.get('groups')

            if groups is not None:

                try:

                    if isinstance(groups, str):
                        group_ids = json.loads(groups)
                    else:
                        group_ids = groups

                    user.groups.set(group_ids)

                except json.JSONDecodeError:

                    return Response(
                        {"error": "Invalid groups format"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            user.save()

            return Response(
                {
                    "message": "User updated successfully",
                    "user_id": user.id
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:

            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
class CallcenterTargetListscrud(ListAPIView):

    queryset = CallcenterTargetList.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serialize = CallcenterTargetListSerializer(data=data)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serialize.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = CallcenterTargetList.objects.get(id=id)
            serialize = CallcenterTargetListSerializer(module)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = CallcenterTargetList.objects.get(id=id)
            serialize = CallcenterTargetListSerializer(instance=module, data=request.data)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serialize.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def delete(self,request,*args,**kwargs):
        try:
            data = request.query_params
            id =data['id']
            module = CallcenterTargetList.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Sucessfully")
            return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        except Exception as e:
            output=JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)


class CallcenterTargetListAdditional(ListAPIView):
    queryset = CallcenterTargetList.objects.all()
    serializer_class =CallcenterTargetListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def get_queryset(self):

        module = CallcenterTargetList.objects.all().order_by('-Created_Date')
        return module

class CallcenterTargetUserbyId(ListAPIView):
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = CallcenterTargetList.objects.get(UserId=id)
            serialize = CallcenterTargetListSerializer(module)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
   
    




# Lead From Social Linkedin 
    

class LicenceRequestMail(ListAPIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db = request.headers
            mail = UserAdminMailConfiguration.objects.get(User_Id=data['UserId'])
            serializer = eval(JSONRenderer().render(UserAdminMailConfigurationSerializer(mail).data))
            SendMailUser(subject=data['MailSubject'], From=data['FromMailId'], To=data['RecevierMailId'], Body=data['MailBody'], Host=serializer['SMTPHost'], Port=serializer['SMTPPort'], Password=data['MailPassword'])
            output = JSONRenderer().render("Sent successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
import pandas as pd
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.db import connection
import zipfile
import os
import tempfile
from psycopg2 import sql
class CancelPlan_DBBackup(ListAPIView):
    def post(self,request,*args,**kwargs):
        try:
            print('CancelPlan_DBBackup')
            # Get the customer's email address from the request (sent from React frontend)
            data=request.data
            customer_email = data['RecevierMailId']
        # Create the backup folder in Django's media folder if it doesn't exist
            backup_folder = os.path.join(settings.MEDIA_ROOT, 'backup')
            os.makedirs(backup_folder, exist_ok=True)
            # Iterate through each table you want to export
            tables = ['Subscriptions', 'Plan']  # Add your table names here
            for table in tables:
                # Query the PostgreSQL table
                with connection.cursor() as cursor:
                    table_identifier = sql.Identifier(table)
                    cursor.execute(sql.SQL("SELECT * FROM {}").format(table_identifier))
                    columns = [col[0] for col in cursor.description]
                    data = cursor.fetchall()
                # Create a DataFrame from the query result
                df = pd.DataFrame(data, columns=columns)
                # Write DataFrame to CSV file in the backup folder
                csv_file_path = os.path.join(backup_folder, f'{table}.csv')
                df.to_csv(csv_file_path, index=False)
                # Create a zip file containing all CSV files
                zip_file_path = os.path.join(settings.MEDIA_ROOT, 'backup.zip')
                with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                    for root, _, files in os.walk(backup_folder):
                        for file in files:
                            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), backup_folder))
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)
        try:
            db=request.headers
            data = request.data
            print("data:")
            print('5867')
            mail = UserAdminMailConfiguration.objects.get(User_Id=data['UserId'])
            print('5869')
            serializer = eval(JSONRenderer().render(UserAdminMailConfigurationSerializer(mail).data))
            print('5871')
            data['MailConfiguration'] = serializer['id']
            # ## print(data['MailConfiguration'])
            print('5874')
            data['MailId'] = MailId3()
            print('5876')
            To = [data["RecevierMailId"]]  # Create a list with the receiver's email address
            print('5878')
            Cc = data["Cc"]
            print('5880')
            RecevierMailIdVaild = validate_email(data['RecevierMailId'], verify=False)
            print('5882')
            if RecevierMailIdVaild:
                print('5884')
                url = 'https://backend.crmfarm.in/media/backup.zip'
                # + data['file']
                # ## print("url",url)
                mail = SendMail(subject=data['mailsubject'], From=serializer['MailId'],To=To, Cc=Cc,
                                Body=data['MailBody'].replace('{{url}}', url),
                                Host=serializer['SMTPHost'],
                                Port=serializer['SMTPPort'], Password=serializer['MailPassword'])
                print('5892')
                if mail:
                    print('5894')
                    return HttpResponse(JSONRenderer().render({"Message": "Mail send Successfully"}),
                                        content_type='application/json', status=status.HTTP_201_CREATED)
                else:
                    print('5898')
                    return HttpResponse(JSONRenderer().render({"Error": "Mail not Sent"}),
                                        content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            else:
                print('5898')
                return HttpResponse(JSONRenderer().render({"Error": "Receiver Mail id is not valid"}),
                                    content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}), content_type='application/json',
                                status=status.HTTP_417_EXPECTATION_FAILED)
        return HttpResponse('Backup created and email sent successfully.')
    
# class RenewalFormData(ListAPIView):
#     def get(self, request, *args, **kwargs):
#             # Retrieve data from Table1 (Subscriptions)
#             table1_data = Subscriptions.objects.all()
#             table1_serializer = Subscriptionserializers(table1_data, many=True).data

#             # Retrieve data from Table2 (Plan)
#             table2_data = Plan.objects.all()
#             table2_serializer = Planserializers(table2_data, many=True).data

#             # Retrieve data from Table2 (Plan)
#             table3_data = Addonsubscription.objects.all()
#             table3_serializer = AddonsubscriptionSerializers(table3_data, many=True).data

#             # Combine the data into a single dictionary
#             combined_data = {
#                 'Subscriptions': table1_serializer,
#                 'Plan': table2_serializer,
#                 'Adddon_Subscription':table3_serializer
#             }

#             # Return the combined data as JSON response
#             return Response(combined_data)
    
# # class subscriptionCRUD(ListAPIView):
  
#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             serializer = Subscriptionserializer(data=data)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        
#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             id = data['Subscription_Id']
#             module = Subscriptions.objects.get(Subscription_Id=id)
#             serializer = Subscriptionfilterserializer(module, many=True)
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    
#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data

#             id = data['Subscription_Id']
#             module = Subscriptions.objects.get(Subscription_Id=id)
#             serializer = Subscriptionserializer(instance=module, data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    
#     def delete(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             # data = request
#             Subscription_Id = data['Subscription_Id']
#             module = Subscriptions.objects.get(Subscription_Id=Subscription_Id).delete()
#             output = JSONRenderer().render("Deleted Successfully")
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        
#     def patch(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:  # Check if data is empty
#                 raise TypeError("Request data cannot be empty")
#             Subscription_Id = data.get('Subscription_Id')
#             module = Subscriptions.objects.get(Subscription_Id=Subscription_Id)
#             serializer = Subscriptionserializer(instance=module, data=data, partial=True)
#             serializer.is_valid(raise_exception=True)  # Raise validation error if serializer is not valid
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except Subscriptions.DoesNotExist:
#             return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
           
# class subscriptionlist(ListAPIView):
#     queryset = Subscriptions.objects.all()
#     serializer_class = Subscriptionserializers
   
#     def get_queryset(self):
#         module = Subscriptions.objects.all()
#         return module

# class subscriptionarchive(ListAPIView):
#     queryset = Subscriptions.objects.all()

#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             id = data['Subscription_Id']
#             module = Subscriptions.objects.get(Subscription_Id=id)
#             serializer = Subscriptionserializer(module, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        
# class subscriptionsearch(ListAPIView):
#     queryset = Subscriptions.objects.all()
   
#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             module = Subscriptions.objects.filter(
#                 Q(Subscription_Id__icontains=data['search']) |
#                     Q(Customer_Id__FirstName__icontains=data['search']),).order_by('-Created_Date')
#             serialize = Subscriptionfilterserializer(module, many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json')
        
# class subscriptionfilter(ListAPIView):
#     queryset = Subscriptions.objects.all()
   
#     def get(self, request, *args, **kwargs):
#         try:
#             Subscription_Id = request.GET.get('Subscription_Id')
#             FirstName =  request.GET.get('FirstName')
#             Created_Date = request.GET.get('Created_Date')
#             print(Created_Date)
#             module = Subscriptions.objects.filter(
#                 Q(Subscription_Id__icontains=Subscription_Id) & Q(Customer_Id__FirstName__icontains=FirstName) &
#                 Q(Created_Date__range=Created_Date),).order_by('-Created_Date')
#             serialize = Subscriptionserializer(module, many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             data1 = {"Subscription_Id__icontains":data['Subscription_Id'],"Customer_Id__FirstName__icontains":data['FirstName'],"Created_Date__range":data['Created_Date']}
#             return requestget(model=Subscriptions, serializer=Subscriptionserializer,data=data1,page=data['page'],Operator='and')
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"Error":str(e)}),content_type='application/json', status=status.HTTP_417_EXPECTATION_FAILED)
        
# class planCRUD(ListAPIView):
#     queryset = Plan.objects.all()
  
#     def post(self, request, *args, **kwargs):
#         try:
#             if request == {}:
#                 raise TypeError
#             serializer = Planserializer(data=request.data)
           
#             print("Plan Model serializer data:",serializer)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json')
#             return HttpResponse(JSONRenderer().render(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             Plan_Id = data['Plan_Id']
#             module = Plan.objects.get(Plan_Id=Plan_Id)
#             serializer = Planserializers(module)
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data
           
#             id = data['id']
#             module = Plan.objects.get(id=id)
#             serializer = Planserializer(module, data=request.data)
            
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json')
#             return HttpResponse(JSONRenderer().render(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#     def delete(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             id = data['id']
#             module = Plan.objects.get(id=id)
#             serializer = Planserializer(module, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        
# class planarchive(ListAPIView):
#     queryset = Plan.objects.all()

#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             id = data['id']
#             module = Plan.objects.get(id=id)
#             serializer = Planserializer(module, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        
# class planlist(ListAPIView):
#     queryset = Plan.objects.all()
#     serializer_class=Planserializer

#     def get_queryset(self):
#         module = Plan.objects.all()
#         return module
        
# class planfilter(ListAPIView):
#     queryset = Plan.objects.all()
   
#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             module = Plan.objects.filter(Plan_Name__icontains=data['Plan_Name'],
#                                          Currency_Type__icontains=data['Currency_Type'])
#             serialize = Planserializer(module, many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json')

# class plansearch(ListAPIView):
#     queryset = Plan.objects.all()
   
#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             module = Plan.objects.filter(Q(Plan_Name__icontains=data['search']) |
#                                          Q(Currency_Type__icontains=data['search']))
#             serialize = Planserializer(module, many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json')

# class AddonsubscriptionCRUD(ListAPIView):
#     queryset = Addonsubscription.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def post(self, request, *args, **kwargs):
#         try:
#             if request == {}:
#                 raise TypeError
#             serializer = AddonsubscriptionSerializer(data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             id = data['Addonsubscriptionid']
#             module = Addonsubscription.objects.get(Addonsubscriptionid=id)
#             serializer = AddonsubscriptionSerializers(module)
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data
          
#             id = data['Addonsubscriptionid']
#             module = Addonsubscription.objects.get(Addonsubscriptionid=id)
#             serializer = AddonsubscriptionSerializer(instance=module, data=data)
#             if serializer.is_valid():
#                 serializer.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             id = data['Addonsubscriptionid']
#             module = Addonsubscription.objects.get(Addonsubscriptionid=id)
#             serializer = AddonsubscriptionSerializer(module, {"Is_Deleted": True}, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json')
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# class Addonsubscriptionlist(ListAPIView):
#     queryset = Addonsubscription.objects.all()
#     serializer_class = AddonsubscriptionSerializers
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         module=Addonsubscription.objects.filter(Is_Deleted=False)
#         return module

# class Addonsubscriptionfilter(ListAPIView):
#     queryset = Addonsubscription.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]


#     def post(self,request,*args,**kwargs):
#         data=request.data
#         data1 = {"Addonsubscriptionname__icontains":data['Addonsubscriptionname'],'Subscriptiondate__range':data['Subscriptiondate'],'Renewaldate__range':data['Renewaldate'],"Is_Deleted":data['Is_Deleted']}
#         return requestget(model=Addonsubscription,serializer=AddonsubscriptionSerializer,data=data1,page=data['page'],Operator='and')

# class Addonsubscriptionsearch(ListAPIView):
#     queryset = Addonsubscription.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get(self,request,*args,**kwargs):
#         data=request.query_params
#         model=Addonsubscription.objects.filter(Q(Addonsubscriptionname__icontains=data['search']),Is_Deleted=False).order_by('Created_Date')
#         serialize = AddonsubscriptionSerializer(model,many=True)
#         output = JSONRenderer().render(serialize.data)
#         return HttpResponse(output,content_type='application/json')

# class AddlicenseRequest(ListAPIView):
#     queryset = UserAddorcancellicense.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def post(self,request,*args,**kwargs):
#         try:
#             data=request.data
#             db = "None"
#             # data['Licensereqid']='LIC' + str(ID(UserAddorcancellicense,UserAddorcancellicenseSerializer,db,'Licensereqid'))
#             data['Licensereqid']=Transaction_Series(data['Organization_Id'],UserAddorcancellicense,"UserAddor_cancellicense","Licensereqid",data['Licensereqid'])

#             serializer = UserAddorcancellicenseSerializer(data=data)
#             print("User add or reduce list serializer:",serializer)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output=JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)


#     def get(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             module = UserAddorcancellicense.objects.get(Licensereqid=data['Licensereqid'])
#             serialize = UserAddorcancellicenseSerializer(module)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)



#     def put(self,request,*args,**kwargs):
#         try:
#             data=request.data
#             db=request.headers
#             # module = Addorcancellicense.objects.get(Licensereqid=data['Licensereqid'])
#             # serialize= AddorcancellicenseSerializer(module,data=request.data)
#             # if serialize.is_valid():
#             #     serialize.save()
#             data['Created_By']=UserAdmin.objects.get(id=data['Created_By'])
#             data['Updated_By']=UserAdmin.objects.get(id=data['Updated_By'])
#             data['OrganizationId']=Userorganizationmaster.objects.get(id=data['OrganizationId'])
#             module = UserAddorcancellicense.objects.filter(Licensereqid=data['Licensereqid']).update(**data)
#             output = JSONRenderer().render("Updated Successfully")
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)

#     def delete(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             db=request.headers
#             module = UserAddorcancellicense.objects.filter(Licensereqid=data['Licensereqid']).update(Is_Deleted=True)
#             output = JSONRenderer().render("Deleted Successfully")
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:  # Check if data is empty
#                 raise TypeError("Request data cannot be empty")
#             id = data.get('id')
#             module = UserAddorcancellicense.objects.get(id=id)
#             serializer = UserAddorcancellicenseSerializer(instance=module, data=data, partial=True)
#             serializer.is_valid(raise_exception=True)  # Raise validation error if serializer is not valid
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except UserAddorcancellicense.DoesNotExist:
#             return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# class UserAddorcancellicenselist(ListAPIView):
#     queryset = UserAddorcancellicense.objects.all()
#     serializer_class = UserAddorcancellicenseSerializers
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         try:
#             queryset = UserAddorcancellicense.objects.filter(Is_Deleted=False).order_by('Created_Date')
#             return queryset
#         except Exception as e:
#             # Log the error for debugging purposes
#             print(f"An error occurred: {str(e)}")
#             # Return an HTTP 500 Internal Server Error response
#             return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class MyuserAddorcancellicenselist(ListAPIView):
#     serializer_class = UserAddorcancellicenseSerializers
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         try:
#             user_id = self.request.query_params.get('UserId')
#             if user_id:
#                 queryset = UserAddorcancellicense.objects.filter(Q(Is_Deleted=False) & Q(Created_By=user_id)).order_by('-Created_Date')
#             else:
#                 queryset = UserAddorcancellicense.objects.none()  # Return an empty queryset if UserId is not provided
#             return queryset
#         except Exception as e:
#             # Log the error for debugging purposes
#             print(f"An error occurred: {str(e)}")
#             # Return an HTTP 500 Internal Server Error response
#             return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class UserAddorcancellicenseSearch(ListAPIView):

#     queryset=UserAddorcancellicense.objects.all()
#     authentication_classes=[JWTAuthentication]
#     permission_classes=[DjangoModelPermissions]
    
#     def get(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             module=UserAddorcancellicense.objects.filter((Q(Licensereqid__icontains=data['search']) |
#                                                             Q(Customer_Id__icontains=data['search']) |
#                                                             Q(Customername__icontains=data['search']) |Q(Planname__icontains=data['search']) |
#                                                             Q(RequestDate__icontains=data['search'])|Q(Requested_By__icontains=data['search']) |
#                                                             Q(Noofusers__icontains=data['search']) | Q(Addorcancel__icontains=data['search']) |
#                                                             Q(Newamount__icontains=data['search']) |Q(Addtionalusers__icontains=data['search']) |
#                                                             Q(RequestDate__icontains=data['search'])|Q(Requested_By__icontains=data['search']) |
#                                                             Q(Effectivedate__icontains=data['search']))&Q(Is_Deleted=False))
            
#             serialize=UserAddorcancellicenseSerializers(module,many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)

#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# class UserAddorcancellicenseFilter(ListAPIView):

#     queryset=UserAddorcancellicense.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]
    
#     def post(self,request,*args,**kwargs):

#         try:
#             data=request.data
#             Created_Date=[data['fromdate'],data['todate']]
#             module=UserAddorcancellicense.objects.filter(Q(Licensereqid__icontains=data['Licensereqid'])&Q(Subscription_Id__Subscription_Id__icontains=data['Subscription_Id'])&Q(Is_Deleted__exact=False)&Q(Created_Date__range=Created_Date)&Q(Created_By=data['Created_By']))
#             serialize=UserAddorcancellicenseSerializers(module,many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# class AddstorageRequest(ListAPIView):
#     queryset = UserAddStorage.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def post(self,request,*args,**kwargs):

#         try:
#             data=request.data
#             db = "None"
#             # data['AddStorageRequestKey']='STR' + str(ID(UserAddStorage,UserAddStorageSerializer,db,'AddStorageRequestKey'))
#             data['AddStorageRequestKey']=Transaction_Series(data['Organization_Id'],UserAddStorage,"User_AddStorage","AddStorageRequestKey",data['AddStorageRequestKey'])

#             serializer = UserAddStorageSerializer(data=data)
#             print("User add or reduce list serializer:",serializer)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output=JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)

#     def get(self,request,*args,**kwargs):
#         try:
#             db=request.headers
#             data=request.query_params
#             module = UserAddStorage.objects.get(AddStorageRequestKey=data['AddStorageRequestKey'])
#             serialize = UserAddStorageSerializer(module)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)

#     def put(self,request,*args,**kwargs):
#         try:
#             data=request.data
#             module = UserAddStorage.objects.get(AddStorageRequestKey=data['AddStorageRequestKey'])
#             print("module:",module)
#             serializer= UserAddStorageSerializer(module,data=request.data)
#             print("serialize:",serializer)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render("Updated  Successfully")
#                 return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)


#     def delete(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             print("data:",data)
#             module = UserAddStorage.objects.filter(AddStorageRequestKey=data['AddStorageRequestKey']).update(Is_Deleted=True)
#             output = JSONRenderer().render("Deleted Successfully")
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)

# class UserAddStoragelist(ListAPIView):
#     queryset = UserAddStorage.objects.all()
#     serializer_class=UserAddStorageSerializers
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         try:
#             module =UserAddStorage.objects.filter(Is_Deleted=False).order_by('Created_Date')
#             return module
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# class MyuserAddStoragelist(ListAPIView):
#     queryset = UserAddStorage.objects.all()
#     serializer_class = UserAddStorageSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         try:
#             data = self.request.query_params
#             queryset = UserAddStorage.objects.filter(Q(Is_Deleted=False) & Q(Created_By=data['UserId'])).order_by('Created_Date')
#             return queryset
#         except Exception as e:
#             # Log the error for debugging purposes
#             print(f"An error occurred: {str(e)}")
#             # Return an HTTP 500 Internal Server Error response
#             return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class AlluserAddStoragelist(ListAPIView):
#     queryset = UserAddStorage.objects.all()
#     serializer_class = UserAddStorageSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         try:
#             data = self.request.query_params
#             queryset = UserAddStorage.objects.filter(Is_Deleted=False).order_by('Created_Date')
#             return queryset
#         except Exception as e:
#             # Log the error for debugging purposes
#             print(f"An error occurred: {str(e)}")
#             # Return an HTTP 500 Internal Server Error response
#             return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class AddstorageSearch(ListAPIView):

#     queryset=UserAddStorage.objects.all()
#     authentication_classes=[JWTAuthentication]
#     permission_classes=[DjangoModelPermissions]
    
#     def get(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             module=UserAddStorage.objects.filter((Q(AddStorageRequestKey__icontains=data['search'])| Q(Customer_Id__icontains=data['search'])| 
#                                                    Q(AllocatedStorage__icontains=data['search'])|Q(StorageRequested__icontains=data['search']) |
#                                                    Q(Storageafter__icontains=data['search']) | Q(Plan_Name__icontains=data['search']) |
#                                                    Q(Invoice_Id__icontains=data['search']) |Q(Additionalstorage__icontains=data['search']))&Q(Is_Deleted=False))
            
#             #  Q(Plan_Id__icontains=data['search']) #|Q(Subscription_Id__icontains=data['search'])                                                
            
#             serialize=UserAddStorageSerializer(module,many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)

#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# class AddstorageFilter(ListAPIView):

#     queryset=UserAddStorage.objects.all()
#     authentication_classes=[JWTAuthentication]
#     permission_classes=[DjangoModelPermissions]
    
#     def post(self,request,*args,**kwargs):

#         try:
#             data=request.data
#             Created_Date=[data['fromdate'],data['todate']]
#             module=UserAddStorage.objects.filter(Q(AddStorageRequestKey__icontains=data['AddStorageRequestKey'])&Q(Subscription_Id__Subscription_Id__icontains=data['Subscription_Id'])&Q(Is_Deleted__exact=False)&Q(Created_Date__range=Created_Date)&Q(Created_By=data['Created_By']))
#             serialize=UserAddStorageSerializers(module,many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# class AddonRequestCRUD(ListAPIView):
#     queryset = AddonRequest.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def post(self,request,*args,**kwargs):
#         try:
#             data=request.data
#             db = "None"
#             # data['AddonRequest_Id']='ADR' + str(ID(AddonRequest,UserAddonRequestSerializer,db,'AddonRequest_Id'))
#             data['AddonRequest_Id']=Transaction_Series(data['Organization_Id'],AddonRequest,"Addon_Request","AddonRequest_Id",data['AddonRequest_Id'])

#             serializer = UserAddonRequestSerializer(data=data)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output=JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)
        
#     def get(self,request,*args,**kwargs):
#         try:
#             db=request.headers
#             data=request.query_params
#             module = AddonRequest.objects.get(id=data['id'])
#             serialize = UserAddonRequestSerializer(module)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)


#     def put(self,request,*args,**kwargs):
#         try:
#             data = request.data
#             db=request.headers
#             AddonRequest_Id=data['AddonRequest_Id']
#             module = AddonRequest.objects.get(AddonRequest_Id=AddonRequest_Id)
#             serialize = UserAddonRequestSerializer(instance=module, data=request.data)
#             if serialize.is_valid():
#                 serialize.save()
#                 output = JSONRenderer().render(serialize.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
#             output = JSONRenderer().render(serialize.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


#     def delete(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             db=request.headers
#             module = AddonRequest.objects.filter(AddonRequest_Id=data['AddonRequest_Id']).update(Is_Deleted=True)
#             output = JSONRenderer().render("Deleted Sucessfully")
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)
        
#     def patch(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:  # Check if data is empty
#                 raise TypeError("Request data cannot be empty")
#             id = data.get('id')
#             module = AddonRequest.objects.get(id=id)
#             serializer = UserAddonRequestSerializer(instance=module, data=data, partial=True)
#             serializer.is_valid(raise_exception=True)  # Raise validation error if serializer is not valid
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except AddonRequest.DoesNotExist:
#             return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# class AddonRequestlist(ListAPIView):
#     queryset = AddonRequest.objects.all()
#     serializer_class = UserAddonRequestSerializers
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         try:
#             queryset = AddonRequest.objects.filter(Is_Deleted=False).order_by('Created_Date')
#             return queryset
#         except Exception as e:
#             # Log the error for debugging purposes
#             print(f"An error occurred: {str(e)}")
#             # Return an HTTP 500 Internal Server Error response
#             return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class MyaddonRequestlist(ListAPIView):
#     queryset = AddonRequest.objects.all()
#     serializer_class = UserAddonRequestSerializers
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         try:
#             data = self.request.query_params
#             queryset = AddonRequest.objects.filter(Q(Is_Deleted=False) & Q(Created_By=data['UserId'])).order_by('Created_Date')
#             return queryset
#         except Exception as e:
#             # Log the error for debugging purposes
#             print(f"An error occurred: {str(e)}")
#             # Return an HTTP 500 Internal Server Error response
#             return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class AddonSearch(ListAPIView):
#     queryset=AddonRequest.objects.all()
#     authentication_classes=[JWTAuthentication]
#     permission_classes=[DjangoModelPermissions]
    
#     def get(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             module=AddonRequest.objects.filter((Q(AddonRequest_Id__icontains=data['search']) |Q(Plan_Name__icontains=data['search'])
#                                                  |Q(Addon_Name__icontains=data['search']) |Q(Requested_By__icontains=data['search'])) 
#                                                  &Q(Is_Deleted=False))# Q(Subscription_Id__icontains=data['search']) 
#             serialize=UserAddonRequestSerializers(module,many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)

#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# class AddonFilter(ListAPIView):

#     queryset=AddonRequest.objects.all()
#     authentication_classes=[JWTAuthentication]
#     permission_classes=[DjangoModelPermissions]
    
#     def post(self,request,*args,**kwargs):

#         try:
#             data=request.data
#             Created_Date=[data['fromdate'],data['todate']]
#             module=AddonRequest.objects.filter(Q(AddonRequest_Id__icontains=data['AddonRequest_Id'])&Q(Subscription_Id__Subscription_Id__icontains=data['Subscription_Id'])&Q(Is_Deleted__exact=False)&Q(Created_Date__range=Created_Date)&Q(Created_By=data['Created_By']))
#             serialize=UserAddonRequestSerializer(module,many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
        
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# class CancelplanCRUD(ListAPIView):
#     queryset = Cancelplan.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def post(self,request,*args,**kwargs):
#         try:
#             data=request.data
#             db=request.headers
#             # serialize=CancelplansSerializer(data=data)
#             # if serialize.is_valid():
#             #     serialize.save()
#             # print("serialize",serialize.data)
#             data['Created_By']=UserAdmin.objects.get(id=data['Created_By'])
#             data['Updated_By']=UserAdmin.objects.get(id=data['Updated_By'])
#             data['OrganizationId']=Userorganizationmaster.objects.get(id=data['OrganizationId'])
            
#             print(data)
#             data['Cancelplan_Id']='CNL' + str(ID(Cancelplan,UserCancelplanSerializer,db['db'],'Cancelplan_Id'))
#             print(data)
#             module = Cancelplan.objects.create(**data)
#             print(module)
#             output = JSONRenderer().render("Created Successfully")
#             return HttpResponse(output,content_type = 'application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output=JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)


#     def get(self,request,*args,**kwargs):
#         try:
#             db=request.headers
#             data=request.query_params
#             module = Cancelplan.objects.get(Cancelplan_Id=data['Cancelplan_Id'])
#             serialize = UserCancelplanSerializer(module)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)



#     def put(self,request,*args,**kwargs):
#         try:
#             data=request.data
#             db=request.headers
#             # module = Cancelplans.objects.get(Cancelplan_Id=data['Cancelplan_Id'])
#             # serialize= CancelplansSerializer(module,data=request.data)
#             # if serialize.is_valid():
#             #     serialize.save()
#             data['Created_By']=UserAdmin.objects.get(id=data['Created_By'])
#             data['Updated_By']=UserAdmin.objects.get(id=data['Updated_By'])
#             data['OrganizationId']=Userorganizationmaster.objects.get(id=data['OrganizationId'])
#             module = Cancelplan.objects.filter(Cancelplan_Id=data['Cancelplan_Id']).update(**data)
#             output = JSONRenderer().render("Updated Successfully")
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)


#     def delete(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             db=request.headers
#             # module = Cancelplans.objects.get(Cancelplan_Id=data['Cancelplan_Id'])
#             # serialize= CancelplansSerializer(module,{"Is_Deleted":True},partial=True)
#             # if serialize.is_valid():
#             #     serialize.save()
#             module = Cancelplan.objects.filter(Cancelplan_Id=data['Cancelplan_Id']).update(Is_Deleted=True)
#             output = JSONRenderer().render("Deleted Successfully")
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)

# class Cancelplanlist(ListAPIView):
#     queryset = Cancelplan.objects.all()
#     serializer_class=UserCancelplanSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         module =Cancelplan.objects.filter(Is_Deleted=False).order_by('Created_Date')
#         return module

# class MyCancelplanlist(ListAPIView):
#     queryset = Cancelplan.objects.all()
#     serializer_class=UserCancelplanSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         data=self.request.GET.get('Created_By')
#         module =Cancelplan.objects.filter(Created_By=data,Is_Deleted=False).order_by('Created_Date')
#         return module

# class UserRenewalRequestCRUD(ListAPIView):
#     queryset = UserRenewalRequest.objects.all()
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def post(self,request,*args,**kwargs):
#         try:
#             data=request.data
#             db=request.headers
#             data['Renewal_Id']=Transaction_Series(data['Organization_Id'],UserRenewal_Request,"UserAddor_cancellicense","Renewal_Id",data['Renewal_Id'])

#             serializer = UserRenewalRequestSerializer(data=data)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output=JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type = 'application/json',status=status.HTTP_400_BAD_REQUEST)


#     def get(self,request,*args,**kwargs):
#         try:
#             db=request.headers
#             data=request.query_params
#             module = UserRenewalRequest.objects.get(Renewal_Id=data['Renewal_Id'])
#             serialize = UserRenewalRequestSerializer(module, many=True)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)



#     def put(self,request,*args,**kwargs):
#         try:
#             data=request.data
#             db=request.headers
#             Renewal_Id = data['Renewal_Id']
#             module = UserAdmin.objects.get(Renewal_Id=Renewal_Id)
#             serializer = UserRenewalRequestSerializer(instance=module, data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)


#     def delete(self,request,*args,**kwargs):
#         try:
#             data=request.query_params
#             db=request.headers
#             module = UserRenewalRequest.objects.filter(Renewal_Id=data['Renewal_Id']).update(Is_Deleted=True)
#             output = JSONRenderer().render("Deleted Successfully")
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error":str(e)})
#             return HttpResponse(output,content_type='application/json',status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:  # Check if data is empty
#                 raise TypeError("Request data cannot be empty")
#             Renewal_Id = data.get('Renewal_Id')
#             module = UserRenewalRequest.objects.get(Renewal_Id=Renewal_Id)
#             serializer = UserRenewalRequestSerializer(instance=module, data=data, partial=True)
#             serializer.is_valid(raise_exception=True)  # Raise validation error if serializer is not valid
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except UserRenewalRequest.DoesNotExist:
#             return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
# class UserRenewalRequestlist(ListAPIView):
#     queryset = UserRenewalRequest.objects.all()
#     serializer_class=UserRenewalRequestSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         module =UserRenewalRequest.objects.filter(Is_Deleted=False).order_by('Created_Date')
#         return module

# class MyUserRenewalRequestlist(ListAPIView):
#     queryset = UserRenewalRequest.objects.all()
#     serializer_class=UserRenewalRequestSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [DjangoModelPermissions]

#     def get_queryset(self):
#         data=self.request.GET.get('Created_By')
#         module =UserRenewalRequest.objects.filter(Created_By=data,Is_Deleted=False).order_by('Created_Date')
#         return module



class ImageattachmentCRUD(ListAPIView):
    queryset = Imageattachment.objects.all()
    serializer_class = ImageattachmentSerialzer
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            # ## print("data",data)
            db=request.headers
            if data['Attachfile'] != '':
                decoded_data = base64.b64decode((data['Attachfile']))
                print("decoded_data",decoded_data)
                data['Attachfile'] = ContentFile(decoded_data, name=data['File_Name'])
                print("data['Attachfile']",data['Attachfile'])
            file = Imageattachment.objects.all().order_by('Attachment_Id').last()
            # ## print("file",file)
            if file != None:
                fileid = int(file.Attachment_Id[5:]) + 1
                data['Attachment_Id'] = "File" + str(fileid).zfill(8)
            else:
                data['Attachment_Id'] = "File" + "00000001"
            serialize = ImageattachmentSerialzer(data=data)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                print("output",output)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serialize.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            id=data['id']
            if data['File'] != '':
                decoded_data = base64.b64decode((data['File']))
                data['File'] = ContentFile(decoded_data, name=data['FileName'])
            module = Imageattachment.objects.get(id=id)
            serialize = ImageattachmentSerialzer(instance=module, data=request.data,partial=True)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serialize.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = Imageattachment.objects.get(id=id)
            serializer = ImageattachmentSerialzers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class Imageattachmentlist(ListAPIView):
    queryset = Imageattachment.objects.all()
    serializer_class = ImageattachmentSerialzer
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [DjangoModelPermissions]
    def get_queryset(self):
        print("Imageattachmentlist running..")
        module=Imageattachment.objects.all()
        return module

class InvoiceTemplateCRUD(ListAPIView):
    queryset = InvoiceTemplate.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = InvoiceTemplateSerialzer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = InvoiceTemplate.objects.get(id=id)
            serializer = InvoiceTemplateSerialzer(module, many=True)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            id = data['id']
            module = InvoiceTemplate.objects.get(id=id)
            serializer = InvoiceTemplateSerialzer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = InvoiceTemplate.objects.get(id=id).delete()
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:  # Check if data is empty
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = InvoiceTemplate.objects.get(id=id)
            serializer = InvoiceTemplateSerialzer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)  # Raise validation error if serializer is not valid
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InvoiceTemplate.DoesNotExist:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class InvoiceTemplatelist(ListAPIView):
    queryset = InvoiceTemplate.objects.all()
    serializer_class = InvoiceTemplateSerialzers
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def get_queryset(self):
        module = InvoiceTemplate.objects.all()
        return module


# Crud Operations for the Contact Notes

class UserTransactionalseriesCRUD(ListAPIView):

    queryset = UserTransactionalseries.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            data['Transactionalseries_Id'] = 'TRS' + str(ID(UserTransactionalseries,UserTransactionalseriesSerializer,db['db'],'Transactionalseries_Id'))
            serialize = UserTransactionalseriesSerializer(data=data)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serialize.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)        
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            headers=request.headers
            id = data['id']
            module = UserTransactionalseries.objects.get(id=id)
            serializer = UserTransactionalseriesSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id=data['id']
            module = UserTransactionalseries.objects.get(id=id)
            serialize = UserTransactionalseriesSerializer(instance=module, data=request.data,partial=True)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serialize.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module1 = UserTransactionalseries.objects.get(id=id)
            module = UserTransactionalseries.objects.filter(id=id).update(Is_Deleted=True)
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# ContactNotes Additional Operation

class UserTransactionalseriesAdditional(ListAPIView):
    queryset=UserTransactionalseries.objects.all()
    serializer_class=UserTransactionalseriesSerializer
    authentication_classes=[JWTAuthentication]
    permission_classes=[DjangoModelPermissions]

    def get_queryset(self):
        data=self.request.headers
        module=UserTransactionalseries.objects.filter(Q(Is_Deleted=False)).order_by('-Created_Date')
        return module

class TransactionbyOrg(ListAPIView):

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            headers=request.headers
            module = UserTransactionalseries.objects.get(Organization_Id=data['Org_Id'])
            serializer = UserTransactionalseriesSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        
 
class UserTransactionalseriesMyAdditional(ListAPIView):
    queryset=UserTransactionalseries.objects.all()
    serializer_class=UserTransactionalseriesSerializer
    authentication_classes=[JWTAuthentication]
    permission_classes=[DjangoModelPermissions]
    def get_queryset(self):
        data=self.request.headers
        module=UserTransactionalseries.objects.filter(Q(Is_Deleted=False)).order_by('-Created_Date')
        return module

class UserTransactionalseriesMyAdditional(ListAPIView):
    queryset=UserTransactionalseries.objects.all()
    serializer_class=UserTransactionalseriesSerializer
    authentication_classes=[JWTAuthentication]
    permission_classes=[DjangoModelPermissions]
    def get_queryset(self):
        data=self.request.headers
        module=UserTransactionalseries.objects.filter(Q(Is_Deleted=False)).order_by('-Created_Date')
        return module
    
class Rolelistwithpagination(APIView):
    def get(self,request,*args,**kwargs):
        data=request.query_params
        module=Group.objects.filter(Is_Deleted=False)
        serialize=GroupSerializer(module,many=True)
        output=JSONRenderer().render(serialize.data)
        return HttpResponse(output,content_type='application/json')
    
class userrolesearch(ListAPIView):
    queryset = Group.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def get_queryset(self):
        data=self.request.GET.get('search')
        module = Group.objects.filter((Q(name__icontains=data) | Q(
                Role_Id__icontains=data))&Q(Is_Deleted=False))
        return module
    
class UserorganizationmasterBankDetailsCRUD(ListAPIView):
    queryset = Userorganizationmaster_BankDetails.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [DjangoModelPermissions]
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            db=request.headers
            serialize = Userorganizationmaster_BankDetailsSerializer(data=data)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serialize.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            db=request.headers
            id = data['id']
            module = Userorganizationmaster_BankDetails.objects.get(id=id)
            serializer = Userorganizationmaster_BankDetailsSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            # data = request
            db=request.headers
            id=data['id']
            module = Userorganizationmaster_BankDetails.objects.get(id=id)
            serialize =Userorganizationmaster_BankDetailsSerializer(instance=module, data=request.data)
            if serialize.is_valid():
                serialize.save()
                output = JSONRenderer().render(serialize.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serialize.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, *args, **kwargs):
        try:
            db=request.headers
            data=request.query_params
            # data = request
            id = data['id']
            module1 = Userorganizationmaster_BankDetails.objects.get(id=id)
            module = Userorganizationmaster_BankDetails.objects.filter(id=id).update(Is_Deleted=True)
            output = JSONRenderer().render("Deleted Successfully")
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def patch(self, request, *args, **kwargs):
        try:
            data=request.data
            id=data['id']
            module=Userorganizationmaster_BankDetails.objects.get(id=id)
            serialize=Userorganizationmaster_BankDetailsSerializer(module,data=data,partial=True)
            if serialize.is_valid():
                serialize.save()
                return HttpResponse(JSONRenderer().render(serialize.data) ,content_type='application/json')
            return HttpResponse(JSONRenderer().render(serialize.errors), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output=JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)

    
##Rolepermission
class RolePermissionCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = RolePermissionSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = RolePermission.objects.get(id=id)
            serializer = RolePermissionSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = RolePermission.objects.get(id=id)
            serializer = RolePermissionSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = RolePermission.objects.get(id=id)
            serializer = RolePermissionSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = RolePermission.objects.get(id=id)
            serializer = RolePermissionSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RolePermission.DoesNotExist:
            return Response({"Error": "RolePermission not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class RolePermissionMyList(ListAPIView):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializers
    def get_queryset(self):
        data = self.request.query_params
        module = RolePermission.objects.filter(Q(Is_Deleted=False) &Q(Created_By=data['Created_By'])).order_by('-id')
        return module



class RolePermissionAlllist(ListAPIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        data1 = {"Is_Deleted": False,"Created_Date__range": data['Created_Date']}
        return requestget(model=RolePermission,serializer=RolePermission_updateSerializer,data=data1,page=data['page'],Operator='and')


class RolePermissionSearch(ListAPIView):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializers
    def get_queryset(self):
        data = self.request.GET.get('search')
        module = RolePermission.objects.filter((Q(Rolepermission_Id__icontains=data) |
                Q(Code__icontains=data) | Q(App_Label__icontains=data) | Q(Model_Name__icontains=data) |  Q(Action__icontains=data)) &Q(Is_Deleted=False))
        return module



class RolePermissionFilter(ListAPIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        data1 = {
            "Rolepermission_Id__icontains": data['Rolepermission_Id'],
            "Code__icontains": data['Code'],
            "App_Label__icontains": data['App_Label'],
            "Model_Name__icontains": data['Model_Name'],
            "Action__icontains": data['Action'],
            "Created_Date__range": data['Created_Date'],
            "Is_Deleted": False
        }

        return requestget(model=RolePermission,
            serializer=RolePermissionSerializers,
            data=data1,
            page=data['page'],
            Operator='and')


import uuid

from user_agents import parse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import authenticate

from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserSession


# class LoginAPI(APIView):

#     def post(self, request, *args, **kwargs):

#         username = request.data.get("username")
#         password = request.data.get("password")

#         user = authenticate(
#             username=username,
#             password=password
#         )

#         if not user:
#             return Response(
#                 {"error": "Invalid credentials"},
#                 status=400
#             )

#         refresh = RefreshToken.for_user(user)

#         access_token = str(refresh.access_token)
#         refresh_token = str(refresh)

#         # DEVICE INFO
#         user_agent_string = request.META.get(
#             'HTTP_USER_AGENT',
#             ''
#         )

#         user_agent = parse(user_agent_string)

#         ip_address = request.META.get(
#             'REMOTE_ADDR'
#         )

#         session_id = str(uuid.uuid4())

#         UserSession.objects.create(
#             user=user,

#             access_token=access_token,
#             refresh_token=refresh_token,

#             session_id=session_id,

#             device_name=user_agent.device.family,

#             browser=user_agent.browser.family,

#             os=user_agent.os.family,

#             ip_address=ip_address,

#             is_logged_in=True
#         )

#         return Response({
#             "access": access_token,
#             "refresh": refresh_token,
#             "session_id": session_id
#         })


class LoginAPI(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CustomTokenObtainPairSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = serializer.validated_data
        # -----------------------------------
        # Authenticated user
        # -----------------------------------
        user = serializer.user
        # -----------------------------------
        # Tokens
        # -----------------------------------
        access_token = response_data["access_token"]

        refresh_token = response_data["refresh_token"]
        # -----------------------------------
        # Device Info
        # -----------------------------------
        user_agent_string = request.META.get(
            'HTTP_USER_AGENT',
            '')
        user_agent = parse(user_agent_string)
        ip_address = request.META.get(
            'REMOTE_ADDR')
        session_id = str(uuid.uuid4())
        # -----------------------------------
        # Create Session
        # -----------------------------------
        UserSession.objects.create(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            session_id=session_id,
            device_name=user_agent.device.family,
            browser=user_agent.browser.family,
            os=user_agent.os.family,
            ip_address=ip_address,
            is_logged_in=True)
        # -----------------------------------
        # Final Response
        # -----------------------------------
        response_data["session_id"] = session_id
        return Response(response_data,status=status.HTTP_200_OK)


from django.utils.timezone import now

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserSession


class LogoutAPI(APIView):
    permission_classes = [IsAuthenticated]    
    def post(self, request, *args, **kwargs):

        try:

            refresh_token = request.data.get("refresh")

            session_id = request.headers.get("Session-Id")

            if not refresh_token:
                return Response(
                    {
                        "status": False,
                        "message": "Refresh token required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            print(request.headers.get("Authorization"))
            if not session_id:
                return Response(
                    {
                        "status": False,
                        "message": "Session-Id required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # BLACKLIST REFRESH TOKEN
            token = RefreshToken(refresh_token)

            token.blacklist()

            # UPDATE SESSION
            session = UserSession.objects.filter(
                session_id=session_id,
                user=request.user,
                is_logged_in=True
            ).first()

            if session:

                session.is_logged_in = False

                session.logout_time = now()

                session.save()

            return Response(
                {
                    "status": True,
                    "message": "Logout successful"
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:

            return Response(
                {
                    "status": False,
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

from rest_framework_simplejwt.views import TokenObtainPairView

# class CustomTokenObtainPairView(TokenObtainPairView):

#     serializer_class = CustomTokenObtainPairSerializer


    

    
