
from CRM.settings import REST_FRAMEWORK
from CRMchat.models import *
from CRMchat.serializer import *
import redis
r = redis.Redis(host="69.30.247.77", port=6379, decode_responses=True)
import os
import re
import ssl
import json
import base64
import random
import string
import zipfile
import smtplib
import imaplib
import tempfile
import datetime as DT
from datetime import datetime, timedelta
from functools import partial
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.threadlocal import get_current_tenant
# =========================
# 2. Third-Party Libraries
# =========================
import requests
from dateutil.relativedelta import relativedelta
from openpyxl import Workbook
from tablib import Dataset
from validate_email import validate_email

# =========================
# 3. Django Imports
# =========================
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.mail import send_mail
from django.core.files.base import ContentFile
from django.db import connections
from django.db.utils import ProgrammingError
from django.db import transaction


from django.db.models import (
    Q, F, Sum, Max, Count,
    Case, When, IntegerField
)

from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password

# =========================
# 4. Django REST Framework
# =========================
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated

# from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

##specific imports
from datetime import date
# =========================
# 5. Project-Specific Imports
# =========================
from CRM.settings import REST_FRAMEWORK

from CRMSuperAdmin.models import *
from CRMSuperAdmin.serializer import *

from CRMUserAdmin.models import *
from CRMUserAdmin.serializer import *

from utils.threadlocal import get_current_tenant
import pandas as pd
import numpy as np
import redis
from psycopg2 import sql
from celery import shared_task
from rest_framework.pagination import PageNumberPagination
class CustomPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100
class ChatRoomCRUD(APIView):

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = ChatRoom_serializer(data=data)

            if serializer.is_valid():
                room = serializer.save()
                tenant = str(get_current_tenant())
                created_by = data.get("created_by") or request.user.id

                #  Notify only creator
                if created_by:
                    payload = {
                        "tenant": tenant,
                        "user_ids": [created_by],
                        "room_id": room.id,
                        "room_type": room.room_type,
                        "room_name": room.name,
                        "event_type": "CHAT_ROOM_CREATED_SELF"
                    }

                    r.publish("notifications", json.dumps(payload))

            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type="application/json", status=status.HTTP_200_OK)

        except Exception as e:
            return HttpResponse(
                JSONRenderer().render({"Error": str(e)}),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )


    def get(self,request,*args,**kwargs):
        try:
            data=request.query_params
            module=ChatRoom.objects.get(id=data['id'])
            serialize=ChatRoom_serializer(module)
            output=JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:
            output=JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,*args,**kwargs):
        try:
            data=request.data
            module=ChatRoom.objects.get(id=data['id'])
            serialize=ChatRoom_serializer(instance=module,data=data)

            if serialize.is_valid():
                room = serialize.save()
                tenant = str(get_current_tenant())
                created_by = data.get("created_by") or request.user.id

                #  Notify only creator
                if created_by:
                    payload = {
                        "tenant": tenant,
                        "user_ids": [created_by],
                        "room_id": room.id,
                        "room_type": room.room_type,
                        "room_name": room.name,
                        "event_type": "CHAT_ROOM_UPDATED"
                    }

                    r.publish("notifications", json.dumps(payload))

            output=JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:
            output=JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)

    def patch(self,request,*args,**kwargs):
        try:
            data=request.data
            module=ChatRoom.objects.get(id=data['id'])
            serialize=ChatRoom_serializer(instance=module,data=data,partial=True)

            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:
            output=JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)


    def delete(self,request,*args,**kwargs):
        try:
            data=request.query_params
            module=ChatRoom.objects.get(id=data['id'])
            module.is_active=False
            module.save()
            serialize=ChatRoom_serializer(module)
            output=JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:
            output=JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)


class ChatRoomSearch(ListAPIView):

    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoom_serializer


    def get_queryset(self):

        try:

            data=self.request.GET.get('search')

            module=ChatRoom.objects.filter(
                Q(name__icontains=data) |
                Q(room_type__icontains=data)
            ).filter(
                Q(is_active=True)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching ChatRoom: {str(e)}")



class ChatRoomListwithPagination(ListAPIView):

    serializer_class = ChatRoom_serializer

    def get_queryset(self):
        try:
            user = self.request.GET.get("user")

            return ChatRoom.objects.filter(participants__user=user,is_active=True).distinct().order_by("-id")

        except Exception:
            return ChatRoom.objects.none()


class ChatParticipantCRUD(APIView):

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = ChatParticipant_serializer(data=data)

            if serializer.is_valid():
                participant = serializer.save()

                tenant = str(get_current_tenant())
                room = participant.room
                user_id = participant.user.id

                payload = {
                    "tenant": tenant,
                    "user_ids": [user_id],
                    "room_id": room.id,
                    "room_type": room.room_type,
                    "room_name": room.name,
                    "event_type": "CHAT_ROOM_JOINED"
                }

                print("Payload", payload)
                r.publish("notifications", json.dumps(payload))

                return HttpResponse(
                    JSONRenderer().render(serializer.data),
                    content_type="application/json",
                    status=status.HTTP_200_OK
                )

            return HttpResponse(
                JSONRenderer().render(serializer.errors),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return HttpResponse(
                JSONRenderer().render({"Error": str(e)}),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            module = ChatParticipant.objects.get(id=data['id'])

            serializer = ChatParticipant_serializer(module)

            return HttpResponse(
                JSONRenderer().render(serializer.data),
                content_type="application/json",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return HttpResponse(
                JSONRenderer().render({"Error": str(e)}),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            module = ChatParticipant.objects.get(id=data['id'])

            old_user_id = module.user.id
            old_room_id = module.room.id

            serializer = ChatParticipant_serializer(instance=module, data=data)

            if serializer.is_valid():
                participant = serializer.save()

                tenant = str(get_current_tenant())

                new_user_id = participant.user.id
                new_room_id = participant.room.id

                payload = {
                    "tenant": tenant,
                    "user_ids": [new_user_id],
                    "room_id": new_room_id,
                    "event_type": "CHAT_ROOM_PARTICIPANT_UPDATED"
                }

                print("Payload", payload)
                r.publish("notifications", json.dumps(payload))

                return HttpResponse(
                    JSONRenderer().render(serializer.data),
                    content_type="application/json",
                    status=status.HTTP_200_OK
                )

            return HttpResponse(
                JSONRenderer().render(serializer.errors),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return HttpResponse(
                JSONRenderer().render({"Error": str(e)}),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            module = ChatParticipant.objects.get(id=data['id'])

            serializer = ChatParticipant_serializer(instance=module, data=data, partial=True)

            if serializer.is_valid():
                participant = serializer.save()

                tenant = str(get_current_tenant())

                payload = {
                    "tenant": tenant,
                    "user_ids": [participant.user.id],
                    "room_id": participant.room.id,
                    "event_type": "CHAT_ROOM_PARTICIPANT_UPDATED"
                }

                r.publish("notifications", json.dumps(payload))

                return HttpResponse(
                    JSONRenderer().render(serializer.data),
                    content_type="application/json",
                    status=status.HTTP_200_OK
                )

            return HttpResponse(
                JSONRenderer().render(serializer.errors),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return HttpResponse(
                JSONRenderer().render({"Error": str(e)}),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            module = ChatParticipant.objects.get(id=data['id'])

            tenant = str(get_current_tenant())
            room = module.room
            user_id = module.user.id

            module.delete()

            payload = {
                "tenant": tenant,
                "user_ids": [user_id],
                "room_id": room.id,
                "event_type": "CHAT_ROOM_LEFT"
            }

            print("Payload", payload)
            r.publish("notifications", json.dumps(payload))

            return HttpResponse(
                JSONRenderer().render({"Message": "Deleted Successfully"}),
                content_type="application/json",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return HttpResponse(
                JSONRenderer().render({"Error": str(e)}),
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )




class ChatParticipantListwithPagination(ListAPIView):

    queryset = ChatParticipant.objects.all()
    serializer_class = ChatParticipant_serializer
    pagination_class = CustomPagination


    def get_queryset(self):

        try:

            room_id=self.request.GET.get('room')

            module=ChatParticipant.objects.filter(
                Q(room=room_id)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching ChatParticipant: {str(e)}")

class ChatParticipantSearch(ListAPIView):

    queryset=ChatParticipant.objects.all()
    serializer_class = ChatParticipant_serializer


    def get_queryset(self):

        try:

            search=self.request.GET.get('search')

            module=ChatParticipant.objects.filter(
                Q(user__username__icontains=search) |
                Q(room__name__icontains=search)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching ChatParticipant: {str(e)}")



class MessageCRUD(APIView):

    def post(self, request, *args, **kwargs):
        try:
            data = request.data

            if "is_typing" in data:
                room_id = data.get("room")
                sender_id = data.get("sender")
                is_typing = data.get("is_typing")

                room = ChatRoom.objects.get(id=room_id)
                tenant = str(get_current_tenant())

                sender = User.objects.get(id=sender_id)

                # PRIVATE CHAT
                if room.room_type == "private":
                    participants = ChatParticipant.objects.filter(room=room)
                    receiver_ids = [
                        p.user.id for p in participants if p.user.id != sender_id
                    ]

                    payload = {
                        "tenant": tenant,
                        "user_ids": receiver_ids,
                        "room_id": room.id,
                        "sender": sender_id,
                        "sender_name": sender.username,
                        "is_typing": is_typing,
                        "event_type": "TYPING"
                    }

                    r.publish("notifications", json.dumps(payload))

                # GROUP CHAT
                elif room.room_type == "group":
                    user_ids = list(
                        ChatParticipant.objects.filter(room=room)
                        .exclude(user_id=sender_id)
                        .values_list("user_id", flat=True)
                    )

                    payload = {
                        "tenant": tenant,
                        "user_ids": user_ids,
                        "group_id": room.id,
                        "group_name": room.name,
                        "sender": sender_id,
                        "sender_name": sender.username,
                        "is_typing": is_typing,
                        "event_type": "GROUP_TYPING"
                    }

                    r.publish("notifications", json.dumps(payload))

                return HttpResponse(
                    JSONRenderer().render({"status": "typing event sent"}),
                    content_type="application/json",
                    status=200
                )

            serializer = Message_serializer(data=data)

            if serializer.is_valid():
                task = serializer.save()

                tenant = str(get_current_tenant())

                room = task.room
                sender_id = task.sender.id
                sender_name = task.sender.username
                message_text = task.message

                if room.room_type == "private":
                    participants = ChatParticipant.objects.filter(room=room)
                    receiver_ids = [
                        p.user.id for p in participants if p.user.id != sender_id
                    ]

                    payload = {
                        "tenant": tenant,
                        "user_ids": receiver_ids,
                        "message": message_text,
                        "sender": sender_id,
                        "sender_name": sender_name,
                        "room_id": room.id,
                        "event_type": "DM_MESSAGE"
                    }

                    r.publish("notifications", json.dumps(payload))

                elif room.room_type == "group":
                    user_ids = list(
                        ChatParticipant.objects.filter(room=room)
                        .exclude(user_id=sender_id)
                        .values_list("user_id", flat=True)
                    )

                    payload = {
                        "tenant": tenant,
                        "user_ids": user_ids,
                        "group_id": room.id,
                        "group_name": room.name,
                        "message": message_text,
                        "sender": sender_id,
                        "sender_name": sender_name,
                        "event_type": "GROUP_MESSAGE"
                    }

                    r.publish("notifications", json.dumps(payload))

            return HttpResponse(
                JSONRenderer().render(serializer.data),
                content_type="application/json",
                status=200
            )

        except Exception as e:
            return HttpResponse(
                JSONRenderer().render({"Error": str(e)}),
                content_type="application/json",
                status=400
            )


    def get(self,request,*args,**kwargs):
        try:
            data=request.query_params
            module=Message.objects.get(id=data['id'])
            serialize=Message_serializer(module)
            output=JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:
            output=JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,*args,**kwargs):
        try:
            data=request.data
            module=Message.objects.get(id=data['id'])
            serialize=Message_serializer(instance=module,data=data)
            if serialize.is_valid():
                task = serialize.save()

                tenant = str(get_current_tenant())

                room = task.room
                sender_id = task.sender.id
                sender_name = task.sender.username
                message_text = task.message

                #  PRIVATE CHAT (DM)
                if room.room_type == "private":

                    participants = ChatParticipant.objects.filter(room=room)
                    receiver_ids = [
                        p.user.id for p in participants if p.user.id != sender_id
                    ]
                    print("receiver_ids",receiver_ids)

                    payload = {
                        "tenant": tenant,
                        "user_ids": receiver_ids,   #  ONLY receiver
                        "message": message_text,
                        "sender": sender_id,
                        "sender_name": sender_name,
                        "room_id": room.id,
                        "event_type": "DM_MESSAGE_UPDATED"
                    }
                    print("Payload",payload)

                    r.publish("notifications", json.dumps(payload))

                #  GROUP CHAT
                elif room.room_type == "group":

                    user_ids = list(
                        ChatParticipant.objects.filter(room=room)
                        .exclude(user_id=sender_id)   # optional (avoid sending to sender)
                        .values_list("user_id", flat=True)
                    )


                    payload = {
                        "tenant": tenant,
                        "user_ids": user_ids,   # Group Users
                        "group_id": room.id,
                        "group_name": room.name,
                        "message": message_text,
                        "sender": sender_id,
                        "sender_name": sender_name,
                        "event_type": "GROUP_MESSAGE_UPDATED"
                    }


                    r.publish("notifications", json.dumps(payload))

            output=JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:
            output=JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)

    def patch(self,request,*args,**kwargs):
        try:
            data=request.data
            module=Message.objects.get(id=data['id'])
            serialize=Message_serializer(instance=module,data=data,partial=True)
            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:
            output=JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            module = Message.objects.get(id=data['id'])

            # store before update
            tenant = str(get_current_tenant())
            room = module.room
            sender_id = module.sender.id
            sender_name = module.sender.username

            # Soft Delete
            module.is_deleted_for_everyone = True
            module.save()

            # Private Chat (DM)
            if room.room_type == "private":

                participants = ChatParticipant.objects.filter(room=room)
                receiver_ids = [
                    p.user.id for p in participants if p.user.id != sender_id
                ]

                payload = {
                    "tenant": tenant,
                    "user_ids": receiver_ids,
                    "message_id": module.id,
                    "sender": sender_id,
                    "sender_name": sender_name,
                    "room_id": room.id,
                    "event_type": "DM_MESSAGE_DELETED"
                }

                print("Payload", payload)
                r.publish("notifications", json.dumps(payload))

            # Group Chat 
            elif room.room_type == "group":

                user_ids = list(
                    ChatParticipant.objects.filter(room=room)
                    .exclude(user_id=sender_id)
                    .values_list("user_id", flat=True)
                )

                payload = {
                    "tenant": tenant,
                    "user_ids": user_ids,
                    "group_id": room.id,
                    "group_name": room.name,
                    "message_id": module.id,
                    "sender": sender_id,
                    "sender_name": sender_name,
                    "event_type": "GROUP_MESSAGE_DELETED"
                }

                print("Payload", payload)
                r.publish("notifications", json.dumps(payload))

            serialize = Message_serializer(module)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type="application/json", status=status.HTTP_200_OK)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)


from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.response import Response

class MessageListwithPagination(APIView):

    def get(self, request, *args, **kwargs):
        try:
            room = request.GET.get('room')
            page = int(request.GET.get('page', 1))
            current_user = request.GET.get('user_id')

            if not room or not current_user:
                return Response({
                    "status": False,
                    "message": "room & user_id required"
                }, status=400)

            try:
                room_obj = ChatRoom.objects.only(
                    "id",
                    "room_type"
                ).get(id=room)

                room_type = room_obj.room_type

            except ChatRoom.DoesNotExist:
                return Response({
                    "status": False,
                    "message": "Invalid room"
                }, status=400)

            page_size = 10

            all_ids = list(
                Message.objects.filter(room_id=room)
                .order_by("-created_at")
                .values_list("id", flat=True)
            )

            total_count = len(all_ids)

            start = (page - 1) * page_size
            end = page * page_size

            message_ids = all_ids[start:end]

            deleted_message_ids = MessageVisibility.objects.filter(
                user_id=current_user,
                is_deleted=True,
                message_id__in=message_ids
            ).values_list("message_id", flat=True)

            messages = Message.objects.filter(
                id__in=message_ids
            ).select_related(
                "sender",
                "reply_to",
                "room"
            ).prefetch_related(
                Prefetch(
                    "read_status",
                    queryset=MessageReadStatus.objects.select_related("user")
                ),
                "reactions",
                "room__participants"
            ).order_by("-created_at")

            final_results = []

            for msg_obj in messages:

                if msg_obj.id in deleted_message_ids:
                    continue

                read_status_list = list(msg_obj.read_status.all())

                data = {
                    "id": msg_obj.id,
                    "message_type": msg_obj.message_type,
                    "created_at": msg_obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "room": msg_obj.room.id,
                    "Participant_id": msg_obj.sender.id
                }

                if msg_obj.is_deleted_for_everyone:

                    data["message"] = "This message was deleted"

                else:

                    # TEXT MESSAGE
                    if msg_obj.message_type == "text":

                        data["message"] = msg_obj.message

                    # ATTACHMENT MESSAGE
                    else:

                        # REALTIME SAFE ATTACHMENT FETCH
                        attachment_qs = MessageAttachment.objects.filter(
                            message_id=msg_obj.id
                        )

                        attachments = []

                        for att in attachment_qs:

                            file_url = None

                            try:
                                if att.file:
                                    file_url = request.build_absolute_uri(att.file.url)
                            except:
                                file_url = None

                            attachments.append({
                                "file": file_url,
                                "file_type": att.file_type,
                                "file_size": att.file_size
                            })

                        # ALWAYS RETURN attachments KEY
                        data["attachments"] = attachments

                    # REPLY MESSAGE
                    if msg_obj.reply_to:

                        data["reply_message"] = {
                            "id": msg_obj.reply_to.id,
                            "message": msg_obj.reply_to.message
                        }

                    # REACTIONS
                    reactions = [
                        {
                            "id": r.id,
                            "user_id": r.user.id,
                            "reaction": r.reaction
                        }
                        for r in msg_obj.reactions.all()
                    ]

                    if reactions:
                        data["reactions"] = reactions

                seen_users = []

                if str(msg_obj.sender.id) == str(current_user):

                    seen_users = [
                        s for s in read_status_list
                        if s.is_read and s.user.id != msg_obj.sender.id
                    ]

                    if seen_users:

                        if room_type == "private":

                            data["seen_by"] = [
                                {
                                    "user_id": s.user.id,
                                    "read_at": s.read_at.strftime("%Y-%m-%d %H:%M:%S")
                                    if s.read_at else None
                                }
                                for s in seen_users
                            ]

                        else:

                            data["seen_by"] = [
                                {
                                    "user_id": s.user.id,
                                    "name": s.user.username,
                                    "read_at": s.read_at.strftime("%Y-%m-%d %H:%M:%S")
                                    if s.read_at else None
                                }
                                for s in seen_users
                            ]

                if str(msg_obj.sender.id) == str(current_user):

                    if room_type == "private":

                        is_seen = len(seen_users) > 0

                    else:

                        total_users = msg_obj.room.participants.count() - 1
                        is_seen = len(seen_users) == total_users

                    data["is_seen"] = is_seen

                if room_type == "group":

                    data["Participant_Name"] = msg_obj.sender.username

                    if msg_obj.sender.User_Photo:
                        data["Participant_Photo"] = request.build_absolute_uri(
                            msg_obj.sender.User_Photo.url
                        )

                final_results.append(data)

            final_results = list(reversed(final_results))

            return Response({
                "count": total_count,
                "page": str(page),
                "results": final_results
            })

        except Exception as e:

            return Response({
                "status": False,
                "message": str(e)
            }, status=500)




class CreateGroupParticipant(APIView):

    def post(self, request, *args, **kwargs):
        try:
            users = request.data.get("users", [])
            created_by = request.data.get("created_by")
            name = request.data.get("name", "")
            room_id = request.data.get("room_id")

            # ================= VALIDATION =================
            if not created_by:
                return Response({
                    "status": False,
                    "message": "created_by is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not users:
                return Response({
                    "status": False,
                    "message": "users list is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            #  Ensure creator is included
            users = set(users)
            users.add(created_by)

            # ================= CREATE GROUP =================
            if not room_id:

                if not name:
                    return Response({
                        "status": False,
                        "message": "Group name is required"
                    }, status=status.HTTP_400_BAD_REQUEST)

                with transaction.atomic():

                    room = ChatRoom.objects.create(
                        room_type="group",
                        name=name,
                        created_by_id=created_by
                    )

                    #  Bulk create directly (no loop)
                    ChatParticipant.objects.bulk_create([
                        ChatParticipant(room=room, user_id=user_id)
                        for user_id in users
                    ])

                return Response({
                    "status": True,
                    "message": "Group created successfully",
                    "room_id": room.id
                }, status=status.HTTP_200_OK)

            # ================= ADD USERS TO EXISTING GROUP =================
            else:
                try:
                    room = ChatRoom.objects.only("id").get(
                        id=room_id,
                        room_type="group"
                    )
                except ChatRoom.DoesNotExist:
                    return Response({
                        "status": False,
                        "message": "Group not found"
                    }, status=status.HTTP_400_BAD_REQUEST)

                with transaction.atomic():

                    #  Fetch existing users efficiently
                    existing_users = set(
                        ChatParticipant.objects.filter(room_id=room.id)
                        .values_list("user_id", flat=True)
                    )

                    #  Find only new users
                    new_users = users - existing_users

                    if not new_users:
                        return Response({
                            "status": True,
                            "message": "All users already exist in group",
                            "room_id": room.id
                        }, status=status.HTTP_200_OK)

                    #  Bulk insert (fast)
                    ChatParticipant.objects.bulk_create([
                        ChatParticipant(room_id=room.id, user_id=user_id)
                        for user_id in new_users
                    ])

                return Response({
                    "status": True,
                    "message": "Participants added successfully",
                    "room_id": room.id,
                    "added_users": list(new_users)
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class MessageSearch(ListAPIView):

    queryset=Message.objects.all()
    serializer_class = Message_serializer


    def get_queryset(self):

        try:

            search=self.request.GET.get('search')

            module=Message.objects.filter(
                Q(message__icontains=search) |
                Q(sender__username__icontains=search)
            ).filter(
                Q(is_deleted_for_everyone=False)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching Message: {str(e)}")


class MessageEditHistoryCRUD(APIView):


    def post(self,request,*args,**kwargs):

        try:

            data=request.data

            serialize=MessageEditHistory_serializer(data=data)

            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def get(self,request,*args,**kwargs):

        try:

            data=request.query_params

            module=MessageEditHistory.objects.get(id=data['id'])

            serialize=MessageEditHistory_serializer(module)

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def put(self,request,*args,**kwargs):

        try:

            data=request.data

            module=MessageEditHistory.objects.get(id=data['id'])

            serialize=MessageEditHistory_serializer(instance=module,data=data)

            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def patch(self,request,*args,**kwargs):

        try:

            data=request.data

            module=MessageEditHistory.objects.get(id=data['id'])

            serialize=MessageEditHistory_serializer(instance=module,data=data,partial=True)

            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def delete(self,request,*args,**kwargs):

        try:

            data=request.query_params

            module=MessageEditHistory.objects.get(id=data['id'])

            module.delete()

            output=JSONRenderer().render({"Message":"Deleted Successfully"})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)


class MessageEditHistoryListwithPagination(ListAPIView):

    queryset = MessageEditHistory.objects.all()
    serializer_class = MessageEditHistory_serializer
    pagination_class = CustomPagination


    def get_queryset(self):

        try:

            message_id=self.request.GET.get('message')

            module=MessageEditHistory.objects.filter(
                Q(message=message_id)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching MessageEditHistory: {str(e)}")

class MessageEditHistorySearch(ListAPIView):

    queryset=MessageEditHistory.objects.all()
    serializer_class = MessageEditHistory_serializer


    def get_queryset(self):

        try:

            search=self.request.GET.get('search')

            module=MessageEditHistory.objects.filter(
                Q(old_message__icontains=search)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching MessageEditHistory: {str(e)}")


class MessageAttachmentCRUD(APIView):

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()

            file_data = data.get('file')
            file_name = data.get('file_name')

            #  Base64 Handling
            if file_data and file_name:
                try:
                    decoded_file = base64.b64decode(file_data)
                    data['file'] = ContentFile(decoded_file, name=file_name)
                except Exception:
                    return Response(
                        {"file": "Invalid base64 file data"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                data.pop('file', None)
                data.pop('file_name', None)

            serializer = MessageAttachment_serializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self,request,*args,**kwargs):

        try:

            data=request.query_params

            module=MessageAttachment.objects.get(id=data['id'])

            serialize=MessageAttachment_serializer(module)

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, *args, **kwargs):
        try:
            data = request.data.copy()

            module = MessageAttachment.objects.get(id=data['id'])

            file_data = data.get('file')
            file_name = data.get('file_name')

            #  Base64 Handling for Update
            if file_data and file_name:
                try:
                    decoded_file = base64.b64decode(file_data)
                    data['file'] = ContentFile(decoded_file, name=file_name)
                except Exception:
                    return Response(
                        {"file": "Invalid base64 file data"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                data.pop('file', None)
                data.pop('file_name', None)

            serializer = MessageAttachment_serializer(instance=module, data=data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, *args, **kwargs):
        try:
            data = request.data.copy()

            module = MessageAttachment.objects.get(id=data['id'])

            file_data = data.get('file')
            file_name = data.get('file_name')

            #  Base64 Handling for Partial Update
            if file_data and file_name:
                try:
                    decoded_file = base64.b64decode(file_data)
                    data['file'] = ContentFile(decoded_file, name=file_name)
                except Exception:
                    return Response(
                        {"file": "Invalid base64 file data"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                data.pop('file', None)
                data.pop('file_name', None)

            serializer = MessageAttachment_serializer(
                instance=module,
                data=data,
                partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,*args,**kwargs):

        try:

            data=request.query_params

            module=MessageAttachment.objects.get(id=data['id'])

            module.delete()

            output=JSONRenderer().render({"Message":"Deleted Successfully"})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



class MessageAttachmentListwithPagination(ListAPIView):

    queryset = MessageAttachment.objects.all()
    serializer_class = MessageAttachment_serializer
    pagination_class = CustomPagination


    def get_queryset(self):

        try:

            message_id=self.request.GET.get('message')

            module=MessageAttachment.objects.filter(
                Q(message=message_id)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching MessageAttachment: {str(e)}")

class MessageAttachmentSearch(ListAPIView):

    queryset=MessageAttachment.objects.all()
    serializer_class = MessageAttachment_serializer


    def get_queryset(self):

        try:

            search=self.request.GET.get('search')

            module=MessageAttachment.objects.filter(
                Q(file_type__icontains=search)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching MessageAttachment: {str(e)}")



class MessageReadStatusCRUD(APIView):


    def post(self,request,*args,**kwargs):

        try:

            data=request.data

            serialize=MessageReadStatus_serializer(data=data)

            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def get(self,request,*args,**kwargs):

        try:

            data=request.query_params

            module=MessageReadStatus.objects.get(id=data['id'])

            serialize=MessageReadStatus_serializer(module)

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def put(self,request,*args,**kwargs):

        try:

            data=request.data

            module=MessageReadStatus.objects.get(id=data['id'])

            serialize=MessageReadStatus_serializer(instance=module,data=data)

            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def patch(self,request,*args,**kwargs):

        try:

            data=request.data

            module=MessageReadStatus.objects.get(id=data['id'])

            serialize=MessageReadStatus_serializer(instance=module,data=data,partial=True)

            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def delete(self,request,*args,**kwargs):

        try:

            data=request.query_params

            module=MessageReadStatus.objects.get(id=data['id'])

            module.delete()

            output=JSONRenderer().render({"Message":"Deleted Successfully"})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)

class MessageReadStatusListwithPagination(ListAPIView):

    queryset = MessageReadStatus.objects.all()
    serializer_class = MessageReadStatus_serializer
    pagination_class = CustomPagination


    def get_queryset(self):

        try:

            message_id=self.request.GET.get('message')

            module=MessageReadStatus.objects.filter(
                Q(message=message_id)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching MessageReadStatus: {str(e)}")

class MessageReadStatusSearch(ListAPIView):

    queryset=MessageReadStatus.objects.all()
    serializer_class = MessageReadStatus_serializer


    def get_queryset(self):

        try:

            search=self.request.GET.get('search')

            module=MessageReadStatus.objects.filter(
                Q(user__username__icontains=search)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching MessageReadStatus: {str(e)}")



class MessageVisibilityCRUD(APIView):


    def post(self,request,*args,**kwargs):

        try:

            data=request.data

            serialize=MessageVisibility_serializer(data=data)

            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def get(self,request,*args,**kwargs):

        try:

            data=request.query_params

            module=MessageVisibility.objects.get(id=data['id'])

            serialize=MessageVisibility_serializer(module)

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def put(self,request,*args,**kwargs):

        try:

            data=request.data

            module=MessageVisibility.objects.get(id=data['id'])

            serialize=MessageVisibility_serializer(instance=module,data=data)

            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def patch(self,request,*args,**kwargs):

        try:

            data=request.data

            module=MessageVisibility.objects.get(id=data['id'])

            serialize=MessageVisibility_serializer(instance=module,data=data,partial=True)

            if serialize.is_valid():
                serialize.save()

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)



    def delete(self,request,*args,**kwargs):

        try:

            data=request.query_params

            module=MessageVisibility.objects.get(id=data['id'])

            module.is_deleted=True
            module.save()

            serialize=MessageVisibility_serializer(module)

            output=JSONRenderer().render(serialize.data)

            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)

        except Exception as e:

            output=JSONRenderer().render({"Error":str(e)})

            return HttpResponse(output,content_type="application/json",status=status.HTTP_400_BAD_REQUEST)

class MessageVisibilityListwithPagination(ListAPIView):

    queryset = MessageVisibility.objects.all()
    serializer_class = MessageVisibility_serializer
    pagination_class = CustomPagination


    def get_queryset(self):

        try:

            user=self.request.GET.get('user')

            module=MessageVisibility.objects.filter(
                Q(user=user) &
                Q(is_deleted=False)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching MessageVisibility: {str(e)}")

class MessageVisibilitySearch(ListAPIView):

    queryset=MessageVisibility.objects.all()
    serializer_class = MessageVisibility_serializer


    def get_queryset(self):

        try:

            search=self.request.GET.get('search')

            module=MessageVisibility.objects.filter(
                Q(message__message__icontains=search)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching MessageVisibility: {str(e)}")


class MessageReactionCRUD(APIView):

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = MessageReaction_serializer(data=data)

            if serializer.is_valid():
                task = serializer.save()

                tenant = str(get_current_tenant())

                message = task.message
                room = message.room
                sender_id = task.user.id   # user who reacted
                reaction = task.reaction

                # PRIVATE CHAT (DM)
                if room.room_type == "private":

                    participants = ChatParticipant.objects.filter(room=room)
                    receiver_ids = [
                        p.user.id for p in participants if p.user.id != sender_id
                    ]

                    payload = {
                        "tenant": tenant,
                        "user_ids": receiver_ids,
                        "message_id": message.id,
                        "reaction": reaction,
                        "sender": sender_id,
                        "room_id": room.id,
                        "event_type": "DM_REACTION"
                    }

                    print("Payload", payload)
                    r.publish("notifications", json.dumps(payload))

                # GROUP CHAT
                elif room.room_type == "group":

                    user_ids = list(
                        ChatParticipant.objects.filter(room=room)
                        .exclude(user_id=sender_id)
                        .values_list("user_id", flat=True)
                    )

                    payload = {
                        "tenant": tenant,
                        "user_ids": user_ids,
                        "group_id": room.id,
                        "message_id": message.id,
                        "reaction": reaction,
                        "sender": sender_id,
                        "event_type": "GROUP_REACTION"
                    }

                    print("Payload", payload)
                    r.publish("notifications", json.dumps(payload))

            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type="application/json", status=status.HTTP_200_OK)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            module = MessageReaction.objects.get(id=data['id'])
            serializer = MessageReaction_serializer(module)

            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type="application/json", status=status.HTTP_200_OK)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            module = MessageReaction.objects.get(id=data['id'])

            serializer = MessageReaction_serializer(instance=module, data=data)

            if serializer.is_valid():
                task = serializer.save()

                tenant = str(get_current_tenant())

                message = task.message
                room = message.room
                sender_id = task.user.id
                reaction = task.reaction

                # PRIVATE
                if room.room_type == "private":

                    participants = ChatParticipant.objects.filter(room=room)
                    receiver_ids = [
                        p.user.id for p in participants if p.user.id != sender_id
                    ]

                    payload = {
                        "tenant": tenant,
                        "user_ids": receiver_ids,
                        "message_id": message.id,
                        "reaction": reaction,
                        "sender": sender_id,
                        "room_id": room.id,
                        "event_type": "DM_REACTION_UPDATED"
                    }

                    r.publish("notifications", json.dumps(payload))

                # GROUP
                elif room.room_type == "group":

                    user_ids = list(
                        ChatParticipant.objects.filter(room=room)
                        .exclude(user_id=sender_id)
                        .values_list("user_id", flat=True)
                    )

                    payload = {
                        "tenant": tenant,
                        "user_ids": user_ids,
                        "group_id": room.id,
                        "message_id": message.id,
                        "reaction": reaction,
                        "sender": sender_id,
                        "event_type": "GROUP_REACTION_UPDATED"
                    }

                    r.publish("notifications", json.dumps(payload))

            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type="application/json", status=status.HTTP_200_OK)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            module = MessageReaction.objects.get(id=data['id'])

            serializer = MessageReaction_serializer(instance=module, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()

            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type="application/json", status=status.HTTP_200_OK)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            module = MessageReaction.objects.get(id=data['id'])

            message = module.message
            room = message.room
            sender_id = module.user.id

            module.delete()

            tenant = str(get_current_tenant())

            # PRIVATE
            if room.room_type == "private":

                participants = ChatParticipant.objects.filter(room=room)
                receiver_ids = [
                    p.user.id for p in participants if p.user.id != sender_id
                ]

                payload = {
                    "tenant": tenant,
                    "user_ids": receiver_ids,
                    "message_id": message.id,
                    "sender": sender_id,
                    "room_id": room.id,
                    "event_type": "DM_REACTION_DELETED"
                }

                r.publish("notifications", json.dumps(payload))

            # GROUP
            elif room.room_type == "group":

                user_ids = list(
                    ChatParticipant.objects.filter(room=room)
                    .exclude(user_id=sender_id)
                    .values_list("user_id", flat=True)
                )

                payload = {
                    "tenant": tenant,
                    "user_ids": user_ids,
                    "group_id": room.id,
                    "message_id": message.id,
                    "sender": sender_id,
                    "event_type": "GROUP_REACTION_DELETED"
                }

                r.publish("notifications", json.dumps(payload))

            output = JSONRenderer().render({"Message": "Deleted Successfully"})
            return HttpResponse(output, content_type="application/json", status=status.HTTP_200_OK)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)



class MessageReactionListwithPagination(ListAPIView):

    queryset = MessageReaction.objects.all()
    serializer_class = MessageReaction_serializer
    pagination_class = CustomPagination


    def get_queryset(self):

        try:

            message=self.request.GET.get('message')

            module=MessageReaction.objects.filter(
                Q(message=message)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching MessageReaction: {str(e)}")

class MessageReactionSearch(ListAPIView):

    queryset=MessageReaction.objects.all()
    serializer_class = MessageReaction_serializer


    def get_queryset(self):

        try:

            search=self.request.GET.get('search')

            module=MessageReaction.objects.filter(
                Q(reaction__icontains=search) |
                Q(user__username__icontains=search)
            ).order_by('-id')

            return module

        except Exception as e:

            raise Exception(f"Error while fetching MessageReaction: {str(e)}")

class CheckPrivateRoom(APIView):

    def post(self, request, *args, **kwargs):
        try:
            user1 = request.data.get("participant_1")
            user2 = request.data.get("participant_2")

            if not user1 or not user2:
                return Response({"status": False,"message": "Both participants are required","room_id": None}, status=status.HTTP_400_BAD_REQUEST)

            if user1 == user2:
                return Response({"status": False,"message": "Participants must be different","room_id": None}, status=status.HTTP_400_BAD_REQUEST)

            users = sorted([int(user1), int(user2)])

            rooms = ChatRoom.objects.filter(room_type="private")

            for room in rooms:
                participant_ids = list(room.participants.values_list("user_id", flat=True))

                if sorted(participant_ids) == users:

                    if not room.is_active:
                        room.is_active = True
                        room.save()

                    return Response({"status": True,"message": "Room already exists","room_id": room.id})

            return Response({"status": False,"message": "Room does not exist.","room_id": None})

        except Exception as e:
            return Response({"status": False,"message": str(e),"room_id": None}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserChatList(APIView):

    def get(self, request, *args, **kwargs):
        try:
            user_id = request.GET.get("user_id")
            set_offline = request.GET.get("offline")

            if not user_id:
                return Response({"status": False, "message": "user_id is required"}, status=400)

            user_id = int(user_id)
            tenant = str(get_current_tenant())
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if set_offline == "true":
                r.delete(f"user:{user_id}:online")
                r.set(f"user:{user_id}:last_seen", current_time)

                r.publish("notifications", json.dumps({
                    "tenant": tenant,
                    "user_ids": [],
                    "user_id": user_id,
                    "status": "offline",
                    "event_type": "USER_OFFLINE",
                    "last_seen": current_time
                }))

                return Response({
                    "status": True,
                    "message": "User set to offline",
                    "last_seen": current_time
                })

            # ONLINE
            r.set(f"user:{user_id}:online", 1, ex=60)
            r.delete(f"user:{user_id}:last_seen")

            r.publish("notifications", json.dumps({
                "tenant": tenant,
                "user_ids": [],
                "user_id": user_id,
                "status": "online",
                "event_type": "USER_ONLINE"
            }))

            rooms = ChatRoom.objects.filter(
                participants__user=user_id,
                is_active=True
            ).prefetch_related(
                Prefetch(
                    'participants',
                    queryset=ChatParticipant.objects.select_related('user')
                ),
                Prefetch(
                    'messages',
                    queryset=Message.objects.filter(
                        is_deleted_for_everyone=False
                    ).select_related('sender')
                    .prefetch_related('attachments', 'read_status')
                    .order_by('-created_at')
                )
            ).distinct().order_by("-id")

            final_data = []

            for room in rooms:
                participants = list(room.participants.all())

                participant_ids = [p.user.id for p in participants]

                online_map = {}
                last_seen_map = {}

                for uid in participant_ids:

                    online = bool(r.get(f"user:{uid}:online"))
                    online_map[uid] = online

                    if not online:

                        last_seen = r.get(f"user:{uid}:last_seen")

                        # FIX FOR LOCAL + LIVE SERVER
                        if isinstance(last_seen, bytes):
                            last_seen = last_seen.decode("utf-8")

                        last_seen_map[uid] = last_seen

                if room.room_type == "private":

                    p = next(
                        (x for x in participants if x.user.id != user_id),
                        None
                    )

                    participant_id = p.user.id if p else None
                    participant_name = p.user.username if p else None

                    participant_photo = (
                        p.user.User_Photo.url
                        if p and p.user.User_Photo
                        else None
                    )

                    is_online = online_map.get(participant_id, False)
                    last_seen = last_seen_map.get(participant_id)

                else:

                    participant_list = []

                    for p in participants:

                        participant_list.append({
                            "Participant_id": p.user.id,
                            "Participant_Name": p.user.username,
                            "Participant_Photo": (
                                p.user.User_Photo.url
                                if p.user.User_Photo
                                else None
                            ),
                            "is_online": online_map.get(p.user.id, False),
                            "last_seen": last_seen_map.get(p.user.id)
                        })

                all_messages = list(room.messages.all())

                last_msg = all_messages[0] if all_messages else None

                message_ids = [msg.id for msg in all_messages]

                read_status_qs = MessageReadStatus.objects.filter(
                    message_id__in=message_ids,
                    user_id=user_id
                )

                read_status_map = {
                    rs.message_id: rs.is_read
                    for rs in read_status_qs
                }

                unread_messages = [
                    msg for msg in all_messages
                    if msg.sender_id != user_id and not read_status_map.get(msg.id, False)
                ]

                unread_count = len(unread_messages)

                if unread_count == 0:

                    messages = all_messages[:10][::-1]

                elif unread_count < 10:

                    first_unread_time = unread_messages[0].created_at

                    old_messages = [
                        msg for msg in all_messages
                        if msg.created_at < first_unread_time
                    ][:10 - unread_count]

                    messages = old_messages[::-1] + unread_messages

                else:

                    messages = unread_messages

                message_list = []

                for msg in messages:

                    seen_users = [
                        s for s in msg.read_status.all()
                        if s.is_read and s.user.id != msg.sender.id
                    ]

                    message_data = {
                        "id": msg.id,
                        "Participant_id": msg.sender.id,
                        "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "is_unread": not read_status_map.get(msg.id, False),
                        "message_type": msg.message_type
                    }

                    if msg.message_type == "text":

                        message_data["message"] = msg.message

                    else:

                        message_data["attachments"] = [
                            {
                                "file": att.file.url if att.file else None,
                                "file_type": att.file_type
                            }
                            for att in msg.attachments.all()
                        ]

                    if room.room_type == "group":

                        message_data["Participant_Name"] = msg.sender.username

                        message_data["Participant_Photo"] = (
                            msg.sender.User_Photo.url
                            if msg.sender.User_Photo
                            else None
                        )

                    if msg.sender_id == user_id:

                        if room.room_type == "private":

                            message_data["is_seen"] = len(seen_users) > 0

                        else:

                            total_users = len(participants) - 1

                            message_data["is_seen"] = (
                                len(seen_users) == total_users
                            )

                    if room.room_type == "group" and seen_users:

                        message_data["seen_by"] = [
                            {
                                "user_id": s.user.id,
                                "name": s.user.username,
                                "read_at": (
                                    s.read_at.strftime("%Y-%m-%d %H:%M:%S")
                                    if s.read_at
                                    else None
                                )
                            }
                            for s in seen_users
                        ]

                    message_list.append(message_data)

                last_message = None
                last_time = None

                if last_msg:

                    last_message = (
                        last_msg.message
                        if last_msg.message_type == "text"
                        else "Media"
                    )

                    last_time = last_msg.created_at.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                if room.room_type == "private":

                    final_data.append({
                        "room_id": room.id,
                        "room_type": room.room_type,
                        "Participant_id": participant_id,
                        "Participant_Name": participant_name,
                        "Participant_Photo": participant_photo,
                        "is_online": is_online,
                        "last_seen": last_seen,
                        "last_message": last_message,
                        "last_message_time": last_time,
                        "unread_count": unread_count,
                        "Participant_Conversation": message_list
                    })

                else:

                    final_data.append({
                        "room_id": room.id,
                        "room_type": room.room_type,
                        "room_name": room.name,
                        "Participant_List": participant_list,
                        "last_message": last_message,
                        "last_message_time": last_time,
                        "unread_count": unread_count,
                        "Participant_Conversation": message_list
                    })

            return Response({
                "status": True,
                "data": final_data
            })

        except Exception as e:

            return Response({
                "status": False,
                "error": str(e)
            }, status=500)


# New Code 29/04


class MarkMessagesRead(APIView):

    def post(self, request, *args, **kwargs):
        try:
            room_id = request.data.get("room_id")
            user_id = request.data.get("user_id")

            if not room_id or not user_id:
                return Response({
                    "status": False,
                    "message": "room_id & user_id required"
                }, status=400)

            user_id = int(user_id)
            tenant = str(get_current_tenant())

            #  Get room safely (NOT from queryset)
            try:
                room = ChatRoom.objects.get(id=room_id)
            except ChatRoom.DoesNotExist:
                return Response({
                    "status": False,
                    "message": "Invalid room"
                }, status=400)

            #  Get unread messages
            unread_qs = MessageReadStatus.objects.filter(
                message__room_id=room_id,
                user_id=user_id,
                is_read=False
            )

            message_ids = list(unread_qs.values_list("message_id", flat=True))

            #  If nothing to update → return safely
            if not message_ids:
                return Response({
                    "status": True,
                    "message": "No unread messages"
                })

            #  Update
            unread_qs.update(
                is_read=True,
                read_at=timezone.now()
            )

            # -----------------------------------
            #  PRIVATE CHAT
            # -----------------------------------
            if room.room_type == "private":

                participants = ChatParticipant.objects.filter(room=room)
                sender_ids = [
                    p.user.id for p in participants if p.user.id != user_id
                ]

                payload = {
                    "tenant": tenant,
                    "user_ids": sender_ids,
                    "room_id": int(room_id),
                    "reader_id": user_id,
                    "message_ids": message_ids,
                    "event_type": "MESSAGE_READ"
                }

                r.publish("notifications", json.dumps(payload))

            # -----------------------------------
            # 🔥 GROUP CHAT
            # -----------------------------------
            else:
                sender_ids = list(
                    Message.objects.filter(id__in=message_ids)
                    .values_list("sender_id", flat=True)
                    .distinct()
                )

                payload = {
                    "tenant": tenant,
                    "user_ids": sender_ids,
                    "room_id": int(room_id),
                    "reader_id": user_id,
                    "message_ids": message_ids,
                    "event_type": "GROUP_MESSAGE_READ"
                }

                r.publish("notifications", json.dumps(payload))

            return Response({
                "status": True,
                "message": "Marked as read"
            })

        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=500)


#-----------------------

class ChatNotificationSettingCRUD(APIView):

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()

            file_data = data.get('Notification_Sound')
            file_name = data.get('File_Name')

            if file_data and file_name:
                try:
                    if ',' in file_data:
                        file_data = file_data.split(',')[-1]

                    decoded_file = base64.b64decode(file_data)
                    data['Notification_Sound'] = ContentFile(decoded_file, name=file_name)

                except Exception:
                    return Response(
                        {"Notification_Sound": "Invalid base64 file"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                data.pop('Notification_Sound', None)
                data.pop('File_Name', None)

            serializer = ChatNotificationSetting_serializer(data=data)

            if serializer.is_valid():
                serializer.save()

                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type="application/json", status=201)

            return Response(serializer.errors, status=400)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type="application/json", status=400)


    def get(self,request,*args,**kwargs):
        try:
            data = request.query_params
            module = ChatNotificationSetting.objects.get(id=data['id'])
            serialize = ChatNotificationSetting_serializer(module)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output,content_type="application/json",status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error":str(e)})
            return HttpResponse(output, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, *args, **kwargs):
        try:
            data = request.data.copy()

            id = data.get('id')
            if not id:
                return Response({"Error": "id required"}, status=400)

            module = ChatNotificationSetting.objects.get(id=id)

            file_data = data.get('Notification_Sound')
            file_name = data.get('File_Name')

            #  Base64 Update
            if file_data and file_name:
                try:
                    if ',' in file_data:
                        file_data = file_data.split(',')[-1]

                    decoded_file = base64.b64decode(file_data)
                    data['Notification_Sound'] = ContentFile(decoded_file, name=file_name)

                except Exception:
                    return Response({"Notification_Sound": "Invalid base64 file"},status=status.HTTP_400_BAD_REQUEST)
            else:
                data.pop('Notification_Sound', None)
                data.pop('File_Name', None)

            serializer = ChatNotificationSetting_serializer(instance=module,data=data,partial=True)

            if serializer.is_valid():
                serializer.save()

                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type="application/json", status=200)

            return Response(serializer.errors, status=400)

        except ChatNotificationSetting.DoesNotExist:
            return Response({"Error": "Not found"}, status=404)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type="application/json", status=400)


    def patch(self, request, *args, **kwargs):
        try:
            data = request.data

            module = ChatNotificationSetting.objects.get(id=data['id'])

            serializer = ChatNotificationSetting_serializer(instance=module,data=data,partial=True)

            if serializer.is_valid():
                serializer.save()

                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type="application/json", status=200)

        except Exception as err:
            output = JSONRenderer().render({'Error': str(err)})
            return HttpResponse(output, content_type="application/json", status=400)


    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data.get('id')

            module = ChatNotificationSetting.objects.get(id=id)
            module.delete()

            return HttpResponse(JSONRenderer().render({"message": "Deleted successfully"}),content_type="application/json",status=200)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type="application/json", status=400)



