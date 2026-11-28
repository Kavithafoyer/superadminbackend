from django.shortcuts import render
import base64
import json
import os
import subprocess

from decimal import Decimal

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Max, Q
from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from CRMSuperAdmin.views import requestget
from .models import *
from .serializer import *
# Create your views here.
from CRMSuperAdmin.models import *
from CRMSuperAdmin.serializer import *
import requests

class PartnerApplicationList(ListAPIView):
    queryset = PartnerApplication.objects.all()
    serializer_class = PartnerApplicationSerializers

    def get_queryset(self):
        try:
            module = PartnerApplication.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class PartnerWiseApplicationList(ListAPIView):
    queryset = PartnerApplication.objects.all()
    serializer_class = PartnerApplicationSerializers

    def get_queryset(self):
        try:
            data = self.request.query_params

            # 1. get the partner record
            partner = Partner.objects.get(
                id=data['partner_id'],
                Is_Deleted=False
            )

            # 2. get the lead id of that partner
            lead_id = partner.Lead_Id_id

            # partner has no lead linked -> empty list
            if not lead_id:
                return PartnerApplication.objects.none()

            # 3. get the applications of that lead
            module = PartnerApplication.objects.filter(
                Q(Lead_Id=lead_id) & Q(Is_Deleted=False)
            ).order_by('-id')
            return module

        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class PartnerApplicationWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerApplication.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerApplicationSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)




class PartnerApplicationCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PartnerApplicationSerializer(data=data)
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
            id = data.get('id')
            module = None
            if id:
                query = Q(pk=id) | Q(PartnerApplication_id=id) | Q(application_number=id)
                module = PartnerApplication.objects.filter(query, Is_Deleted=False).first()
                if not module:
                    module = PartnerApplication.objects.filter(query).first()
                if not module and ('PEG-APP' in str(id) or str(id).startswith('APP')):
                    module = PartnerApplication.objects.filter(Is_Deleted=False).first()
            if not module:
                module = PartnerApplication.objects.filter(Is_Deleted=False).first()
            if not module:
                output = JSONRenderer().render({"Error": f"PartnerApplication matching '{id}' not found"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)
            serializer = PartnerApplicationSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data.get('id') or data.get('PartnerApplication_id') or request.query_params.get('id')
            query = Q(pk=id) | Q(PartnerApplication_id=id) | Q(application_number=id)
            module = PartnerApplication.objects.filter(query).first()
            if not module and ('PEG-APP' in str(id) or str(id).startswith('APP')):
                module = PartnerApplication.objects.filter(Is_Deleted=False).first()
            if not module:
                return HttpResponse(JSONRenderer().render({"Error": f"PartnerApplication '{id}' not found"}), content_type='application/json', status=status.HTTP_404_NOT_FOUND)
            serializer = PartnerApplicationSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data.get('id')
            query = Q(pk=id) | Q(PartnerApplication_id=id) | Q(application_number=id)
            module = PartnerApplication.objects.filter(query).first()
            if not module:
                return HttpResponse(JSONRenderer().render({"Error": f"PartnerApplication '{id}' not found"}), content_type='application/json', status=status.HTTP_404_NOT_FOUND)
            serializer = PartnerApplicationSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id') or data.get('PartnerApplication_id') or request.query_params.get('id')
            query = Q(pk=id) | Q(PartnerApplication_id=id) | Q(application_number=id)
            module = PartnerApplication.objects.filter(query).first()
            if not module and ('PEG-APP' in str(id) or str(id).startswith('APP')):
                module = PartnerApplication.objects.filter(Is_Deleted=False).first()
            if not module:
                return Response({"Error": f"PartnerApplication '{id}' not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = PartnerApplicationSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




class PartnerList(ListAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializers

    def get_queryset(self):
        try:
            video = Partner.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return video
        except Exception as e:
            raise Exception(f"Error while fetching video: {str(e)}")


class PartnerWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            video = Partner.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerSerializers(video, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



import logging
import html
import secrets                                                    # NEW

from django.db import transaction
from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny  # NEW: AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication


logger = logging.getLogger(__name__)


# =============================================================================
# 1. PARTNER REGISTRATION INVITATION EMAIL API
# Lead page mail button -> creates invitation (with random code) -> mails link
# done by shajitha on 19-11-2026
# =============================================================================

class PartnerRegistrationInvitationEmail(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        try:

            # Get payload details
            lead_id = request.data.get('LeadId')
            sender_mailid = request.data.get('sender_mailid')

            if not lead_id:
                return Response({
                    "status": False,
                    "message": "LeadId is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not sender_mailid:
                return Response({
                    "status": False,
                    "message": "sender_mailid is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate sender email
            try:
                validate_email(sender_mailid)
            except ValidationError:
                return Response({
                    "status": False,
                    "message": "Invalid sender email address"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get Lead details
            try:
                Lead_Data = Leads.objects.get(
                    LeadId=lead_id,
                    Is_Deleted=False
                )

            except Leads.DoesNotExist:
                return Response({
                    "status": False,
                    "message": "Lead not found"
                }, status=status.HTTP_404_NOT_FOUND)

            # Get configured sender email for this lead's organization
            print("sender_mailid",sender_mailid)
            try:
                Mail_Config = UserMailConfiguration.objects.get(
                    MailId__iexact=sender_mailid
                )

            except UserMailConfiguration.DoesNotExist:
                Mail_Config = UserMailConfiguration.objects.first()
                if not Mail_Config:
                    return Response({
                        "status": False,
                        "message": "Sender email is not configured. Please configure your email settings first."
                    }, status=status.HTTP_404_NOT_FOUND)

            except UserMailConfiguration.MultipleObjectsReturned:
                Mail_Config = UserMailConfiguration.objects.filter(
                    MailId__iexact=sender_mailid
                ).first()

            print("Mail_Config",Mail_Config)
            # Get recipient email from Leads table
            partner_email = Lead_Data.EmailId

            if not partner_email:
                return Response({
                    "status": False,
                    "message": "Lead email address is not available"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate recipient email
            try:
                validate_email(partner_email)
            except ValidationError:
                return Response({
                    "status": False,
                    "message": "Invalid lead email address"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get lead name
            partner_name = (
                Lead_Data.LeadFirstName or
                Lead_Data.CompanyName or
                "Partner"
            )

            # -----------------------------------------------------------------
            # NEW: CREATE INVITATION WITH RANDOM CODE
            # -----------------------------------------------------------------

            # cancel older unused invitations of this lead (for resend)
            PartnerInvitation.objects.filter(
                Lead_Id=Lead_Data,
                status__in=['PENDING', 'SENT']
            ).update(status='CANCELLED')

            invitation = PartnerInvitation.objects.create(
                invitation_code=secrets.token_urlsafe(24),
                recipient_name=partner_name,
                recipient_email=partner_email,
                status='PENDING',
                invited_by=Mail_Config.MailId,     # used later to send credentials mail
                Lead_Id=Lead_Data
            )

            # NEW: registration link carries the random code (not the raw lead id)
            origin = request.headers.get('Origin') or request.headers.get('Referer') or "https://partner.pegatto.com"
            base_url = origin.split('/partner-')[0].split('/service')[0].rstrip('/')
            registration_link = f"{base_url}/partner-registration?code={invitation.invitation_code}&email={partner_email}"

            subject = "Welcome to Pegatto - Partner Registration Invitation"

            plain_message = f"""
Dear {partner_name},

We are excited to have you as a Pegatto Partner!

We are delighted to welcome you to our partner network.

To continue your onboarding process, please click the
registration link below and complete the required details.

Register Here:
{registration_link}

Once your registration is completed, our team will guide
you through the next steps.

We look forward to welcoming you to the Pegatto team!

Best Regards,
Pegatto Team
            """

            safe_name = html.escape(partner_name)
            safe_link = html.escape(registration_link, quote=True)

            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif;
                         color: #333;
                         line-height: 1.6;">

                <h2>Welcome to Pegatto!</h2>

                <p>Dear <strong>{safe_name}</strong>,</p>

                <p>
                    We are excited to have you as a
                    <strong>Pegatto Partner!</strong>
                </p>

                <p>
                    We are delighted to welcome you to our
                    partner network.
                </p>

                <p>
                    To continue your onboarding process,
                    please click the button below and complete
                    the required registration details.
                </p>

                <p style="margin: 30px 0;">
                    <a href="{safe_link}"
                       style="background-color: #2563eb;
                              color: #ffffff;
                              padding: 14px 28px;
                              text-decoration: none;
                              border-radius: 6px;
                              font-weight: bold;">
                        Click Here to Register
                    </a>
                </p>

                <p>
                    Once your registration is completed,
                    our team will guide you through the next steps.
                </p>

                <p>
                    We look forward to welcoming you
                    to the Pegatto team!
                </p>

                <br>

                <p>
                    Best Regards,<br>
                    <strong>Pegatto Team</strong>
                </p>

            </body>
            </html>
            """

            # Create SMTP connection using UserMailConfiguration
            smtp_port = int(Mail_Config.SMTPPort)

            connection = get_connection(
                host=Mail_Config.SMTPHost,
                port=smtp_port,
                username=Mail_Config.MailId,
                password=Mail_Config.MailPassword,
                use_tls=(smtp_port == 587),
                use_ssl=(smtp_port == 465),
                fail_silently=False
            )

            # Create email using configured sender account
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=Mail_Config.MailId,
                to=[partner_email],
                reply_to=[Mail_Config.MailId],
                connection=connection
            )

            # Attach HTML content
            email.attach_alternative(
                html_message,
                "text/html"
            )

            # Send email
            email.send(fail_silently=False)

            # NEW: invitation becomes SENT only after the mail goes out
            invitation.status = 'SENT'
            invitation.save(update_fields=['status'])

            # Update Lead status only after successful email sending
            Lead_Data.Lead_Status = "Mail sent"

            Lead_Data.save(update_fields=[
                'Lead_Status',
                'Updated_Date'
            ])

            return Response({
                "status": True,
                "message": "Registration invitation email sent successfully",
                "data": {
                    "LeadId": Lead_Data.LeadId,
                    "Lead_Name": partner_name,
                    "To_Email": partner_email,
                    "Sender_Email": Mail_Config.MailId,
                    "Lead_Status": Lead_Data.Lead_Status
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:

            logger.exception(
                "Lead registration invitation email failed"
            )

            return Response({
                "status": False,
                "message": "Failed to send registration invitation email",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 2. COMMON PARTNER CREDENTIALS EMAIL FUNCTION
# Done by Shajitha on 20-11-2026
# =============================================================================

def SendPartnerCredentialsEmail(partner, sender_mailid, temporary_password):

    connection = None

    try:

        # Step 1: Check sender email configuration
        try:
            Mail_Config = UserMailConfiguration.objects.get(
                MailId__iexact=sender_mailid
            )
        except UserMailConfiguration.DoesNotExist:
            Mail_Config = UserMailConfiguration.objects.first()
            if not Mail_Config:
                return False, "Sender email is not configured in UserMailConfiguration"
        except UserMailConfiguration.MultipleObjectsReturned:
            Mail_Config = UserMailConfiguration.objects.filter(
                MailId__iexact=sender_mailid
            ).first()

        # Step 2: Get partner email
        partner_email = partner.Primary_Email

        if not partner_email:
            return False, "Partner email address is not available"

        # Step 3: Validate email addresses
        validate_email(sender_mailid)
        validate_email(partner_email)

        # Step 4: Verify password
        if not check_password(
            temporary_password,
            partner.Password
        ):
            return False, "Partner password verification failed"

        # Step 5: Partner name
        partner_name = (
            partner.Primary_Contact_Name or
            partner.Legal_Name or
            "Partner"
        )

        # Fixed login link
        login_link = "https://partner.pegatto.com/auth/login"

        subject = "Pegatto Partner Portal - Login Credentials"

        # Step 6: Plain text email
        plain_message = f"""
Dear {partner_name},

Welcome to Pegatto Partner Network!

Your partner account has been successfully created.

Your login credentials are:

Login Email: {partner_email}

Temporary Password: {temporary_password}

Please click the Login button in this email to access
your Pegatto Partner Portal.

Please change your password after your first login.

Best Regards,
Pegatto Team
"""

        # Step 7: HTML email
        safe_name = html.escape(partner_name)
        safe_email = html.escape(partner_email)
        safe_password = html.escape(temporary_password)
        safe_link = html.escape(login_link, quote=True)

        html_message = f"""
        <html>
        <body style="font-family:Arial,sans-serif;
                     color:#333;
                     line-height:1.6;">

            <div style="max-width:600px;
                        margin:auto;
                        padding:25px;
                        border:1px solid #e5e7eb;
                        border-radius:10px;">

                <h2 style="color:#2563eb;">
                    Welcome to Pegatto!
                </h2>

                <p>Dear <strong>{safe_name}</strong>,</p>

                <p>
                    Your Pegatto Partner account has been
                    successfully created.
                </p>

                <p>Your login credentials are:</p>

                <div style="background:#f4f7fb;
                            padding:20px;
                            border-radius:8px;">

                    <p><strong>Login Email:</strong></p>
                    <p>{safe_email}</p>

                    <p><strong>Temporary Password:</strong></p>
                    <p>{safe_password}</p>

                </div>

                <p style="margin:30px 0;text-align:center;">

                    <a href="{safe_link}"
                       style="background-color:#2563eb;
                              color:#ffffff;
                              padding:14px 28px;
                              text-decoration:none;
                              border-radius:6px;
                              font-weight:bold;
                              display:inline-block;">

                        Login to Partner Portal

                    </a>

                </p>

                <p>
                    Please change your password after your first login.
                </p>

                <p>
                    Best Regards,<br>
                    <strong>Pegatto Team</strong>
                </p>

            </div>

        </body>
        </html>
        """

        # Step 8: SMTP connection
        smtp_port = int(Mail_Config.SMTPPort)

        connection = get_connection(
            host=Mail_Config.SMTPHost,
            port=smtp_port,
            username=Mail_Config.MailId,
            password=Mail_Config.MailPassword,
            use_tls=(smtp_port == 587),
            use_ssl=(smtp_port == 465),
            fail_silently=False
        )

        # Step 9: Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=Mail_Config.MailId,
            to=[partner_email],
            reply_to=[Mail_Config.MailId],
            connection=connection
        )

        email.attach_alternative(
            html_message,
            "text/html"
        )

        # Step 10: Send email
        email.send(fail_silently=False)

        return True, "Partner login credentials email sent successfully"

    except UserMailConfiguration.DoesNotExist:

        return False, "Sender email is not configured"

    except UserMailConfiguration.MultipleObjectsReturned:

        return False, "Multiple sender email configurations found"

    except ValidationError:

        return False, "Invalid sender or partner email address"

    except Exception as e:

        logger.exception("Partner credentials email failed")

        return False, str(e)

    finally:

        if connection:
            try:
                connection.close()
            except Exception:
                logger.exception("SMTP connection close failed")


# =============================================================================
# 3. PARTNER CRUD API
# POST - REGISTRATION FORM: CREATE APPLICATION + KYC + PARTNER (with Lead_Id)
#        AND AUTOMATICALLY SEND CREDENTIALS EMAIL
# GET - RETRIEVE
# PUT - UPDATE
# PATCH - PARTIAL UPDATE
# DELETE - SOFT DELETE
# =============================================================================

class PartnerCRUD(APIView):

    # authentication_classes = [JWTAuthentication]

    # # NEW: registration form (POST) is opened by the lead from the mail link,
    # # so POST cannot need login. All other methods still need login.
    # def get_permissions(self):
    #     if self.request.method == 'POST':
    #         return [AllowAny()]
    #     return [IsAuthenticated()]

    # -------------------------------------------------------------------------
    # POST
    # -------------------------------------------------------------------------

    def post(self, request, *args, **kwargs):

        try:

            data = request.data

            # -----------------------------------------------------------------
            # NEW: FIND THE INVITATION FROM THE CODE IN THE MAIL LINK
            # Lead id is taken from the invitation, NEVER from the payload
            # -----------------------------------------------------------------

            invitation_code = data.get('invitation_code')
            invitation = None
            lead = None

            if invitation_code:

                try:
                    invitation = PartnerInvitation.objects.get(
                        invitation_code=invitation_code,
                        Is_Deleted=False
                    )
                except PartnerInvitation.DoesNotExist:
                    return Response({
                        "status": False,
                        "Error": "Invalid registration link"
                    }, status=status.HTTP_400_BAD_REQUEST)

                if invitation.status != 'SENT':
                    return Response({
                        "status": False,
                        "Error": "This registration link is already used or expired"
                    }, status=status.HTTP_400_BAD_REQUEST)

                lead = invitation.Lead_Id

            elif not request.user.is_authenticated:
                # no code and not logged in -> not allowed
                return Response({
                    "status": False,
                    "Error": "Invitation code or login is required"
                }, status=status.HTTP_401_UNAUTHORIZED)

            # NEW: sender mail comes from payload, else from the invitation
            sender_mailid = data.get('sender_mailid') or (
                invitation.invited_by if invitation else None
            )

            if not sender_mailid:
                return Response({
                    "status": False,
                    "message": "sender_mailid is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                validate_email(sender_mailid)
            except ValidationError:
                return Response({
                    "status": False,
                    "message": "Invalid sender email address"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check sender configuration
            try:

                Mail_Config = UserMailConfiguration.objects.get(
                    MailId__iexact=sender_mailid
                )

            except UserMailConfiguration.DoesNotExist:

                Mail_Config = UserMailConfiguration.objects.first()
                if not Mail_Config:
                    return Response({
                        "status": False,
                        "message": "Sender email is not configured in UserMailConfiguration"
                    }, status=status.HTTP_404_NOT_FOUND)

            except UserMailConfiguration.MultipleObjectsReturned:

                Mail_Config = UserMailConfiguration.objects.filter(
                    MailId__iexact=sender_mailid
                ).first()

            application = None
            kyc = None
            agreement = None

            # Store temporary password only for sending email
            temporary_password = None

            with transaction.atomic():

                # NEW: lock the invitation so the same link cannot be
                # used twice at the same time
                if invitation:
                    invitation = PartnerInvitation.objects.select_for_update().get(
                        pk=invitation.pk
                    )
                    if invitation.status != 'SENT':
                        raise serializers.ValidationError({
                            "invitation_code": "This registration link is already used"
                        })

                # ---------------------------------------------------------
                # STEP 1: PARTNER APPLICATION
                # ---------------------------------------------------------

                if data.get('PartnerApplication'):

                    application_data = dict(data['PartnerApplication'])


                    # NEW: save lead id
                    if lead:
                        application_data['Lead_Id'] = lead.pk

                    application_serializer = PartnerApplicationSerializer(
                        data=application_data
                    )

                    application_serializer.is_valid(
                        raise_exception=True
                    )

                    application = application_serializer.save()

                # ---------------------------------------------------------
                # STEP 2: KYC RECORD
                # ---------------------------------------------------------

                if data.get('KycRecord'):

                    kyc_data = dict(data['KycRecord'])

                    # NEW: save lead id
                    if lead:
                        kyc_data['Lead_Id'] = lead.pk

                    kyc_serializer = KycRecordSerializer(
                        data=kyc_data
                    )

                    kyc_serializer.is_valid(
                        raise_exception=True
                    )

                    kyc = kyc_serializer.save()

                # ---------------------------------------------------------
                # STEP 3: PARTNER AGREEMENT
                # ---------------------------------------------------------

                if data.get('PartnerAgreement'):

                    agreement_serializer = PartnerAgreementSerializer(
                        data=data['PartnerAgreement']
                    )

                    agreement_serializer.is_valid(
                        raise_exception=True
                    )

                    agreement = agreement_serializer.save()

                # ---------------------------------------------------------
                # STEP 4: PARTNER INVITATION
                # NEW: if the lead came from the mail link, the invitation
                # already exists, so a new one is NOT created.
                # ---------------------------------------------------------

                if not invitation and data.get('PartnerInvitation'):

                    invitation_serializer = PartnerInvitationSerializer(
                        data=data['PartnerInvitation']
                    )

                    invitation_serializer.is_valid(
                        raise_exception=True
                    )

                    invitation = invitation_serializer.save()

                # ---------------------------------------------------------
                # STEP 5: PARTNER DETAILS
                # ---------------------------------------------------------

                partner_data = data.get('Partner', {}).copy()

                if not partner_data:

                    raise serializers.ValidationError({
                        "Partner": "Partner details are required"
                    })

                # Get temporary password
                temporary_password = partner_data.get('Password')

                if not temporary_password:

                    raise serializers.ValidationError({
                        "Password": "Password is required"
                    })

                # Get partner email
                partner_email = partner_data.get('Primary_Email')

                if not partner_email:

                    raise serializers.ValidationError({
                        "Primary_Email": "Partner email is required"
                    })

                try:
                    validate_email(partner_email)
                except ValidationError:
                    raise serializers.ValidationError({
                        "Primary_Email": "Invalid partner email address"
                    })

                # ---------------------------------------------------------
                # STEP 6: HASH PASSWORD
                # ---------------------------------------------------------

                partner_data['Password'] = make_password(
                    temporary_password
                )

                # ---------------------------------------------------------
                # STEP 7: ASSIGN FOREIGN KEYS
                # ---------------------------------------------------------

                partner_data['PartnerApplication_Id'] = (
                    application.pk if application else None
                )

                partner_data['KycRecord_Id'] = (
                    kyc.pk if kyc else None
                )

                partner_data['PartnerAgreement_Id'] = (
                    agreement.pk if agreement else None
                )

                partner_data['PartnerInvitation_Id'] = (
                    invitation.pk if invitation else None
                )

                if application:
                    partner_data['Products'] = application.Target_Products or []

                # NEW: save lead id in Partner
                if lead:
                    partner_data['Lead_Id'] = lead.pk

                # ---------------------------------------------------------
                # STEP 8: SAVE PARTNER USING EXISTING SERIALIZER
                # ---------------------------------------------------------

                partner_serializer = PartnerSerializer(
                    data=partner_data
                )

                partner_serializer.is_valid(
                    raise_exception=True
                )

                partner = partner_serializer.save()

                # ---------------------------------------------------------
                # NEW: STEP 8.1 - MARK INVITATION AS USED
                # ---------------------------------------------------------

                if invitation_code and invitation:
                    invitation.status = 'REGISTERED'
                    invitation.save(update_fields=['status'])

            # -------------------------------------------------------------
            # STEP 9: SEND EMAIL AFTER PARTNER CREATION
            # Outside transaction.atomic()
            # -------------------------------------------------------------

            email_status, email_message = SendPartnerCredentialsEmail(
                partner=partner,
                sender_mailid=Mail_Config.MailId,
                temporary_password=temporary_password
            )

            # -------------------------------------------------------------
            # STEP 10: SUCCESS RESPONSE
            # -------------------------------------------------------------

            output = {
                "status": True,
                "message": "Partner details saved successfully",

                "data": {

                    "Partner_Database_Id": partner.id,

                    "Partner_Id": partner.Partner_Id,

                    "Partner_Code": partner.Partner_Code,

                    "Partner_Name": partner.Primary_Contact_Name,

                    "Primary_Email": partner.Primary_Email,

                    "Lead_Id": lead.pk if lead else None,   # NEW

                    "Partner": PartnerSerializers(partner).data,

                    "PartnerApplication": (
                        PartnerApplicationSerializers(application).data
                        if application else None
                    ),

                    "KycRecord": (
                        KycRecordSerializers(kyc).data
                        if kyc else None
                    ),

                    "PartnerAgreement": (
                        PartnerAgreementSerializers(agreement).data
                        if agreement else None
                    ),

                    "PartnerInvitation": (
                        PartnerInvitationSerializers(invitation).data
                        if invitation else None
                    ),

                    "Email_Status": (
                        "Sent" if email_status else "Failed"
                    ),

                    "Email_Message": email_message

                }
            }

            return Response(
                output,
                status=status.HTTP_201_CREATED
            )

        except serializers.ValidationError as e:

            return Response({
                "status": False,
                "Error": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:

            logger.exception("Partner creation API failed")

            return Response({
                "status": False,
                "Error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # -------------------------------------------------------------------------
    # GET
    # -------------------------------------------------------------------------

    def get(self, request, *args, **kwargs):

        try:

            partner_id = request.query_params.get('id')

            if not partner_id:
                return Response({
                    "status": False,
                    "Error": "id is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            partner = Partner.objects.get(
                id=partner_id,
                Is_Deleted=False
            )

            serializer = PartnerSerializers(partner)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        except Partner.DoesNotExist:

            return Response({
                "status": False,
                "Error": "Partner not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:

            return Response({
                "status": False,
                "Error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # PUT
    # -------------------------------------------------------------------------

    def put(self, request, *args, **kwargs):

        try:

            partner_id = request.data.get('id')

            if not partner_id:
                return Response({
                    "status": False,
                    "Error": "id is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            partner = Partner.objects.get(
                id=partner_id,
                Is_Deleted=False
            )

            partner_data = request.data.copy()

            if partner_data.get('Password'):

                partner_data['Password'] = make_password(
                    partner_data['Password']
                )

            serializer = PartnerSerializer(
                instance=partner,
                data=partner_data,
                partial=True
            )

            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({
                "status": True,
                "message": "Partner updated successfully",
                "data": PartnerSerializers(partner).data
            }, status=status.HTTP_200_OK)

        except Partner.DoesNotExist:

            return Response({
                "status": False,
                "Error": "Partner not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except serializers.ValidationError as e:

            return Response({
                "status": False,
                "Error": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:

            return Response({
                "status": False,
                "Error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # PATCH
    # -------------------------------------------------------------------------

    def patch(self, request, *args, **kwargs):

        try:

            partner_id = request.data.get('id')

            if not partner_id:
                return Response({
                    "status": False,
                    "Error": "id is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            partner = Partner.objects.get(
                id=partner_id,
                Is_Deleted=False
            )

            partner_data = request.data.copy()

            if partner_data.get('Password'):

                partner_data['Password'] = make_password(
                    partner_data['Password']
                )

            serializer = PartnerSerializer(
                instance=partner,
                data=partner_data,
                partial=True
            )

            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({
                "status": True,
                "message": "Partner updated successfully",
                "data": PartnerSerializers(partner).data
            }, status=status.HTTP_200_OK)

        except Partner.DoesNotExist:

            return Response({
                "status": False,
                "Error": "Partner not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except serializers.ValidationError as e:

            return Response({
                "status": False,
                "Error": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:

            return Response({
                "status": False,
                "Error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------

    def delete(self, request, *args, **kwargs):

        try:

            partner_id = request.query_params.get('id')

            if not partner_id:
                return Response({
                    "status": False,
                    "Error": "id is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            partner = Partner.objects.get(
                id=partner_id,
                Is_Deleted=False
            )

            partner.Is_Deleted = True

            partner.save(
                update_fields=['Is_Deleted']
            )

            return Response({
                "status": True,
                "message": "Partner deleted successfully"
            }, status=status.HTTP_200_OK)

        except Partner.DoesNotExist:

            return Response({
                "status": False,
                "Error": "Partner not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:

            return Response({
                "status": False,
                "Error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# 3. SEPARATE PARTNER CREDENTIALS EMAIL API
# Used for RESENDING LOGIN CREDENTIALS
# =============================================================================

class PartnerCredentialsEmail(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        try:

            partner_id = request.data.get('Partner_Database_Id')

            sender_mailid = request.data.get('sender_mailid')

            temporary_password = request.data.get('temporary_password')

            # Validate payload
            if not partner_id:
                return Response({
                    "status": False,
                    "message": "Partner_Database_Id is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not sender_mailid:
                return Response({
                    "status": False,
                    "message": "sender_mailid is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not temporary_password:
                return Response({
                    "status": False,
                    "message": "temporary_password is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get Partner
            try:

                partner = Partner.objects.get(
                    id=partner_id,
                    Is_Deleted=False
                )

            except Partner.DoesNotExist:

                return Response({
                    "status": False,
                    "message": "Partner not found"
                }, status=status.HTTP_404_NOT_FOUND)

            # Send credentials email
            email_status, email_message = SendPartnerCredentialsEmail(
                partner=partner,
                sender_mailid=sender_mailid,
                temporary_password=temporary_password
            )

            if not email_status:

                return Response({
                    "status": False,
                    "message": email_message
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({

                "status": True,

                "message": email_message,

                "data": {

                    "Partner_Database_Id": partner.id,

                    "Partner_Id": partner.Partner_Id,

                    "Partner_Name": partner.Primary_Contact_Name,

                    "To_Email": partner.Primary_Email,

                    "Sender_Email": sender_mailid,

                    "Email_Status": "Sent"

                }

            }, status=status.HTTP_200_OK)

        except Exception as e:

            logger.exception("Partner credentials email API failed")

            return Response({
                "status": False,
                "message": "Failed to send partner credentials email",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class PartnerCRUD(APIView):

#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data

#             with transaction.atomic():

#                 # Step 1: Check whether related table data is provided
#                 application = None
#                 kyc = None
#                 agreement = None
#                 invitation = None

#                 # Step 2: Save PartnerApplication only if provided
#                 if data.get('PartnerApplication'):
#                     application_serializer = PartnerApplicationSerializer(
#                         data=data['PartnerApplication']
#                     )
#                     application_serializer.is_valid(raise_exception=True)
#                     application = application_serializer.save()

#                 # Step 3: Save KycRecord only if provided
#                 if data.get('KycRecord'):
#                     kyc_serializer = KycRecordSerializer(
#                         data=data['KycRecord']
#                     )
#                     kyc_serializer.is_valid(raise_exception=True)
#                     kyc = kyc_serializer.save()

#                 # Step 4: Save PartnerAgreement only if provided
#                 if data.get('PartnerAgreement'):
#                     agreement_serializer = PartnerAgreementSerializer(
#                         data=data['PartnerAgreement']
#                     )
#                     agreement_serializer.is_valid(raise_exception=True)
#                     agreement = agreement_serializer.save()

#                 # Step 5: Save PartnerInvitation only if provided
#                 if data.get('PartnerInvitation'):
#                     invitation_serializer = PartnerInvitationSerializer(
#                         data=data['PartnerInvitation']
#                     )
#                     invitation_serializer.is_valid(raise_exception=True)
#                     invitation = invitation_serializer.save()

#                 # Step 6: Save Partner
#                 partner_data = data.get('Partner', {}).copy()

#                 if not partner_data:
#                     raise serializers.ValidationError(
#                         {"Partner": "Partner details are required"}
#                     )

#                 # Assign ForeignKeys only when records are created
#                 if application:
#                     partner_data['PartnerApplication_Id'] = application.id

#                 if kyc:
#                     partner_data['KycRecord_Id'] = kyc.id

#                 if agreement:
#                     partner_data['PartnerAgreement_Id'] = agreement.id

#                 if invitation:
#                     partner_data['PartnerInvitation_Id'] = invitation.id

#                 partner_serializer = PartnerSerializer(data=partner_data)
#                 partner_serializer.is_valid(raise_exception=True)
#                 partner = partner_serializer.save()

#             # Step 7: Success Response
#             output = JSONRenderer().render({
#                 "Message": "Partner details saved successfully",
#                 "Partner": PartnerSerializers(partner).data,
#                 "PartnerApplication": PartnerApplicationSerializers(application).data if application else None,
#                 "KycRecord": KycRecordSerializers(kyc).data if kyc else None,
#                 "PartnerAgreement": PartnerAgreementSerializers(agreement).data if agreement else None,
#                 "PartnerInvitation": PartnerInvitationSerializers(invitation).data if invitation else None
#             })

#             return HttpResponse(
#                 output,
#                 content_type='application/json',
#                 status=status.HTTP_201_CREATED
#             )

#         except serializers.ValidationError as e:
#             output = JSONRenderer().render({"Error": e.detail})
#             return HttpResponse(
#                 output,
#                 content_type='application/json',
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(
#                 output,
#                 content_type='application/json',
#                 status=status.HTTP_400_BAD_REQUEST
#             )


#     def get(self, request, *args, **kwargs):
#             try:
#                 data = request.query_params
#                 id = data['id']
#                 module = Partner.objects.get(id=id)
#                 serializer = PartnerSerializers(module)
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#             except Exception as e:
#                 output = JSONRenderer().render({"Error": str(e)})
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             id = data['id']
#             video = Partner.objects.get(id=id)
#             serializer = PartnerSerializer(instance=video, data=request.data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             id = data['id']
#             video = Partner.objects.get(id=id)
#             serializer = PartnerSerializer(video, {"Is_Deleted": True}, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:
#                 raise TypeError("Request data cannot be empty")
#             id = data.get('id')
#             video = Partner.objects.get(id=id)
#             serializer = PartnerSerializer(instance=video, data=data, partial=True)
#             serializer.is_valid(raise_exception=True)
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Partner.DoesNotExist as e:
#             return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



# not need

# GET /PartnerProfile/?id=1
class PartnerProfile(APIView):
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data.get('id')
            if not id:
                partner = Partner.objects.filter(Is_Deleted=False).first()
            else:
                query = Q(id=id) if str(id).isdigit() else Q(Partner_Id=id)
                partner = Partner.objects.filter(query, Is_Deleted=False).first()

            if not partner:
                output = JSONRenderer().render({"Error": "Partner not found"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)

            serializer = PartnerSerializers(partner)
            output_data = serializer.data
            output_data['Created_By'] = getattr(partner, 'Created_By_id', None)
            output_data['Updated_By'] = getattr(partner, 'Updated_By_id', None)

            output = JSONRenderer().render(output_data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# GET /PartnerProfile/?id=1
class PartnerTeamMemberProfile(APIView):
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data.get('id')
            if not id:
                partner = PartnerTeamMember.objects.filter(Is_Deleted=False).first()
            else:
                query = Q(id=id) if str(id).isdigit() else Q(Partner_Id=id)
                partner = PartnerTeamMember.objects.filter(query, Is_Deleted=False).first()

            if not partner:
                output = JSONRenderer().render({"Error": "Partner not found"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)

            serializer = PartnerTeamMemberSerializers(partner)
            output_data = serializer.data
            output_data['Created_By'] = getattr(partner, 'Created_By_id', None)
            output_data['Updated_By'] = getattr(partner, 'Updated_By_id', None)

            output = JSONRenderer().render(output_data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)




from django.contrib.auth.hashers import check_password, make_password, identify_hasher


def _password_matches(partner, raw_password):
    """True if the password is right. Works for old plain-text passwords too and upgrades them to a hash."""
    stored = partner.Password or ""
    cleaned = (raw_password or "").strip()
    try:
        identify_hasher(stored)                 # already hashed
        return check_password(raw_password, stored) or check_password(cleaned, stored)
    except ValueError:                          # old plain-text password
        if stored and (stored == raw_password or stored == cleaned):
            partner.Password = make_password(cleaned)
            partner.save(update_fields=["Password"])
            return True
        return False


# POST /PartnerLogin/   {"Primary_Email": "p@x.com", "Password": "secret"}
class PartnerLogin(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            email = (data.get('Primary_Email') or '').strip()
            password = data.get('Password') or ''
            if not email or not password:
                output = JSONRenderer().render({"Error": "Primary_Email and Password are required"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

            partner = Partner.objects.filter(Primary_Email__iexact=email, Is_Deleted=False).first()
            if not partner or not _password_matches(partner, password):
                output = JSONRenderer().render({"Error": "Invalid email or password"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_401_UNAUTHORIZED)

            serializer = PartnerSerializers(partner)
            output_data = serializer.data
            output_data.pop('Password', None)         # never send the password back

            if partner.Partner_Type:
                output_data['role'] = partner.Partner_Type

            output = JSONRenderer().render(output_data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)




# POST /PartnerTeamMemberLogin/   {"Primary_Email": "p@x.com", "Password": "secret"}
class PartnerTeamMemberLogin(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            email = (data.get('Email') or '').strip()
            password = data.get('Password') or ''
            if not email or not password:
                output = JSONRenderer().render({"Error": "Primary_Email and Password are required"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

            partner = PartnerTeamMember.objects.filter(Email__iexact=email, Is_Deleted=False).first()
            if not partner or not _password_matches(partner, password):
                output = JSONRenderer().render({"Error": "Invalid email or password"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_401_UNAUTHORIZED)

            serializer = PartnerTeamMemberSerializers(partner)
            output_data = serializer.data
            output_data.pop('Password', None)         # never send the password back
            output = JSONRenderer().render(output_data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



class PartnerTickets(APIView):
        def get(self, request, *args, **kwargs):
            try:
                data = request.query_params
                id = data.get('Partner_Id')
                if id:
                    if str(id).isdigit():
                        modules = TicketManagement.objects.filter(Q(Partner_Id=int(id)) | Q(Partner_Id__Partner_Id=id), Is_Deleted=False).order_by('-pk')
                    else:
                        modules = TicketManagement.objects.filter(Q(Partner_Id__Partner_Id=id) | Q(Partner_Id__Partner_Code=id), Is_Deleted=False).order_by('-pk')
                else:
                    modules = TicketManagement.objects.filter(Is_Deleted=False).order_by('-pk')
                serializer = TicketManagementSerializers(modules, many=True)
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            except Exception as e:
                output = JSONRenderer().render({"Error": str(e)})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class PartnerTeamMemberTickets(APIView):
        def get(self, request, *args, **kwargs):
            try:
                data = request.query_params
                id = data.get('PartnerTeamMember_Id')
                if id:
                    if str(id).isdigit():
                        modules = TicketManagement.objects.filter(Q(Partner_Id=int(id)) | Q(Partner_Id__Partner_Id=id), Is_Deleted=False).order_by('-pk')
                    else:
                        modules = TicketManagement.objects.filter(Q(Partner_Id__Partner_Id=id) | Q(Partner_Id__Partner_Code=id), Is_Deleted=False).order_by('-pk')
                else:
                    modules = TicketManagement.objects.filter(Is_Deleted=False).order_by('-pk')
                serializer = TicketManagementSerializers(modules, many=True)
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            except Exception as e:
                output = JSONRenderer().render({"Error": str(e)})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)




def TicketManagement_I():
    last_note = TicketManagement.objects.order_by('pk').last()
    if not last_note:
        return "TKM000000001"

    last_id = last_note.TicketManagement_Id  # e.g. "TSK0000000007"
    numeric_part = ''.join(filter(str.isdigit, last_id))  # keep only digits
    new_id = int(numeric_part) + 1

    return "TKM" + str(new_id).zfill(9)

import base64
import binascii

from django.core.files.base import ContentFile
from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

# from .models import TicketManagement
# from .serializers import TicketManagementSerializer, TicketManagementSerializers


# ---------------------------------------------------------------
# Ticket ID generator
# ---------------------------------------------------------------
def TicketManagement_I():
    last_note = TicketManagement.objects.order_by('pk').last()
    if not last_note:
        return "TKM000000001"

    numeric_part = ''.join(filter(str.isdigit, last_note.TicketManagement_Id))
    new_id = int(numeric_part) + 1 if numeric_part else 1
    return "TKM" + str(new_id).zfill(9)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def to_plain_dict(request_data):
    """Safe copy of request.data for both JSON and multipart (no deepcopy of files)."""
    return {key: value for key, value in request_data.items()}


def extract_file(data):
    """
    Pulls 'File' and 'File_Name' out of data and returns (file_obj, error).
    Supports:
      - multipart upload (File is a real uploaded file)
      - base64 string, with or without 'data:...;base64,' prefix
    Returns (None, None) when no file was sent.
    """
    raw_file = data.pop('File', None)
    file_name = data.pop('File_Name', None)

    if not raw_file:
        return None, None

    # Case 1: real file sent as multipart/form-data
    if hasattr(raw_file, 'read'):
        return raw_file, None

    # Case 2: base64 string
    if not file_name:
        return None, {"File_Name": "File_Name is required when File is sent as base64"}

    b64 = str(raw_file).strip()
    if ';base64,' in b64:                 # remove "data:application/pdf;base64,"
        b64 = b64.split(';base64,', 1)[1]
    b64 += '=' * (-len(b64) % 4)          # fix missing padding

    try:
        decoded = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        return None, {"File": "Invalid base64 file data"}

    return ContentFile(decoded, name=file_name), None


def json_error(message, code=status.HTTP_400_BAD_REQUEST):
    output = JSONRenderer().render({"Error": str(message)})
    return HttpResponse(output, content_type='application/json', status=code)


# ---------------------------------------------------------------
# View
# ---------------------------------------------------------------
class TicketManagementCRUDwithnotoken(ListAPIView):
    queryset = TicketManagement.objects.all()
    # authentication_classes=[JWTAuthentication]
    # permission_classes=[DjangoModelPermissions]

    # ---------- CREATE ----------
    def post(self, request, *args, **kwargs):
        try:
            data = to_plain_dict(request.data)
            data['TicketManagement_Id'] = TicketManagement_I()

            file_obj, file_error = extract_file(data)
            if file_error:
                return Response(file_error, status=status.HTTP_400_BAD_REQUEST)

            serializer = TicketManagementSerializer(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Pass the file directly so the serializer cannot drop it
            if file_obj:
                instance = serializer.save(File=file_obj)
            else:
                instance = serializer.save()

            return Response(TicketManagementSerializer(instance).data,
                            status=status.HTTP_201_CREATED)

        except Exception as e:
            return json_error(e)

    # ---------- READ ----------
    def get(self, request, *args, **kwargs):
        try:
            ticket_id = request.query_params.get('id')
            if not ticket_id:
                return json_error("id is required")

            module = TicketManagement.objects.get(id=ticket_id)
            serializer = TicketManagementSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')

        except TicketManagement.DoesNotExist:
            return json_error("Ticket not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return json_error(e)

    # ---------- UPDATE (PUT) ----------
    def put(self, request, *args, **kwargs):
        return self._update(request)

    # ---------- UPDATE (PATCH) ----------
    def patch(self, request, *args, **kwargs):
        return self._update(request)

    def _update(self, request):
        try:
            data = to_plain_dict(request.data)

            ticket_id = data.get('id')
            if not ticket_id:
                return Response({"Error": "id is required"},
                                status=status.HTTP_400_BAD_REQUEST)

            module = TicketManagement.objects.get(id=ticket_id)

            file_obj, file_error = extract_file(data)
            if file_error:
                return Response(file_error, status=status.HTTP_400_BAD_REQUEST)

            serializer = TicketManagementSerializer(instance=module, data=data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if file_obj:
                instance = serializer.save(File=file_obj)
            else:
                instance = serializer.save()   # existing file is kept

            return Response(TicketManagementSerializer(instance).data,
                            status=status.HTTP_200_OK)

        except TicketManagement.DoesNotExist:
            return Response({"Error": "Ticket not found"},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ---------- SOFT DELETE ----------
    def delete(self, request, *args, **kwargs):
        try:
            ticket_id = request.query_params.get('id')
            if not ticket_id:
                return json_error("id is required")

            module = TicketManagement.objects.get(id=ticket_id)
            serializer = TicketManagementSerializer(module, {"Is_Deleted": True}, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json',
                                status=status.HTTP_200_OK)

        except TicketManagement.DoesNotExist:
            return json_error("Ticket not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return json_error(e)

class KycRecordList(ListAPIView):
    queryset = KycRecord.objects.all()
    serializer_class = KycRecordSerializers

    def get_queryset(self):
        try:
            module = KycRecord.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")

class KycRecordWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = KycRecord.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = KycRecordSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class KycRecordCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = KycRecordSerializer(data=data)
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
            id = data.get('id')
            module = None
            if id:
                query = Q(pk=id) | Q(KycRecord_id=id)
                module = KycRecord.objects.filter(query, Is_Deleted=False).first()
                if not module:
                    module = KycRecord.objects.filter(query).first()
            if not module:
                module = KycRecord.objects.filter(Is_Deleted=False).first()
            if not module:
                output = JSONRenderer().render({"Error": f"KycRecord matching '{id}' not found"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)
            serializer = KycRecordSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data.get('id') or data.get('KycRecord_id') or request.query_params.get('id')
            query = Q(pk=id) | Q(KycRecord_id=id)
            module = KycRecord.objects.filter(query).first()
            if not module:
                return HttpResponse(JSONRenderer().render({"Error": f"KycRecord '{id}' not found"}), content_type='application/json', status=status.HTTP_404_NOT_FOUND)
            serializer = KycRecordSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data.get('id')
            query = Q(pk=id) | Q(KycRecord_id=id)
            module = KycRecord.objects.filter(query).first()
            if not module:
                return HttpResponse(JSONRenderer().render({"Error": f"KycRecord '{id}' not found"}), content_type='application/json', status=status.HTTP_404_NOT_FOUND)
            serializer = KycRecordSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id') or data.get('KycRecord_id') or request.query_params.get('id')
            query = Q(pk=id) | Q(KycRecord_id=id)
            module = KycRecord.objects.filter(query).first()
            if not module:
                return Response({"Error": f"KycRecord '{id}' not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = KycRecordSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class PartnerWiseKycList(ListAPIView):
    queryset = KycRecord.objects.all()
    serializer_class = KycRecordSerializers

    def get_queryset(self):
        try:
            data = self.request.query_params

            # 1. get the partner record
            partner = Partner.objects.get(
                id=data['partner_id'],
                Is_Deleted=False
            )

            # 2. get the lead id of that partner
            lead_id = partner.Lead_Id_id

            # partner has no lead linked -> empty list
            if not lead_id:
                return KycRecord.objects.none()

            # 3. get the KYC records of that lead
            module = KycRecord.objects.filter(
                Q(Lead_Id=lead_id) & Q(Is_Deleted=False)
            ).order_by('-pk')
            return module

        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")



class PartnerAgreementList(ListAPIView):
    queryset = PartnerAgreement.objects.all()
    serializer_class = PartnerAgreementSerializers

    def get_queryset(self):
        try:
            module = PartnerAgreement.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")

class PartnerAgreementWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerAgreement.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerAgreementSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

import base64
from django.core.files.base import ContentFile


# helper - handles both multipart file upload and base64 string
# name_field: 'FileName' for AgreementTemplate, 'File_Name' for PartnerAgreement
def handle_base64_or_file(data, name_field):
    """
    Returns an error message if the file is invalid, else None.
    - multipart upload  -> File is an uploaded file object, keep as it is
    - base64 string     -> decode and convert to a file
    - nothing sent      -> remove File / name field so old file stays
    """
    file_data = data.get('File')
    file_name = data.get(name_field)

    # multipart: real file object
    if hasattr(file_data, 'read'):
        if not file_name:
            data[name_field] = file_data.name
        return None

    # json: base64 string
    if isinstance(file_data, str) and file_data and file_name:
        try:
            if ',' in file_data:
                file_data = file_data.split(',')[-1]
            decoded_file = base64.b64decode(file_data)
            data['File'] = ContentFile(decoded_file, name=file_name)
            return None
        except Exception:
            return "Invalid base64 file data"

    # no file sent
    data.pop('File', None)
    data.pop(name_field, None)
    return None


def get_request_data(request):
    """Plain dict that is safe for both multipart and json."""
    if hasattr(request.data, 'dict'):
        return request.data.dict()
    return dict(request.data)


class PartnerAgreementCRUD(ListAPIView):
    queryset = PartnerAgreement.objects.all()

    def post(self, request, *args, **kwargs):
        try:
            data = get_request_data(request)

            file_error = handle_base64_or_file(data, 'File_Name')
            if file_error:
                return Response(
                    {"File": file_error},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = PartnerAgreementSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(
                output,
                content_type='application/json',
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerAgreement.objects.get(id=id)
            serializer = PartnerAgreementSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = get_request_data(request)

            agreement_id = data.get('id')
            if not agreement_id:
                return Response(
                    {"Error": "id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            module = PartnerAgreement.objects.get(id=agreement_id)

            file_error = handle_base64_or_file(data, 'File_Name')
            if file_error:
                return Response(
                    {"File": file_error},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = PartnerAgreementSerializer(
                instance=module,
                data=data,
                partial=True   # important for PUT/PATCH
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except PartnerAgreement.DoesNotExist:
            return Response(
                {"Error": "Partner agreement not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"Error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request, *args, **kwargs):
        try:
            data = get_request_data(request)
            module = PartnerAgreement.objects.get(id=data['id'])

            file_error = handle_base64_or_file(data, 'File_Name')
            if file_error:
                return Response(
                    {"File": file_error},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = PartnerAgreementSerializer(instance=module, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            output = JSONRenderer().render({'Error': str(err)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerAgreement.objects.get(id=id)
            serializer = PartnerAgreementSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# class PartnerAgreementCRUD(APIView):
#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             serializer = PartnerAgreementSerializer(data=data)
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
#             id = data.get('id')
#             module = None
#             if id:
#                 query = Q(pk=id) | Q(agreement_code=id) | Q(partner_org_id=id)
#                 module = PartnerAgreement.objects.filter(query, Is_Deleted=False).first()
#                 if not module:
#                     module = PartnerAgreement.objects.filter(query).first()
#                 if not module:
#                     app = PartnerApplication.objects.filter(
#                         Q(pk=id) | Q(PartnerApplication_id=id) | Q(application_number=id)
#                     ).first()
#                     if app:
#                         module = PartnerAgreement.objects.filter(
#                             Q(partner_org_id=str(app.pk)) | Q(partner_org_name=app.organisation_name),
#                             Is_Deleted=False
#                         ).first()
#                 if not module and ('PEG-APP' in str(id) or str(id).startswith('APP')):
#                     module = PartnerAgreement.objects.filter(Is_Deleted=False).first()
#             if not module:
#                 module = PartnerAgreement.objects.filter(Is_Deleted=False).first()
#             if not module:
#                 output = JSONRenderer().render({"Error": f"PartnerAgreement matching '{id}' not found"})
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)
#             serializer = PartnerAgreementSerializers(module)
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             id = data.get('id') or data.get('PartnerAgreement_id') or request.query_params.get('id')
#             query = Q(pk=id) | Q(agreement_code=id) | Q(partner_org_id=id)
#             module = PartnerAgreement.objects.filter(query).first()
#             if not module and ('PEG-APP' in str(id) or str(id).startswith('APP')):
#                 module = PartnerAgreement.objects.filter(Is_Deleted=False).first()
#             if not module:
#                 return HttpResponse(JSONRenderer().render({"Error": f"PartnerAgreement '{id}' not found"}), content_type='application/json', status=status.HTTP_404_NOT_FOUND)
#             serializer = PartnerAgreementSerializer(instance=module, data=request.data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             id = data.get('id')
#             query = Q(pk=id) | Q(agreement_code=id) | Q(partner_org_id=id)
#             module = PartnerAgreement.objects.filter(query).first()
#             if not module:
#                 return HttpResponse(JSONRenderer().render({"Error": f"PartnerAgreement '{id}' not found"}), content_type='application/json', status=status.HTTP_404_NOT_FOUND)
#             serializer = PartnerAgreementSerializer(module, {"Is_Deleted": True}, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             if not data:
#                 raise TypeError("Request data cannot be empty")
#             id = data.get('id') or data.get('PartnerAgreement_id') or request.query_params.get('id')
#             query = Q(pk=id) | Q(agreement_code=id) | Q(partner_org_id=id)
#             module = PartnerAgreement.objects.filter(query).first()
#             if not module and ('PEG-APP' in str(id) or str(id).startswith('APP')):
#                 module = PartnerAgreement.objects.filter(Is_Deleted=False).first()
#             if not module:
#                 return Response({"Error": f"PartnerAgreement '{id}' not found"}, status=status.HTTP_404_NOT_FOUND)
#             serializer = PartnerAgreementSerializer(instance=module, data=data, partial=True)
#             serializer.is_valid(raise_exception=True)
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PartnerWiseAgreementList(ListAPIView):
    serializer_class = PartnerAgreementSerializers

    def get_queryset(self):
        partner_id = self.request.query_params.get('partner_id')
        if not partner_id or not partner_id.isdigit():
            raise ValidationError({"partner_id": "A valid partner_id query parameter is required."})

        return PartnerAgreement.objects.filter(
            Is_Deleted=False,
            Partner_Id=partner_id,
        ).order_by('-id')


import base64
from django.core.files.base import ContentFile


# helper - handles both multipart file upload and base64 string
def handle_template_file(data):
    """
    Returns an error message if the file is invalid, else None.
    - multipart upload  -> File is an uploaded file object, keep as it is
    - base64 string     -> decode and convert to a file
    - nothing sent      -> remove File / FileName so old file stays
    """
    file_data = data.get('File')
    file_name = data.get('FileName')

    # multipart: real file object
    if hasattr(file_data, 'read'):
        if not file_name:
            data['FileName'] = file_data.name
        return None

    # json: base64 string
    if isinstance(file_data, str) and file_data and file_name:
        try:
            if ',' in file_data:
                file_data = file_data.split(',')[-1]
            decoded_file = base64.b64decode(file_data)
            data['File'] = ContentFile(decoded_file, name=file_name)
            return None
        except Exception:
            return "Invalid base64 file data"

    # no file sent
    data.pop('File', None)
    data.pop('FileName', None)
    return None


def get_request_data(request):
    """Plain dict that is safe for both multipart and json."""
    if hasattr(request.data, 'dict'):
        return request.data.dict()
    return dict(request.data)


class AgreementTemplateCRUD(ListAPIView):
    queryset = AgreementTemplate.objects.all()

    def post(self, request, *args, **kwargs):
        try:
            data = get_request_data(request)

            # Generate Template ID
            data['Template_Name_Id'] = AgreementTemplate_Id_I()

            file_error = handle_template_file(data)
            if file_error:
                return Response(
                    {"File": file_error},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = AgreementTemplateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(
                output,
                content_type='application/json',
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = AgreementTemplate.objects.get(id=id)
            serializer = AgreementTemplateSerializer(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json')
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = get_request_data(request)

            template_id = data.get('id')
            if not template_id:
                return Response(
                    {"Error": "id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            module = AgreementTemplate.objects.get(id=template_id)

            file_error = handle_template_file(data)
            if file_error:
                return Response(
                    {"File": file_error},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = AgreementTemplateSerializer(
                instance=module,
                data=data,
                partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except AgreementTemplate.DoesNotExist:
            return Response(
                {"Error": "Agreement template not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"Error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request, *args, **kwargs):
        try:
            data = get_request_data(request)
            module = AgreementTemplate.objects.get(id=data['id'])

            file_error = handle_template_file(data)
            if file_error:
                return Response(
                    {"File": file_error},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = AgreementTemplateSerializer(instance=module, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            output = JSONRenderer().render({'Error': str(err)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = AgreementTemplate.objects.get(id=id)
            serializer = AgreementTemplateSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class AgreementTemplateList(ListAPIView):
    queryset = AgreementTemplate.objects.all()
    serializer_class = AgreementTemplateSerializer

    def get_queryset(self):
        try:
            module = AgreementTemplate.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")

class AgreementTemplateWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = AgreementTemplate.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = AgreementTemplateSerializer(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)





class PartnerInvitationList(ListAPIView):
    queryset = PartnerInvitation.objects.all()
    serializer_class = PartnerInvitationSerializers

    def get_queryset(self):
        try:
            module = PartnerInvitation.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class PartnerInvitationWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerInvitation.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerInvitationSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



class PartnerInvitationCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PartnerInvitationSerializer(data=data)
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
            module = PartnerInvitation.objects.get(id=id)
            serializer = PartnerInvitationSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = PartnerInvitation.objects.get(id=id)
            serializer = PartnerInvitationSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerInvitation.objects.get(id=id)
            serializer = PartnerInvitationSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerInvitation.objects.get(id=id)
            serializer = PartnerInvitationSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerInvitation.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class partnerProductSupportList(ListAPIView):
    queryset = PartnerProductSupport.objects.all()
    serializer_class = PartnerProductSupportSerializers

    def get_queryset(self):
        try:
            module = PartnerProductSupport.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")

class partnerProductSupportWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerProductSupport.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerProductSupportSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class partnerProductSupportCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PartnerProductSupportSerializer(data=data)
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
            module = PartnerProductSupport.objects.get(id=id)
            serializer = PartnerProductSupportSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = PartnerProductSupport.objects.get(id=id)
            serializer = PartnerProductSupportSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerProductSupport.objects.get(id=id)
            serializer = PartnerProductSupportSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerProductSupport.objects.get(id=id)
            serializer = PartnerProductSupportSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerProductSupport.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class CustomerLeadList(ListAPIView):
    queryset = PartnerCustomer.objects.all()
    serializer_class = PartnerCustomerSerializers

    def get_queryset(self):
        try:
            module = PartnerCustomer.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")



class CustomerLeadWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerCustomer.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerCustomerSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)




class PartnerCustomerLeadListwithPartnerId(ListAPIView):

    queryset = PartnerCustomerLead.objects.all()
    serializer_class = PartnerCustomerLeadSerializers
    def get_queryset(self):
        try:
            data = self.request.query_params
            Partner_Id = data.get('Partner_Id')
            module = PartnerCustomerLead.objects.filter(Q(Is_Deleted=False)&Q(Partner_Id=Partner_Id)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")




class PartnerCustomerLeadList(ListAPIView):
    queryset = PartnerCustomerLead.objects.all()
    serializer_class = PartnerCustomerLeadSerializers

    def get_queryset(self):
        try:
            module = PartnerCustomerLead.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")



class PartnerCustomerLeadWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerCustomerLead.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerCustomerLeadSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



class CustomerLeadCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PartnerCustomerLeadSerializer(data=data)
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
            module =PartnerCustomerLead.objects.get(id=id)
            serializer = PartnerCustomerLeadSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = PartnerCustomerLead.objects.get(id=id)
            serializer = PartnerCustomerLeadSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerCustomerLead.objects.get(id=id)
            serializer = PartnerCustomerLeadSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerCustomerLead.objects.get(id=id)
            serializer = PartnerCustomerLeadSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PartnerOpportunityList(ListAPIView):
    queryset = PartnerOpportunity.objects.all()
    serializer_class = PartnerOpportunitySerializers

    def get_queryset(self):
        try:
            module = PartnerOpportunity.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class PartnerOpportunityWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerOpportunity.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerOpportunitySerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class PartnerOpportunityCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PartnerOpportunitySerializer(data=data)
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
            module = PartnerOpportunity.objects.get(id=id)
            serializer = PartnerOpportunitySerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = PartnerOpportunity.objects.get(id=id)
            serializer = PartnerOpportunitySerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerOpportunity.objects.get(id=id)
            serializer = PartnerOpportunitySerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerOpportunity.objects.get(id=id)
            serializer = PartnerOpportunitySerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerOpportunity.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class PartnerCustomerList(ListAPIView):
    queryset = PartnerCustomer.objects.all()
    serializer_class = PartnerCustomerSerializers

    def get_queryset(self):
        try:
            module = PartnerCustomer.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class PartnerCustomerWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerCustomer.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerCustomerSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class PartnerCustomerCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PartnerCustomerSerializer(data=data)
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
            module = PartnerCustomer.objects.get(id=id)
            serializer = PartnerCustomerSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = PartnerCustomer.objects.get(id=id)
            serializer = PartnerCustomerSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerCustomer.objects.get(id=id)
            serializer = PartnerCustomerSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerCustomer.objects.get(id=id)
            serializer = PartnerCustomerSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerCustomer.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class BusinessCommissionList(ListAPIView):
    queryset = PartnerPayout.objects.all()
    serializer_class = PartnerPayoutSerializers

    def get_queryset(self):
        try:
            module = PartnerPayout.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")

class BusinessCommissionWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerPayout.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerPayoutSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class BusinessCommissionCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PartnerPayoutSerializer(data=data)
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
            module = PartnerPayout.objects.get(id=id)
            serializer = PartnerPayoutSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = PartnerPayout.objects.get(id=id)
            serializer = PartnerPayoutSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerPayout.objects.get(id=id)
            serializer = PartnerPayoutSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerPayout.objects.get(id=id)
            serializer = PartnerPayoutSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerPayout.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class PartnerPayoutList(ListAPIView):
    queryset = PartnerPayout.objects.all()
    serializer_class = PartnerPayoutSerializers

    def get_queryset(self):
        try:
            module = PartnerPayout.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")

class PartnerPayoutWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerPayout.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerPayoutSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class PartnerPayoutCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PartnerPayoutSerializer(data=data)
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
            module = PartnerPayout.objects.get(id=id)
            serializer = PartnerPayoutSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = PartnerPayout.objects.get(id=id)
            serializer = PartnerPayoutSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerPayout.objects.get(id=id)
            serializer = PartnerPayoutSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerPayout.objects.get(id=id)
            serializer = PartnerPayoutSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerPayout.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class BusinessResourceList(ListAPIView):
    queryset = BusinessResource.objects.all()
    serializer_class = BusinessResourceSerializers

    def get_queryset(self):
        try:
            module = BusinessResource.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class BusinessResourceWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = BusinessResource.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = BusinessResourceSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            if 'does not exist' in str(e).lower() or 'relation' in str(e).lower():
                return HttpResponse('[]', content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class BusinessResourceCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = BusinessResourceSerializer(data=data)
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
            module = BusinessResource.objects.get(id=id)
            serializer = BusinessResourceSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = BusinessResource.objects.get(id=id)
            serializer = BusinessResourceSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = BusinessResource.objects.get(id=id)
            serializer = BusinessResourceSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = BusinessResource.objects.get(id=id)
            serializer = BusinessResourceSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BusinessResource.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ImplementationProjectList(ListAPIView):
    queryset = ImplementationProject.objects.all()
    serializer_class = ImplementationProjectSerializers

    def get_queryset(self):
        try:
            module = ImplementationProject.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")

class ImplementationProjectWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = ImplementationProject.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = ImplementationProjectSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class ImplementationProjectCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = ImplementationProjectSerializer(data=data)
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
            module = ImplementationProject.objects.get(id=id)
            serializer = ImplementationProjectSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = ImplementationProject.objects.get(id=id)
            serializer = ImplementationProjectSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = ImplementationProject.objects.get(id=id)
            serializer = ImplementationProjectSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = ImplementationProject.objects.get(id=id)
            serializer = ImplementationProjectSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ImplementationProject.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DailyWorkUpdateList(ListAPIView):
    queryset = DailyWorkUpdate.objects.all()
    serializer_class = DailyWorkUpdateSerializers

    def get_queryset(self):
        try:
            module = DailyWorkUpdate.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")

class DailyWorkUpdateWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = DailyWorkUpdate.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = DailyWorkUpdateSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            if 'does not exist' in str(e).lower() or 'relation' in str(e).lower():
                return HttpResponse('[]', content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)




# class SuperadminDailyWorkUpdateList(ListAPIView):
#     queryset = DailyWorkUpdate.objects.all()
#     serializer_class = DailyWorkUpdateSerializers

#     def get_queryset(self):
#         try:
#             return DailyWorkUpdate.objects.filter(
#                 Is_Deleted=False,
#                 PartnerTeamMember_Id__isnull=True,
#             ).order_by('-id')
#         except Exception as e:
#             raise Exception(f"Error while fetching module: {str(e)}")

# class PartnerMyDailyWorkUpdateList(ListAPIView):
#     queryset = DailyWorkUpdate.objects.all()
#     serializer_class = DailyWorkUpdateSerializers

#     def get_queryset(self):
#         try:
#             partner_id = self.kwargs.get('partner_id')
#             return DailyWorkUpdate.objects.filter(
#                 Is_Deleted=False,
#                 Partner_Id=partner_id,
#             ).select_related('Partner_Id').order_by('-id')
#         except Exception as e:
#             raise Exception(f"Error while fetching partner daily work updates: {str(e)}")


# class PartnerAllteamDailyWorkUpdateList(ListAPIView):
#     serializer_class = DailyWorkUpdateSerializers

#     def get_queryset(self):
#         try:
#             partner_id = self.kwargs.get('partner_id')
#             return DailyWorkUpdate.objects.filter(
#                 Is_Deleted=False,
#                 Partner_Id=partner_id,
#                 PartnerTeamMember_Id__isnull=False,
#             ).select_related('Partner_Id', 'PartnerTeamMember_Id').order_by('-pk')
#         except Exception as e:
#             raise Exception(f"Error while fetching partner team daily work updates: {str(e)}")



# class PartnerTeamMemberDailyWorkUpdateList(ListAPIView):
#     serializer_class = DailyWorkUpdateSerializers
#     def get_queryset(self):
#         try:
#             PartnerTeamMember_Id = self.kwargs.get('partnerTeamUser_id')
#             return DailyWorkUpdate.objects.filter(
#                 Is_Deleted=False,
#                 PartnerTeamMember_Id=PartnerTeamMember_Id,
#             ).select_related('PartnerTeamMember_Id').order_by('-id')
#         except Exception as e:
#             raise Exception(f"Error while fetching partner daily work updates: {str(e)}")

from rest_framework.exceptions import ValidationError


class SuperadminDailyWorkUpdateList(ListAPIView):
    queryset = DailyWorkUpdate.objects.all()
    serializer_class = DailyWorkUpdateSerializers

    def get_queryset(self):
        try:
            return DailyWorkUpdate.objects.filter(
                Is_Deleted=False,
                PartnerTeamMember_Id__isnull=True,
            ).order_by('-id')
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


# class PartnerMyDailyWorkUpdateList(ListAPIView):
#     queryset = DailyWorkUpdate.objects.all()
#     serializer_class = DailyWorkUpdateSerializers

#     def get_queryset(self):
#         partner_id = self.request.query_params.get('Partner_Id')
#         if not partner_id:
#             raise ValidationError({"partner_id": "This query parameter is required."})

#         try:
#             return DailyWorkUpdate.objects.filter(
#                 Is_Deleted=False,
#                 Partner_Id=partner_id,
#                 PartnerTeamMember_Id__isnull=False,
#             ).select_related('Partner_Id').order_by('-id')
#         except Exception as e:
#             raise Exception(f"Error while fetching partner daily work updates: {str(e)}")

class PartnerMyDailyWorkUpdateList(ListAPIView):
    queryset = DailyWorkUpdate.objects.all()
    serializer_class = DailyWorkUpdateSerializers

    def get_queryset(self):
        partner_id = self.request.query_params.get('Partner_Id')
        if not partner_id:
            raise ValidationError({"partner_id": "This query parameter is required."})

        try:
            return DailyWorkUpdate.objects.filter(
                Is_Deleted=False,
                Partner_Id=partner_id,
                PartnerTeamMember_Id__isnull=True,   # partner only, excludes records that have both ids
            ).select_related('Partner_Id').order_by('-id')
        except Exception as e:
            raise Exception(f"Error while fetching partner daily work updates: {str(e)}")

class PartnerAllteamDailyWorkUpdateList(ListAPIView):
    serializer_class = DailyWorkUpdateSerializers

    def get_queryset(self):
        partner_id = self.request.query_params.get('Partner_Id')
        if not partner_id:
            raise ValidationError({"partner_id": "This query parameter is required."})

        try:
            return DailyWorkUpdate.objects.filter(
                Is_Deleted=False,
                Partner_Id=partner_id,
                PartnerTeamMember_Id__isnull=False,
            ).select_related('Partner_Id', 'PartnerTeamMember_Id').order_by('-pk')
        except Exception as e:
            raise Exception(f"Error while fetching partner team daily work updates: {str(e)}")


class PartnerTeamMemberDailyWorkUpdateList(ListAPIView):
    serializer_class = DailyWorkUpdateSerializers

    def get_queryset(self):
        partner_team_user_id = self.request.query_params.get('partnerTeamUser_id')
        if not partner_team_user_id:
            raise ValidationError({"partnerTeamUser_id": "This query parameter is required."})

        try:
            return DailyWorkUpdate.objects.filter(
                Is_Deleted=False,
                PartnerTeamMember_Id=partner_team_user_id,
            ).select_related('PartnerTeamMember_Id').order_by('-id')
        except Exception as e:
            raise Exception(f"Error while fetching partner team member daily work updates: {str(e)}")

class DailyWorkUpdateCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = DailyWorkUpdateSerializer(data=data)
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
            module = DailyWorkUpdate.objects.get(id=id)
            serializer = DailyWorkUpdateSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = DailyWorkUpdate.objects.get(id=id)
            serializer = DailyWorkUpdateSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = DailyWorkUpdate.objects.get(id=id)
            serializer = DailyWorkUpdateSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = DailyWorkUpdate.objects.get(id=id)
            serializer = DailyWorkUpdateSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DailyWorkUpdate.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class TenantProvisioningJobList(ListAPIView):
    queryset = TenantProvisioningJob.objects.all()
    serializer_class = TenantProvisioningJobSerializers

    def get_queryset(self):
        try:
            module = TenantProvisioningJob.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class TenantProvisioningJobWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = TenantProvisioningJob.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = TenantProvisioningJobSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class TenantProvisioningJobCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = TenantProvisioningJobSerializer(data=data)
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
            module = TenantProvisioningJob.objects.get(id=id)
            serializer = TenantProvisioningJobSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = TenantProvisioningJob.objects.get(id=id)
            serializer = TenantProvisioningJobSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = TenantProvisioningJob.objects.get(id=id)
            serializer = TenantProvisioningJobSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = TenantProvisioningJob.objects.get(id=id)
            serializer = TenantProvisioningJobSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TenantProvisioningJob.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




class PartnerTeamMemberList(ListAPIView):
    queryset = PartnerTeamMember.objects.all()
    serializer_class = PartnerTeamMemberSerializers
    def get_queryset(self):
        try:
            data = self.request.query_params
            Partner_Id = data.get('Partner_Id')
            module = PartnerTeamMember.objects.filter(Q(Is_Deleted=False)&Q(Partner_Id=Partner_Id)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")



class PartnerTeamMemberWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerTeamMember.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerTeamMemberSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# class PartnerTeamMemberCRUD(APIView):
#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             serializer = PartnerTeamMemberSerializer(data=data)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

import html
import logging
import secrets
import string

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email


TEAM_LOGIN_LINK = "https://partner.pegatto.com/auth/team-login"


# -----------------------------------------------------------------------------
# TEMP PASSWORD
# -----------------------------------------------------------------------------

def GenerateTemporaryPassword(length=10):
    alphabet = string.ascii_letters + string.digits
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
        ):
            return password


# -----------------------------------------------------------------------------
# EMAIL
# -----------------------------------------------------------------------------

def SendPartnerTeamMemberCredentialsEmail(team_member, partner_mailid, temporary_password):
    """
    Sends welcome + login credentials mail to the team member.
    No UserMailConfiguration used. Uses Django EMAIL_* settings.
    partner_mailid is used as Reply-To.
    """
    try:
        # Step 1: Team member email
        team_email = team_member.Email

        if not team_email:
            return False, "Team member email address is not available"

        # Step 2: Validate email addresses
        validate_email(partner_mailid)
        validate_email(team_email)

        # Step 3: Verify password
        if not check_password(temporary_password, team_member.Password):
            return False, "Team member password verification failed"

        # Step 4: Names
        member_name = (
            f"{team_member.First_Name or ''} {team_member.Last_Name or ''}".strip()
            or "Team Member"
        )

        partner = team_member.Partner_Id
        partner_name = (
            (partner.Trade_Name or partner.Legal_Name) if partner else None
        ) or "your partner organisation"

        subject = "Welcome to the Pegatto Partner Team - Login Credentials"

        # Step 5: Plain text email
        plain_message = f"""
Dear {member_name},

Welcome to the team!

You are now a Partner Team Member of {partner_name} on the Pegatto Partner Network.

Your login credentials are:

Login Email: {team_email}

Temporary Password: {temporary_password}

Please click the Login button in this email to access
your Pegatto Partner Team Portal:
{TEAM_LOGIN_LINK}

Please change your password after your first login.

Best Regards,
Pegatto Team
"""

        # Step 6: HTML email
        safe_name = html.escape(member_name)
        safe_partner = html.escape(partner_name)
        safe_email = html.escape(team_email)
        safe_password = html.escape(temporary_password)
        safe_link = html.escape(TEAM_LOGIN_LINK, quote=True)

        html_message = f"""
        <html>
        <body style="font-family:Arial,sans-serif;
                     color:#333;
                     line-height:1.6;">

            <div style="max-width:600px;
                        margin:auto;
                        padding:25px;
                        border:1px solid #e5e7eb;
                        border-radius:10px;">

                <h2 style="color:#2563eb;">
                    Welcome to the Team!
                </h2>

                <p>Dear <strong>{safe_name}</strong>,</p>

                <p>
                    You are now a <strong>Partner Team Member</strong>
                    of <strong>{safe_partner}</strong> on the
                    Pegatto Partner Network.
                </p>

                <p>Your login credentials are:</p>

                <div style="background:#f4f7fb;
                            padding:20px;
                            border-radius:8px;">

                    <p><strong>Login Email:</strong></p>
                    <p>{safe_email}</p>

                    <p><strong>Temporary Password:</strong></p>
                    <p>{safe_password}</p>

                </div>

                <p style="margin:30px 0;text-align:center;">

                    <a href="{safe_link}"
                       style="background-color:#2563eb;
                              color:#ffffff;
                              padding:14px 28px;
                              text-decoration:none;
                              border-radius:6px;
                              font-weight:bold;
                              display:inline-block;">

                        Login to Team Portal

                    </a>

                </p>

                <p>
                    Please change your password after your first login.
                </p>

                <p>
                    Best Regards,<br>
                    <strong>Pegatto Team</strong>
                </p>

            </div>

        </body>
        </html>
        """

        # Step 7: Create email
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)

        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=from_email,
            to=[team_email],
            reply_to=[partner_mailid],
        )

        email.attach_alternative(html_message, "text/html")

        # Step 8: Send email
        email.send(fail_silently=False)

        return True, "Team member login credentials email sent successfully"

    except ValidationError:
        return False, "Invalid partner or team member email address"

    except Exception as e:
        logger.exception("Team member credentials email failed")
        return False, str(e)


# -----------------------------------------------------------------------------
# API
# -----------------------------------------------------------------------------

class PartnerTeamMemberCRUD(APIView):

    # CREATE + SEND MAIL
    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()

            # Temporary password: from request, else generated
            temporary_password = data.get('Password') or GenerateTemporaryPassword()
            data['Password'] = make_password(temporary_password)

            # Login id defaults to email
            if not data.get('User_Id') and data.get('Email'):
                data['User_Id'] = data.get('Email')

            serializer = PartnerTeamMemberSerializer(data=data)
            if serializer.is_valid():
                team_member = serializer.save()

                # Partner mail id: from request, else partner's primary email
                partner_mailid = data.get('partner_mail_id')
                if not partner_mailid and team_member.Partner_Id:
                    partner_mailid = team_member.Partner_Id.Primary_Email

                # Send mail after record is created
                email_sent, email_message = SendPartnerTeamMemberCredentialsEmail(
                    team_member, partner_mailid, temporary_password
                )

                response_data = dict(serializer.data)
                response_data['email_sent'] = email_sent
                response_data['email_message'] = email_message

                output = JSONRenderer().render(response_data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)

            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id_val = data.get('id') or data.get('PartnerTeamMember_Id') or data.get('partnerTeamUser_id')
            if not id_val:
                return HttpResponse(JSONRenderer().render({"Error": "id is required"}), content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            module = None
            if str(id_val).isdigit():
                module = PartnerTeamMember.objects.filter(
                    Q(id=int(id_val)) | Q(PartnerTeamMember_id=f"PTT{str(id_val).zfill(9)}") | Q(PartnerTeamMember_id=str(id_val)),
                    Is_Deleted=False
                ).first()
            if not module:
                module = PartnerTeamMember.objects.filter(
                    Q(PartnerTeamMember_id=str(id_val)) | Q(Email__iexact=str(id_val)),
                    Is_Deleted=False
                ).first()
            if not module:
                # Fallback to any active partner team member if not found
                module = PartnerTeamMember.objects.filter(Is_Deleted=False).first()
            if not module:
                return HttpResponse(JSONRenderer().render({"Error": "Partner team member not found"}), content_type='application/json', status=status.HTTP_404_NOT_FOUND)
            serializer = PartnerTeamMemberSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id_val = data.get('id') or data.get('PartnerTeamMember_Id') or data.get('partnerTeamUser_id')
            module = None
            if str(id_val).isdigit():
                module = PartnerTeamMember.objects.filter(
                    Q(id=int(id_val)) | Q(PartnerTeamMember_id=f"PTT{str(id_val).zfill(9)}") | Q(PartnerTeamMember_id=str(id_val)),
                    Is_Deleted=False
                ).first()
            if not module and id_val:
                module = PartnerTeamMember.objects.filter(
                    Q(PartnerTeamMember_id=str(id_val)) | Q(Email__iexact=str(id_val)),
                    Is_Deleted=False
                ).first()
            if not module:
                return HttpResponse(JSONRenderer().render({"Error": "Partner team member not found"}), content_type='application/json', status=status.HTTP_404_NOT_FOUND)
            serializer = PartnerTeamMemberSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerTeamMember.objects.get(id=id)
            serializer = PartnerTeamMemberSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerTeamMember.objects.get(id=id)
            serializer = PartnerTeamMemberSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerTeamMember.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




class PartnerCustomerList(ListAPIView):
    queryset = PartnerCustomer.objects.all()
    serializer_class = PartnerCustomerSerializers

    def get_queryset(self):
        try:
            module = PartnerCustomer.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")

class PartnerCustomerWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerCustomer.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerCustomerSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class PartnerCustomerCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PartnerCustomerSerializer(data=data)
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
            module = PartnerCustomer.objects.get(id=id)
            serializer = PartnerCustomerSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = PartnerCustomer.objects.get(id=id)
            serializer = PartnerCustomerSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerCustomer.objects.get(id=id)
            serializer = PartnerCustomerSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerCustomer.objects.get(id=id)
            serializer = PartnerCustomerSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerCustomer.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PartnerDealList(ListAPIView):
    queryset = PartnerDeal.objects.all()
    serializer_class = PartnerDealSerializers

    def get_queryset(self):
        try:
            module = PartnerDeal.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")

class PartnerDealWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerDeal.objects.filter(Q(Is_Deleted__exact=False)).order_by('-pk')
            serialize = PartnerDealSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class PartnerDealCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = PartnerDealSerializer(data=data)
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
            module = PartnerDeal.objects.get(id=id)
            serializer = PartnerDealSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = PartnerDeal.objects.get(id=id)
            serializer = PartnerDealSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerDeal.objects.get(id=id)
            serializer = PartnerDealSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerDeal.objects.get(id=id)
            serializer = PartnerDealSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerDeal.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TicketmanagemntListSuperadmin(ListAPIView):
    queryset = TicketManagement.objects.all()
    serializer_class = TicketManagementSerializers

    def get_queryset(self):
        try:
            video = TicketManagement.objects.filter(Q(Is_Deleted=False)).order_by('-pk')
            return video
        except Exception as e:
            raise Exception(f"Error while fetching video: {str(e)}")



from django.core.mail import EmailMultiAlternatives, get_connection


# import logging
# import html

# from django.conf import settings
# from django.core.mail import EmailMultiAlternatives, get_connection
# from django.core.validators import validate_email
# from django.core.exceptions import ValidationError

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework import status
# from rest_framework_simplejwt.authentication import JWTAuthentication

# from CRMSuperAdmin.models import Leads

# logger = logging.getLogger(__name__)


# # done by shajitha on 19-11-2026
# # partner Registration Invitation Email API

# class PartnerRegistrationInvitationEmail(APIView):

#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):

#         try:

#             # Get payload details
#             lead_id = request.data.get('LeadId')
#             sender_mailid = request.data.get('sender_mailid')

#             registration_link = "https://partner.pegatto.com/partner-registration"

#             if not lead_id:
#                 return Response({
#                     "status": False,
#                     "message": "LeadId is required"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             if not sender_mailid:
#                 return Response({
#                     "status": False,
#                     "message": "sender_mailid is required"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # Validate sender email
#             try:
#                 validate_email(sender_mailid)
#             except ValidationError:
#                 return Response({
#                     "status": False,
#                     "message": "Invalid sender email address"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # Get Lead details
#             try:
#                 Lead_Data = Leads.objects.get(
#                     LeadId=lead_id,
#                     Is_Deleted=False
#                 )

#             except Leads.DoesNotExist:
#                 return Response({
#                     "status": False,
#                     "message": "Lead not found"
#                 }, status=status.HTTP_404_NOT_FOUND)

#             # Get configured sender email for this lead's organization
#             try:
#                 Mail_Config = UserMailConfiguration.objects.get(
#                     MailId__iexact=sender_mailid
#                 )

#             except UserMailConfiguration.DoesNotExist:
#                 Mail_Config = UserMailConfiguration.objects.first()
#                 if not Mail_Config:
#                     return Response({
#                         "status": False,
#                         "message": "Sender email is not configured. Please configure your email settings first."
#                     }, status=status.HTTP_404_NOT_FOUND)

#             except UserMailConfiguration.MultipleObjectsReturned:
#                 Mail_Config = UserMailConfiguration.objects.filter(
#                     MailId__iexact=sender_mailid
#                 ).first()

#             # Dynamic registration link with query params for auto-filling
#             origin = request.headers.get('Origin') or request.headers.get('Referer') or "https://partner.pegatto.com"
#             base_url = origin.split('/partner-')[0].split('/service')[0].rstrip('/')
#             registration_link = f"{base_url}/partner-registration?lead_id={Lead_Data.id}&lead_code={Lead_Data.LeadId}&email={Lead_Data.EmailId}"

#             # Get recipient email from Leads table
#             partner_email = Lead_Data.EmailId

#             if not partner_email:
#                 return Response({
#                     "status": False,
#                     "message": "Lead email address is not available"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # Validate recipient email
#             try:
#                 validate_email(partner_email)
#             except ValidationError:
#                 return Response({
#                     "status": False,
#                     "message": "Invalid lead email address"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # Get lead name
#             partner_name = (
#                 Lead_Data.LeadFirstName or
#                 Lead_Data.CompanyName or
#                 "Partner"
#             )

#             subject = "Welcome to Pegatto - Partner Registration Invitation"

#             plain_message = f"""
# Dear {partner_name},

# We are excited to have you as a Pegatto Partner!

# We are delighted to welcome you to our partner network.

# To continue your onboarding process, please click the
# registration link below and complete the required details.

# Register Here:
# {registration_link}

# Once your registration is completed, our team will guide
# you through the next steps.

# We look forward to welcoming you to the Pegatto team!

# Best Regards,
# Pegatto Team
#             """

#             safe_name = html.escape(partner_name)
#             safe_link = html.escape(registration_link, quote=True)

#             html_message = f"""
#             <html>
#             <body style="font-family: Arial, sans-serif;
#                          color: #333;
#                          line-height: 1.6;">

#                 <h2>Welcome to Pegatto!</h2>

#                 <p>Dear <strong>{safe_name}</strong>,</p>

#                 <p>
#                     We are excited to have you as a
#                     <strong>Pegatto Partner!</strong>
#                 </p>

#                 <p>
#                     We are delighted to welcome you to our
#                     partner network.
#                 </p>

#                 <p>
#                     To continue your onboarding process,
#                     please click the button below and complete
#                     the required registration details.
#                 </p>

#                 <p style="margin: 30px 0;">
#                     <a href="{safe_link}"
#                        style="background-color: #2563eb;
#                               color: #ffffff;
#                               padding: 14px 28px;
#                               text-decoration: none;
#                               border-radius: 6px;
#                               font-weight: bold;">
#                         Click Here to Register
#                     </a>
#                 </p>

#                 <p>
#                     Once your registration is completed,
#                     our team will guide you through the next steps.
#                 </p>

#                 <p>
#                     We look forward to welcoming you
#                     to the Pegatto team!
#                 </p>

#                 <br>

#                 <p>
#                     Best Regards,<br>
#                     <strong>Pegatto Team</strong>
#                 </p>

#             </body>
#             </html>
#             """

#             # Create SMTP connection using UserMailConfiguration
#             smtp_port = int(Mail_Config.SMTPPort)

#             connection = get_connection(
#                 host=Mail_Config.SMTPHost,
#                 port=smtp_port,
#                 username=Mail_Config.MailId,
#                 password=Mail_Config.MailPassword,
#                 use_tls=(smtp_port == 587),
#                 use_ssl=(smtp_port == 465),
#                 fail_silently=False
#             )

#             # Create email using configured sender account
#             email = EmailMultiAlternatives(
#                 subject=subject,
#                 body=plain_message,
#                 from_email=Mail_Config.MailId,
#                 to=[partner_email],
#                 reply_to=[Mail_Config.MailId],
#                 connection=connection
#             )

#             # Attach HTML content
#             email.attach_alternative(
#                 html_message,
#                 "text/html"
#             )

#             # Send email
#             email.send(fail_silently=False)

#             # Update Lead status only after successful email sending
#             Lead_Data.Lead_Status = "Mail sent"

#             Lead_Data.save(update_fields=[
#                 'Lead_Status',
#                 'Updated_Date'
#             ])

#             return Response({
#                 "status": True,
#                 "message": "Registration invitation email sent successfully",
#                 "data": {
#                     "LeadId": Lead_Data.LeadId,
#                     "Lead_Name": partner_name,
#                     "To_Email": partner_email,
#                     "Sender_Email": Mail_Config.MailId,
#                     "Registration_Link": registration_link,
#                     "Lead_Status": Lead_Data.Lead_Status
#                 }
#             }, status=status.HTTP_200_OK)

#         except Exception as e:

#             logger.exception(
#                 "Lead registration invitation email failed"
#             )

#             return Response({
#                 "status": False,
#                 "message": "Failed to send registration invitation email",
#                 "error": str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






# =============================================================================
# DASHBOARD APIS (SuperAdmin/User, Partner, and Partner Team Member)
# =============================================================================

from django.db.models import Count, Sum, Avg, Q
from authapp.models import User
from CRMSuperAdmin.models import Leads, Deal, Account, TicketManagement
from partner.models import Partner, PartnerTeamMember, PartnerCustomerLead, PartnerDeal, PartnerCustomer
from partneracademy.models import ModuleEnrollment, VideoProgress, Certificate, AcademyNotification


# Status buckets (case-insensitive). Adjust if your app uses different values.
PENDING_STATUSES = ['PENDING', 'SUBMITTED', 'UNDER_REVIEW', 'IN_REVIEW', 'IN_PROGRESS']
APPROVED_STATUSES = ['APPROVED', 'VERIFIED', 'ACTIVE', 'COMPLETED']
REJECTED_STATUSES = ['REJECTED', 'DECLINED', 'FAILED']
SIGNED_STATUSES = ['SIGNED', 'EXECUTED', 'COMPLETED', 'ACTIVE']


def _status_q(field, values):
    """Build an OR of case-insensitive exact matches for a status field."""
    q = Q()
    for v in values:
        q |= Q(**{f"{field}__iexact": v})
    return q


def _status_counts(qs, field):
    """{status_value: count}, with blank/None grouped under 'UNKNOWN'."""
    out = {}
    for row in qs.values(field).annotate(count=Count('id')):
        key = (row[field] or 'UNKNOWN').upper()
        out[key] = out.get(key, 0) + row['count']
    return out


# -----------------------------------------------------------------------------
# 1. USER / SUPER ADMIN DASHBOARD API
# -----------------------------------------------------------------------------

def _to_int(value):
    """Partner table stores KycRecord / PartnerApplication ids as varchar, so convert safely."""
    return int(value) if str(value or '').isdigit() else None


class SuperAdminUserDashboardAPIView(APIView):
    """
    API 1: Dashboard for Internal User / SuperAdmin.
    Displays:
    - User details (from request.user or payload user_id)
    - Support tickets overall metrics and recent tickets
    - Overall leads metrics and breakdown (Partner vs Customer leads)
    - Overall partners overview and breakdown
    - Partner-wise breakdown (Leads, Deals, Customers, Team Members, Tickets,
      Agreements, KYC status per partner)
    - Deals & Customer metrics
    - Partner applications overview
    - KYC verification overview (pending vs approved vs rejected)
    - Partner agreements overview (uploaded / signed counts)
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        return self._handle_dashboard(request, request.query_params)

    def post(self, request, *args, **kwargs):
        return self._handle_dashboard(request, request.data)

    def _handle_dashboard(self, request, params):
        try:
            # 1. Current User Details
            user_id = params.get('user_id') or params.get('User_Id')
            current_user = None
            if user_id:
                current_user = User.objects.filter(id=user_id).first()
            if not current_user and getattr(request, 'user', None) and request.user.is_authenticated:
                current_user = request.user
            if not current_user:
                current_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

            user_details = {
                "id": getattr(current_user, 'id', None),
                "username": getattr(current_user, 'username', ''),
                "first_name": getattr(current_user, 'first_name', ''),
                "last_name": getattr(current_user, 'last_name', ''),
                "full_name": f"{getattr(current_user, 'first_name', '')} {getattr(current_user, 'last_name', '')}".strip() or getattr(current_user, 'username', ''),
                "email": getattr(current_user, 'email', ''),
                "phone_no": getattr(current_user, 'PhoneNo', ''),
                "designation": getattr(current_user, 'Designation', ''),
                "user_type": getattr(current_user, 'UserType', ''),
                "roll_name": getattr(current_user, 'Roll_Name', ''),
                "organization_id": getattr(current_user, 'Organization_Id', 1),
            }

            # 2. Overall Support Tickets
            all_tickets = TicketManagement.objects.filter(Is_Deleted=False)
            total_tickets = all_tickets.count()
            ticket_status_counts = dict(all_tickets.values('Ticket_Status').annotate(count=Count('id')).values_list('Ticket_Status', 'count'))
            ticket_priority_counts = dict(all_tickets.values('Priority').annotate(count=Count('id')).values_list('Priority', 'count'))
            recent_tickets = list(all_tickets.order_by('-pk')[:10].values(
                'id', 'TicketManagement_Id', 'Related_Module', 'Ticket_Status',
                'Priority', 'Category', 'Assigned_Person', 'Created_Date',
                'Partner_Id__Legal_Name', 'Partner_Id__Partner_Id'
            ))

            # 3. Overall Leads
            all_leads = Leads.objects.filter(Is_Deleted=False)
            total_leads = all_leads.count()
            leads_status_counts = dict(all_leads.values('Lead_Status').annotate(count=Count('id')).values_list('Lead_Status', 'count'))
            leads_type_counts = dict(all_leads.values('Partner_Or_Customer_Leads').annotate(count=Count('id')).values_list('Partner_Or_Customer_Leads', 'count'))
            recent_leads = list(all_leads.order_by('-pk')[:10].values(
                'id', 'LeadId', 'LeadFirstName', 'LeadLastName', 'CompanyName',
                'EmailId', 'PhoneNo', 'Lead_Status', 'Lead_Stage', 'Partner_Or_Customer_Leads',
                'Partner_Id__Legal_Name', 'Partner_Id__Partner_Id', 'Created_Date'
            ))

            # 4. Overall Partners Overview
            all_partners = Partner.objects.filter(Is_Deleted=False)
            total_partners = all_partners.count()
            partner_status_counts = dict(all_partners.values('Status').annotate(count=Count('id')).values_list('Status', 'count'))
            partner_tier_counts = dict(all_partners.values('Tier').annotate(count=Count('id')).values_list('Tier', 'count'))

            # 5. Partner-wise Breakdown
            # select_related fails because the Partner table has these ids as varchar,
            # so KYC and Application are fetched separately in 2 queries.
            partner_wise_summary = []
            partner_list = list(all_partners.order_by('-pk')[:50])

            kyc_ids = [_to_int(p.KycRecord_Id_id) for p in partner_list if _to_int(p.KycRecord_Id_id)]
            app_ids = [_to_int(p.PartnerApplication_Id_id) for p in partner_list if _to_int(p.PartnerApplication_Id_id)]

            kyc_map = {k.id: k for k in KycRecord.objects.filter(id__in=kyc_ids)}
            app_map = {a.id: a for a in PartnerApplication.objects.filter(id__in=app_ids)}

            for p in partner_list:
                p_leads = Leads.objects.filter(Partner_Id=p, Is_Deleted=False).count()
                p_deals = Deal.objects.filter(Partner_Id=p, Is_Deleted=False).count()
                p_cust = Account.objects.filter(Partner_Id=p, Is_Deleted=False).count()
                p_team = PartnerTeamMember.objects.filter(Partner_Id=p, Is_Deleted=False).count()
                p_tickets = TicketManagement.objects.filter(Partner_Id=p, Is_Deleted=False).count()
                p_agreements = PartnerAgreement.objects.filter(Partner_Id=p, Is_Deleted=False)
                p_agreements_total = p_agreements.count()
                p_agreements_uploaded = p_agreements.exclude(Q(File__isnull=True) | Q(File='')).count()

                kyc = kyc_map.get(_to_int(p.KycRecord_Id_id))
                app = app_map.get(_to_int(p.PartnerApplication_Id_id))

                partner_wise_summary.append({
                    "id": p.id,
                    "Partner_Id": p.Partner_Id,
                    "Partner_Code": p.Partner_Code,
                    "Legal_Name": p.Legal_Name,
                    "Trade_Name": p.Trade_Name,
                    "Tier": p.Tier,
                    "Status": p.Status,
                    "Primary_Contact_Name": p.Primary_Contact_Name,
                    "Primary_Email": p.Primary_Email,
                    "Primary_Phone": p.Primary_Phone,
                    "Rating": float(p.Rating) if p.Rating is not None else 0.0,
                    "Total_Leads": p_leads,
                    "Total_Deals": p_deals,
                    "Total_Customers": p_cust,
                    "Total_Team_Members": p_team,
                    "Total_Tickets": p_tickets,
                    "Total_Agreements": p_agreements_total,
                    "Agreements_Uploaded": p_agreements_uploaded,
                    "KYC_Status": kyc.status if kyc and not kyc.Is_Deleted else None,
                    "Application_Status": app.status if app and not app.Is_Deleted else None,
                })

            # 6. Overall Deals and Customer Accounts Metrics
            all_deals = Deal.objects.filter(Is_Deleted=False)
            total_deals = all_deals.count()
            total_deals_value = all_deals.aggregate(total=Sum('Amount'))['total'] or 0
            deal_stage_counts = dict(all_deals.values('Deal_Stage').annotate(count=Count('id')).values_list('Deal_Stage', 'count'))

            all_accounts = Account.objects.filter(Is_Deleted=False)
            total_customers = all_accounts.count()

            # 7. Partner Applications Overview
            all_applications = PartnerApplication.objects.filter(Is_Deleted=False)
            app_agg = all_applications.aggregate(
                total=Count('id'),
                pending=Count('id', filter=_status_q('status', PENDING_STATUSES) | Q(status__isnull=True) | Q(status='')),
                approved=Count('id', filter=_status_q('status', APPROVED_STATUSES)),
                rejected=Count('id', filter=_status_q('status', REJECTED_STATUSES)),
            )
            recent_applications = list(all_applications.order_by('-pk')[:10].values(
                'id', 'PartnerApplication_id', 'application_number', 'applicant_name',
                'email', 'phone', 'organisation_name', 'entity_type', 'status',
                'city', 'country', 'submitted_at'
            ))

            # 8. KYC Verification Overview
            all_kyc = KycRecord.objects.filter(Is_Deleted=False)
            kyc_agg = all_kyc.aggregate(
                total=Count('id'),
                pending=Count('id', filter=_status_q('status', PENDING_STATUSES) | Q(status__isnull=True) | Q(status='')),
                approved=Count('id', filter=_status_q('status', APPROVED_STATUSES)),
                rejected=Count('id', filter=_status_q('status', REJECTED_STATUSES)),
            )
            kyc_total = kyc_agg['total'] or 0
            kyc_approval_rate = round((kyc_agg['approved'] / kyc_total) * 100, 2) if kyc_total else 0.0
            recent_kyc = list(all_kyc.order_by('-pk')[:10].values(
                'id', 'KycRecord_id', 'partner_name', 'status',
                'verified_at', 'created_at'
            ))

            # 9. Partner Agreements Overview
            all_agreements = PartnerAgreement.objects.filter(Is_Deleted=False)
            has_file = ~(Q(File__isnull=True) | Q(File=''))
            agr_agg = all_agreements.aggregate(
                total=Count('id'),
                uploaded=Count('id', filter=has_file),
                signed=Count('id', filter=Q(signed_at__isnull=False) | _status_q('status', SIGNED_STATUSES)),
                pending_signature=Count('id', filter=Q(signed_at__isnull=True) & ~_status_q('status', SIGNED_STATUSES)),
                partners_with_agreement=Count('Partner_Id', distinct=True, filter=has_file),
            )
            recent_agreements = list(all_agreements.order_by('-pk')[:10].values(
                'id', 'PartnerAgreement_id', 'agreement_code', 'partner_org_name',
                'template_version', 'status', 'FileName', 'signed_at', 'created_at',
                'Partner_Id__Legal_Name', 'Partner_Id__Partner_Id',
                'AgreementTemplate_Id__Template_Name',
            ))
            active_templates = AgreementTemplate.objects.filter(Is_Deleted=False, Is_Active=True).count()

            return Response({
                "status": True,
                "message": "User / SuperAdmin dashboard details fetched successfully",
                "data": {
                    "user_details": user_details,
                    "support_tickets_overview": {
                        "total_tickets": total_tickets,
                        "status_counts": ticket_status_counts,
                        "priority_counts": ticket_priority_counts,
                        "recent_tickets": recent_tickets
                    },
                    "leads_overview": {
                        "total_leads": total_leads,
                        "status_counts": leads_status_counts,
                        "type_counts": leads_type_counts,
                        "recent_leads": recent_leads
                    },
                    "partners_overview": {
                        "total_partners": total_partners,
                        "status_counts": partner_status_counts,
                        "tier_counts": partner_tier_counts,
                        "partner_wise_summary": partner_wise_summary
                    },
                    "deals_overview": {
                        "total_deals": total_deals,
                        "total_deals_value": total_deals_value,
                        "stage_counts": deal_stage_counts
                    },
                    "customers_overview": {
                        "total_customers": total_customers
                    },
                    "applications_overview": {
                        "total_applications": app_agg['total'],
                        "pending_applications": app_agg['pending'],
                        "approved_applications": app_agg['approved'],
                        "rejected_applications": app_agg['rejected'],
                        "status_counts": _status_counts(all_applications, 'status'),
                        "recent_applications": recent_applications,
                    },
                    "kyc_overview": {
                        "total_kyc": kyc_total,
                        "pending_kyc": kyc_agg['pending'],
                        "approved_kyc": kyc_agg['approved'],
                        "rejected_kyc": kyc_agg['rejected'],
                        "approval_rate_percent": kyc_approval_rate,
                        "status_counts": _status_counts(all_kyc, 'status'),
                        "recent_kyc": recent_kyc,
                    },
                    "agreements_overview": {
                        "total_agreements": agr_agg['total'],
                        "uploaded_agreements": agr_agg['uploaded'],
                        "not_uploaded_agreements": agr_agg['total'] - agr_agg['uploaded'],
                        "signed_agreements": agr_agg['signed'],
                        "pending_signature": agr_agg['pending_signature'],
                        "partners_with_agreement": agr_agg['partners_with_agreement'],
                        "partners_without_agreement": max(total_partners - agr_agg['partners_with_agreement'], 0),
                        "active_templates": active_templates,
                        "status_counts": _status_counts(all_agreements, 'status'),
                        "recent_agreements": recent_agreements,
                    },
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Failed to fetch user dashboard: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)


# # -----------------------------------------------------------------------------
# # 1. USER / SUPER ADMIN DASHBOARD API
# # -----------------------------------------------------------------------------
# class SuperAdminUserDashboardAPIView(APIView):
#     """
#     API 1: Dashboard for Internal User / SuperAdmin.
#     Displays:
#     - User details (from request.user or payload user_id)
#     - Support tickets overall metrics and recent tickets
#     - Overall leads metrics and breakdown (Partner vs Customer leads)
#     - Overall partners overview and breakdown
#     - Partner-wise breakdown (Leads, Deals, Customers, Team Members, Tickets,
#       Agreements, KYC status per partner)
#     - Deals & Customer metrics
#     - [NEW] Partner applications overview
#     - [NEW] KYC verification overview (pending vs approved vs rejected)
#     - [NEW] Partner agreements overview (uploaded / signed counts)
#     """
#     authentication_classes = [JWTAuthentication]

#     def get(self, request, *args, **kwargs):
#         return self._handle_dashboard(request, request.query_params)

#     def post(self, request, *args, **kwargs):
#         return self._handle_dashboard(request, request.data)

#     def _handle_dashboard(self, request, params):
#         try:
#             # 1. Current User Details
#             user_id = params.get('user_id') or params.get('User_Id')
#             current_user = None
#             if user_id:
#                 current_user = User.objects.filter(id=user_id).first()
#             if not current_user and getattr(request, 'user', None) and request.user.is_authenticated:
#                 current_user = request.user
#             if not current_user:
#                 current_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

#             user_details = {
#                 "id": getattr(current_user, 'id', None),
#                 "username": getattr(current_user, 'username', ''),
#                 "first_name": getattr(current_user, 'first_name', ''),
#                 "last_name": getattr(current_user, 'last_name', ''),
#                 "full_name": f"{getattr(current_user, 'first_name', '')} {getattr(current_user, 'last_name', '')}".strip() or getattr(current_user, 'username', ''),
#                 "email": getattr(current_user, 'email', ''),
#                 "phone_no": getattr(current_user, 'PhoneNo', ''),
#                 "designation": getattr(current_user, 'Designation', ''),
#                 "user_type": getattr(current_user, 'UserType', ''),
#                 "roll_name": getattr(current_user, 'Roll_Name', ''),
#                 "organization_id": getattr(current_user, 'Organization_Id', 1),
#             }

#             # 2. Overall Support Tickets
#             all_tickets = TicketManagement.objects.filter(Is_Deleted=False)
#             total_tickets = all_tickets.count()
#             ticket_status_counts = dict(all_tickets.values('Ticket_Status').annotate(count=Count('id')).values_list('Ticket_Status', 'count'))
#             ticket_priority_counts = dict(all_tickets.values('Priority').annotate(count=Count('id')).values_list('Priority', 'count'))
#             recent_tickets = list(all_tickets.order_by('-pk')[:10].values(
#                 'id', 'TicketManagement_Id', 'Related_Module', 'Ticket_Status',
#                 'Priority', 'Category', 'Assigned_Person', 'Created_Date',
#                 'Partner_Id__Legal_Name', 'Partner_Id__Partner_Id'
#             ))

#             # 3. Overall Leads
#             all_leads = Leads.objects.filter(Is_Deleted=False)
#             total_leads = all_leads.count()
#             leads_status_counts = dict(all_leads.values('Lead_Status').annotate(count=Count('id')).values_list('Lead_Status', 'count'))
#             leads_type_counts = dict(all_leads.values('Partner_Or_Customer_Leads').annotate(count=Count('id')).values_list('Partner_Or_Customer_Leads', 'count'))
#             recent_leads = list(all_leads.order_by('-pk')[:10].values(
#                 'id', 'LeadId', 'LeadFirstName', 'LeadLastName', 'CompanyName',
#                 'EmailId', 'PhoneNo', 'Lead_Status', 'Lead_Stage', 'Partner_Or_Customer_Leads',
#                 'Partner_Id__Legal_Name', 'Partner_Id__Partner_Id', 'Created_Date'
#             ))

#             # 4. Overall Partners Overview
#             all_partners = Partner.objects.filter(Is_Deleted=False)
#             total_partners = all_partners.count()
#             partner_status_counts = dict(all_partners.values('Status').annotate(count=Count('id')).values_list('Status', 'count'))
#             partner_tier_counts = dict(all_partners.values('Tier').annotate(count=Count('id')).values_list('Tier', 'count'))

#             # 5. Partner-wise Breakdown
#             partner_wise_summary = []
#             for p in all_partners.select_related('KycRecord_Id', 'PartnerApplication_Id').order_by('-pk')[:50]:
#                 p_leads = Leads.objects.filter(Partner_Id=p, Is_Deleted=False).count()
#                 p_deals = Deal.objects.filter(Partner_Id=p, Is_Deleted=False).count()
#                 p_cust = Account.objects.filter(Partner_Id=p, Is_Deleted=False).count()
#                 p_team = PartnerTeamMember.objects.filter(Partner_Id=p, Is_Deleted=False).count()
#                 p_tickets = TicketManagement.objects.filter(Partner_Id=p, Is_Deleted=False).count()
#                 # [NEW] agreements per partner
#                 p_agreements = PartnerAgreement.objects.filter(Partner_Id=p, Is_Deleted=False)
#                 p_agreements_total = p_agreements.count()
#                 p_agreements_uploaded = p_agreements.exclude(Q(File__isnull=True) | Q(File='')).count()

#                 kyc = p.KycRecord_Id
#                 app = p.PartnerApplication_Id

#                 partner_wise_summary.append({
#                     "id": p.id,
#                     "Partner_Id": p.Partner_Id,
#                     "Partner_Code": p.Partner_Code,
#                     "Legal_Name": p.Legal_Name,
#                     "Trade_Name": p.Trade_Name,
#                     "Tier": p.Tier,
#                     "Status": p.Status,
#                     "Primary_Contact_Name": p.Primary_Contact_Name,
#                     "Primary_Email": p.Primary_Email,
#                     "Primary_Phone": p.Primary_Phone,
#                     "Rating": float(p.Rating) if p.Rating is not None else 0.0,
#                     "Total_Leads": p_leads,
#                     "Total_Deals": p_deals,
#                     "Total_Customers": p_cust,
#                     "Total_Team_Members": p_team,
#                     "Total_Tickets": p_tickets,
#                     # [NEW]
#                     "Total_Agreements": p_agreements_total,
#                     "Agreements_Uploaded": p_agreements_uploaded,
#                     "KYC_Status": kyc.status if kyc and not kyc.Is_Deleted else None,
#                     "Application_Status": app.status if app and not app.Is_Deleted else None,
#                 })

#             # 6. Overall Deals and Customer Accounts Metrics
#             all_deals = Deal.objects.filter(Is_Deleted=False)
#             total_deals = all_deals.count()
#             total_deals_value = all_deals.aggregate(total=Sum('Amount'))['total'] or 0
#             deal_stage_counts = dict(all_deals.values('Deal_Stage').annotate(count=Count('id')).values_list('Deal_Stage', 'count'))

#             all_accounts = Account.objects.filter(Is_Deleted=False)
#             total_customers = all_accounts.count()

#             # 7. [NEW] Partner Applications Overview
#             all_applications = PartnerApplication.objects.filter(Is_Deleted=False)
#             app_agg = all_applications.aggregate(
#                 total=Count('id'),
#                 pending=Count('id', filter=_status_q('status', PENDING_STATUSES) | Q(status__isnull=True) | Q(status='')),
#                 approved=Count('id', filter=_status_q('status', APPROVED_STATUSES)),
#                 rejected=Count('id', filter=_status_q('status', REJECTED_STATUSES)),
#             )
#             recent_applications = list(all_applications.order_by('-pk')[:10].values(
#                 'id', 'PartnerApplication_id', 'application_number', 'applicant_name',
#                 'email', 'phone', 'organisation_name', 'entity_type', 'status',
#                 'city', 'country', 'submitted_at'
#             ))

#             # 8. [NEW] KYC Verification Overview
#             all_kyc = KycRecord.objects.filter(Is_Deleted=False)
#             kyc_agg = all_kyc.aggregate(
#                 total=Count('id'),
#                 pending=Count('id', filter=_status_q('status', PENDING_STATUSES) | Q(status__isnull=True) | Q(status='')),
#                 approved=Count('id', filter=_status_q('status', APPROVED_STATUSES)),
#                 rejected=Count('id', filter=_status_q('status', REJECTED_STATUSES)),
#             )
#             kyc_total = kyc_agg['total'] or 0
#             kyc_approval_rate = round((kyc_agg['approved'] / kyc_total) * 100, 2) if kyc_total else 0.0
#             recent_kyc = list(all_kyc.order_by('-pk')[:10].values(
#                 'id', 'KycRecord_id', 'partner_name', 'status',
#                 'verified_at', 'created_at'
#             ))

#             # 9. [NEW] Partner Agreements Overview
#             all_agreements = PartnerAgreement.objects.filter(Is_Deleted=False)
#             has_file = ~(Q(File__isnull=True) | Q(File=''))
#             agr_agg = all_agreements.aggregate(
#                 total=Count('id'),
#                 uploaded=Count('id', filter=has_file),
#                 signed=Count('id', filter=Q(signed_at__isnull=False) | _status_q('status', SIGNED_STATUSES)),
#                 pending_signature=Count('id', filter=Q(signed_at__isnull=True) & ~_status_q('status', SIGNED_STATUSES)),
#                 partners_with_agreement=Count('Partner_Id', distinct=True, filter=has_file),
#             )
#             recent_agreements = list(all_agreements.order_by('-pk')[:10].values(
#                 'id', 'PartnerAgreement_id', 'agreement_code', 'partner_org_name',
#                 'template_version', 'status', 'FileName', 'signed_at', 'created_at',
#                 'Partner_Id__Legal_Name', 'Partner_Id__Partner_Id',
#                 'AgreementTemplate_Id__Template_Name',
#             ))
#             active_templates = AgreementTemplate.objects.filter(Is_Deleted=False, Is_Active=True).count()

#             return Response({
#                 "status": True,
#                 "message": "User / SuperAdmin dashboard details fetched successfully",
#                 "data": {
#                     "user_details": user_details,
#                     "support_tickets_overview": {
#                         "total_tickets": total_tickets,
#                         "status_counts": ticket_status_counts,
#                         "priority_counts": ticket_priority_counts,
#                         "recent_tickets": recent_tickets
#                     },
#                     "leads_overview": {
#                         "total_leads": total_leads,
#                         "status_counts": leads_status_counts,
#                         "type_counts": leads_type_counts,
#                         "recent_leads": recent_leads
#                     },
#                     "partners_overview": {
#                         "total_partners": total_partners,
#                         "status_counts": partner_status_counts,
#                         "tier_counts": partner_tier_counts,
#                         "partner_wise_summary": partner_wise_summary
#                     },
#                     "deals_overview": {
#                         "total_deals": total_deals,
#                         "total_deals_value": total_deals_value,
#                         "stage_counts": deal_stage_counts
#                     },
#                     "customers_overview": {
#                         "total_customers": total_customers
#                     },
#                     # ---------------- NEW SECTIONS ----------------
#                     "applications_overview": {
#                         "total_applications": app_agg['total'],
#                         "pending_applications": app_agg['pending'],
#                         "approved_applications": app_agg['approved'],
#                         "rejected_applications": app_agg['rejected'],
#                         "status_counts": _status_counts(all_applications, 'status'),
#                         "recent_applications": recent_applications,
#                     },
#                     "kyc_overview": {
#                         "total_kyc": kyc_total,
#                         "pending_kyc": kyc_agg['pending'],
#                         "approved_kyc": kyc_agg['approved'],
#                         "rejected_kyc": kyc_agg['rejected'],
#                         "approval_rate_percent": kyc_approval_rate,
#                         "status_counts": _status_counts(all_kyc, 'status'),
#                         "recent_kyc": recent_kyc,
#                     },
#                     "agreements_overview": {
#                         "total_agreements": agr_agg['total'],
#                         "uploaded_agreements": agr_agg['uploaded'],
#                         "not_uploaded_agreements": agr_agg['total'] - agr_agg['uploaded'],
#                         "signed_agreements": agr_agg['signed'],
#                         "pending_signature": agr_agg['pending_signature'],
#                         "partners_with_agreement": agr_agg['partners_with_agreement'],
#                         "partners_without_agreement": max(total_partners - agr_agg['partners_with_agreement'], 0),
#                         "active_templates": active_templates,
#                         "status_counts": _status_counts(all_agreements, 'status'),
#                         "recent_agreements": recent_agreements,
#                     },
#                 }
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({
#                 "status": False,
#                 "message": f"Failed to fetch user dashboard: {str(e)}"
#             }, status=status.HTTP_400_BAD_REQUEST)



# # -----------------------------------------------------------------------------
# # 1. USER / SUPER ADMIN DASHBOARD API
# # -----------------------------------------------------------------------------
# class SuperAdminUserDashboardAPIView(APIView):
#     """
#     API 1: Dashboard for Internal User / SuperAdmin.
#     Displays:
#     - User details (from request.user or payload user_id)
#     - Support tickets overall metrics and recent tickets
#     - Overall leads metrics and breakdown (Partner vs Customer leads)
#     - Overall partners overview and breakdown
#     - Partner-wise breakdown (Leads, Deals, Customers, Team Members, Tickets per partner)
#     - Deals & Customer metrics
#     """
#     authentication_classes = [JWTAuthentication]

#     def get(self, request, *args, **kwargs):
#         return self._handle_dashboard(request, request.query_params)

#     def post(self, request, *args, **kwargs):
#         return self._handle_dashboard(request, request.data)

#     def _handle_dashboard(self, request, params):
#         try:
#             # 1. Current User Details
#             user_id = params.get('user_id') or params.get('User_Id')
#             current_user = None
#             if user_id:
#                 current_user = User.objects.filter(id=user_id).first()
#             if not current_user and getattr(request, 'user', None) and request.user.is_authenticated:
#                 current_user = request.user
#             if not current_user:
#                 current_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

#             user_details = {
#                 "id": getattr(current_user, 'id', None),
#                 "username": getattr(current_user, 'username', ''),
#                 "first_name": getattr(current_user, 'first_name', ''),
#                 "last_name": getattr(current_user, 'last_name', ''),
#                 "full_name": f"{getattr(current_user, 'first_name', '')} {getattr(current_user, 'last_name', '')}".strip() or getattr(current_user, 'username', ''),
#                 "email": getattr(current_user, 'email', ''),
#                 "phone_no": getattr(current_user, 'PhoneNo', ''),
#                 "designation": getattr(current_user, 'Designation', ''),
#                 "user_type": getattr(current_user, 'UserType', ''),
#                 "roll_name": getattr(current_user, 'Roll_Name', ''),
#                 "organization_id": getattr(current_user, 'Organization_Id', 1),
#             }

#             # 2. Overall Support Tickets
#             all_tickets = TicketManagement.objects.filter(Is_Deleted=False)
#             total_tickets = all_tickets.count()
#             ticket_status_counts = dict(all_tickets.values('Ticket_Status').annotate(count=Count('id')).values_list('Ticket_Status', 'count'))
#             ticket_priority_counts = dict(all_tickets.values('Priority').annotate(count=Count('id')).values_list('Priority', 'count'))
#             recent_tickets = list(all_tickets.order_by('-pk')[:10].values(
#                 'id', 'TicketManagement_Id', 'Related_Module', 'Ticket_Status',
#                 'Priority', 'Category', 'Assigned_Person', 'Created_Date',
#                 'Partner_Id__Legal_Name', 'Partner_Id__Partner_Id'
#             ))

#             # 3. Overall Leads
#             all_leads = Leads.objects.filter(Is_Deleted=False)
#             total_leads = all_leads.count()
#             leads_status_counts = dict(all_leads.values('Lead_Status').annotate(count=Count('id')).values_list('Lead_Status', 'count'))
#             leads_type_counts = dict(all_leads.values('Partner_Or_Customer_Leads').annotate(count=Count('id')).values_list('Partner_Or_Customer_Leads', 'count'))
#             recent_leads = list(all_leads.order_by('-pk')[:10].values(
#                 'id', 'LeadId', 'LeadFirstName', 'LeadLastName', 'CompanyName',
#                 'EmailId', 'PhoneNo', 'Lead_Status', 'Lead_Stage', 'Partner_Or_Customer_Leads',
#                 'Partner_Id__Legal_Name', 'Partner_Id__Partner_Id', 'Created_Date'
#             ))

#             # 4. Overall Partners Overview
#             all_partners = Partner.objects.filter(Is_Deleted=False)
#             total_partners = all_partners.count()
#             partner_status_counts = dict(all_partners.values('Status').annotate(count=Count('id')).values_list('Status', 'count'))
#             partner_tier_counts = dict(all_partners.values('Tier').annotate(count=Count('id')).values_list('Tier', 'count'))

#             # 5. Partner-wise Breakdown (Leads, Deals, Customers, Team Members, Tickets)
#             partner_wise_summary = []
#             for p in all_partners.order_by('-pk')[:50]:
#                 p_leads = Leads.objects.filter(Partner_Id=p, Is_Deleted=False).count()
#                 p_deals = Deal.objects.filter(Partner_Id=p, Is_Deleted=False).count()
#                 p_cust = Account.objects.filter(Partner_Id=p, Is_Deleted=False).count()
#                 p_team = PartnerTeamMember.objects.filter(Partner_Id=p, Is_Deleted=False).count()
#                 p_tickets = TicketManagement.objects.filter(Partner_Id=p, Is_Deleted=False).count()
#                 partner_wise_summary.append({
#                     "id": p.id,
#                     "Partner_Id": p.Partner_Id,
#                     "Partner_Code": p.Partner_Code,
#                     "Legal_Name": p.Legal_Name,
#                     "Trade_Name": p.Trade_Name,
#                     "Tier": p.Tier,
#                     "Status": p.Status,
#                     "Primary_Contact_Name": p.Primary_Contact_Name,
#                     "Primary_Email": p.Primary_Email,
#                     "Primary_Phone": p.Primary_Phone,
#                     "Rating": float(p.Rating) if p.Rating is not None else 0.0,
#                     "Total_Leads": p_leads,
#                     "Total_Deals": p_deals,
#                     "Total_Customers": p_cust,
#                     "Total_Team_Members": p_team,
#                     "Total_Tickets": p_tickets,
#                 })

#             # 6. Overall Deals and Customer Accounts Metrics
#             all_deals = Deal.objects.filter(Is_Deleted=False)
#             total_deals = all_deals.count()
#             total_deals_value = all_deals.aggregate(total=Sum('Amount'))['total'] or 0
#             deal_stage_counts = dict(all_deals.values('Deal_Stage').annotate(count=Count('id')).values_list('Deal_Stage', 'count'))

#             all_accounts = Account.objects.filter(Is_Deleted=False)
#             total_customers = all_accounts.count()

#             return Response({
#                 "status": True,
#                 "message": "User / SuperAdmin dashboard details fetched successfully",
#                 "data": {
#                     "user_details": user_details,
#                     "support_tickets_overview": {
#                         "total_tickets": total_tickets,
#                         "status_counts": ticket_status_counts,
#                         "priority_counts": ticket_priority_counts,
#                         "recent_tickets": recent_tickets
#                     },
#                     "leads_overview": {
#                         "total_leads": total_leads,
#                         "status_counts": leads_status_counts,
#                         "type_counts": leads_type_counts,
#                         "recent_leads": recent_leads
#                     },
#                     "partners_overview": {
#                         "total_partners": total_partners,
#                         "status_counts": partner_status_counts,
#                         "tier_counts": partner_tier_counts,
#                         "partner_wise_summary": partner_wise_summary
#                     },
#                     "deals_overview": {
#                         "total_deals": total_deals,
#                         "total_deals_value": total_deals_value,
#                         "stage_counts": deal_stage_counts
#                     },
#                     "customers_overview": {
#                         "total_customers": total_customers
#                     }
#                 }
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({
#                 "status": False,
#                 "message": f"Failed to fetch user dashboard: {str(e)}"
#             }, status=status.HTTP_400_BAD_REQUEST)




# # -----------------------------------------------------------------------------
# # 2. PARTNER DASHBOARD API
# # -----------------------------------------------------------------------------
# class PartnerDashboardAPIView(APIView):
#     """
#     API 2: Dashboard for Partner.
#     Uses Partner_Id from payload / query params.
#     Displays:
#     - Partner details
#     - Leads created/assigned for that partner
#     - Members created for that partner
#     - Deals & customers for that partner
#     - Support tickets for that partner & partner-created support tickets
#     """
#     authentication_classes = [JWTAuthentication]

#     def get(self, request, *args, **kwargs):
#         return self._handle_dashboard(request, request.query_params)

#     def post(self, request, *args, **kwargs):
#         return self._handle_dashboard(request, request.data)

#     def _handle_dashboard(self, request, params):
#         try:
#             partner_id = params.get('Partner_Id') or params.get('partner_id') or params.get('id')
#             partner = None

#             if partner_id:
#                 if str(partner_id).isdigit():
#                     partner = Partner.objects.filter(Q(id=int(partner_id)) | Q(Partner_Id=partner_id), Is_Deleted=False).first()
#                 else:
#                     partner = Partner.objects.filter(Q(Partner_Id=partner_id) | Q(Partner_Code=partner_id), Is_Deleted=False).first()

#             if not partner and getattr(request, 'user', None) and getattr(request.user, 'Partner_Id', None):
#                 partner = request.user.Partner_Id

#             if not partner:
#                 return Response({
#                     "status": False,
#                     "message": "Partner_Id is required or valid partner not found"
#                 }, status=status.HTTP_404_NOT_FOUND)

#             # 1. Partner Details
#             partner_details = {
#                 "id": partner.id,
#                 "Partner_Id": partner.Partner_Id,
#                 "Partner_Code": partner.Partner_Code,
#                 "Legal_Name": partner.Legal_Name,
#                 "Trade_Name": partner.Trade_Name,
#                 "Tier": partner.Tier,
#                 "Status": partner.Status,
#                 "Country": partner.Country,
#                 "City": partner.City,
#                 "Primary_Contact_Name": partner.Primary_Contact_Name,
#                 "Primary_Email": partner.Primary_Email,
#                 "Primary_Phone": partner.Primary_Phone,
#                 "Website": partner.Website,
#                 "Rating": float(partner.Rating) if partner.Rating is not None else 0.0,
#                 "Partner_Type": partner.Partner_Type,
#                 "Created_Date": partner.Created_Date,
#             }

#             # 2. Team Members Created for that Partner
#             team_qs = PartnerTeamMember.objects.filter(Partner_Id=partner, Is_Deleted=False)
#             total_members = team_qs.count()
#             active_members = team_qs.filter(Is_Active=True).count()
#             team_members_list = list(team_qs.order_by('-pk').values(
#                 'id', 'PartnerTeamMember_id', 'First_Name', 'Last_Name',
#                 'Email', 'Phone_Number', 'Role', 'Designation', 'Profile_Image',
#                 'Is_Primary_User', 'Is_Active', 'Created_Date'
#             ))

#             # 3. Leads for that Partner
#             leads_qs = Leads.objects.filter(
#                 Q(Partner_Id=partner) | Q(Partner_Id__Partner_Id=partner.Partner_Id),
#                 Is_Deleted=False
#             )
#             total_leads = leads_qs.count()
#             if total_leads == 0:
#                 pcl_qs = PartnerCustomerLead.objects.filter(
#                     Q(Partner_Id=partner) | Q(Partner_Id__Partner_Id=partner.Partner_Id),
#                     Is_Deleted=False
#                 )
#                 total_leads = pcl_qs.count()
#                 leads_status_counts = dict(pcl_qs.values('lead_status').annotate(count=Count('id')).values_list('lead_status', 'count'))
#                 leads_stage_counts = dict(pcl_qs.values('Lead_Stage').annotate(count=Count('id')).values_list('Lead_Stage', 'count'))
#                 leads_list = list(pcl_qs.order_by('-pk')[:15].values(
#                     'id', 'lead_code', 'customer_name', 'company_name',
#                     'email', 'phone', 'lead_status', 'Lead_Stage', 'created_at'
#                 ))
#             else:
#                 leads_status_counts = dict(leads_qs.values('Lead_Status').annotate(count=Count('id')).values_list('Lead_Status', 'count'))
#                 leads_stage_counts = dict(leads_qs.values('Lead_Stage').annotate(count=Count('id')).values_list('Lead_Stage', 'count'))
#                 leads_list = list(leads_qs.order_by('-pk')[:15].values(
#                     'id', 'LeadId', 'LeadFirstName', 'LeadLastName', 'CompanyName',
#                     'EmailId', 'PhoneNo', 'Lead_Status', 'Lead_Stage', 'Created_Date'
#                 ))

#             # 4. Deals for that Partner
#             deals_qs = Deal.objects.filter(
#                 Q(Partner_Id=partner) | Q(Partner_Id__Partner_Id=partner.Partner_Id),
#                 Is_Deleted=False
#             )
#             total_deals = deals_qs.count()
#             deals_pipeline_value = deals_qs.aggregate(total=Sum('Amount'))['total'] or 0
#             deals_stage_counts = dict(deals_qs.values('Deal_Stage').annotate(count=Count('id')).values_list('Deal_Stage', 'count'))
#             deals_list = list(deals_qs.order_by('-pk')[:10].values(
#                 'id', 'Deal_Id', 'Deal_Name', 'Deal_Type', 'Amount', 'Deal_Stage', 'ExpClosing_Date'
#             ))

#             # 5. Customers for that Partner
#             cust_qs = Account.objects.filter(
#                 Q(Partner_Id=partner) | Q(Partner_Id__Partner_Id=partner.Partner_Id),
#                 Is_Deleted=False
#             )
#             total_customers = cust_qs.count()
#             customers_list = list(cust_qs.order_by('-pk')[:10].values(
#                 'id', 'Account_Id', 'Contact_Name', 'Account_Owner', 'Phone_Number', 'Mail', 'City'
#             ))

#             # 6. Support Tickets for that Partner & Partner Created Tickets
#             tickets_qs = TicketManagement.objects.filter(
#                 Q(Partner_Id=partner) | Q(Partner_Id__Partner_Id=partner.Partner_Id),
#                 Is_Deleted=False
#             )
#             total_tickets = tickets_qs.count()
#             ticket_status_counts = dict(tickets_qs.values('Ticket_Status').annotate(count=Count('id')).values_list('Ticket_Status', 'count'))
#             ticket_priority_counts = dict(tickets_qs.values('Priority').annotate(count=Count('id')).values_list('Priority', 'count'))
#             tickets_list = list(tickets_qs.order_by('-pk')[:15].values(
#                 'id', 'TicketManagement_Id', 'Related_Module', 'Ticket_Status',
#                 'Priority', 'Category', 'Ticket_Description', 'Created_Date', 'Assigned_Person'
#             ))

#             return Response({
#                 "status": True,
#                 "message": "Partner dashboard details fetched successfully",
#                 "data": {
#                     "partner_details": partner_details,
#                     "team_members_overview": {
#                         "total_members": total_members,
#                         "active_members": active_members,
#                         "members_list": team_members_list
#                     },
#                     "leads_overview": {
#                         "total_leads": total_leads,
#                         "status_counts": leads_status_counts,
#                         "stage_counts": leads_stage_counts,
#                         "leads_list": leads_list
#                     },
#                     "deals_overview": {
#                         "total_deals": total_deals,
#                         "deals_pipeline_value": deals_pipeline_value,
#                         "stage_counts": deals_stage_counts,
#                         "deals_list": deals_list
#                     },
#                     "customers_overview": {
#                         "total_customers": total_customers,
#                         "customers_list": customers_list
#                     },
#                     "support_tickets_overview": {
#                         "total_tickets": total_tickets,
#                         "status_counts": ticket_status_counts,
#                         "priority_counts": ticket_priority_counts,
#                         "tickets_list": tickets_list
#                     }
#                 }
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({
#                 "status": False,
#                 "message": f"Failed to fetch partner dashboard: {str(e)}"
#             }, status=status.HTTP_400_BAD_REQUEST)



# -----------------------------------------------------------------------------
# PARTNER DASHBOARD (combined: CRM + Academy) — one call for the whole page
#   GET  /PartnerDashboard/?Partner_Id=PTR001      (or ?Partner=1 / ?id=1 / ?partner_id=..)
#   POST /PartnerDashboard/   {"Partner_Id": "PTR001"}
# Falls back to the logged-in user's partner when no id is passed.
# -----------------------------------------------------------------------------
from django.db.models import Q, Count, Sum
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from partneracademy.models import *
from partner.models import *
from CRMSuperAdmin.models import *
from partneracademy.views import (
    _get_partner, _partner_products, _product_summary,
    _certificate_info, _video_brief, _num,
)

def _hours_minutes(seconds):
    seconds = int(seconds or 0)
    hours, minutes = seconds // 3600, (seconds % 3600) // 60
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"


def _count_by(qs, field):
    """{value: count} grouped on one field."""
    return dict(qs.values(field).annotate(count=Count("id")).values_list(field, "count"))


class PartnerDashboardAPIView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        return self._handle(request, request.query_params)

    def post(self, request, *args, **kwargs):
        return self._handle(request, request.data)

    # ------------------------------------------------------------------ main
    def _handle(self, request, params):
        try:
            partner = self._resolve_partner(request, params)
            if not partner:
                return Response({"status": False,
                                 "message": "Partner_Id is required or valid partner not found"},
                                status=status.HTTP_404_NOT_FOUND)

            # Each section is built independently: if one fails, the rest of the
            # dashboard still loads and the failure is reported in "errors".
            errors = {}

            def section(name, builder):
                try:
                    return builder(partner)
                except Exception as e:
                    errors[name] = str(e)
                    return None

            data = {
                "partner_details": self._partner_details(partner),
                "team_members_overview": section("team_members_overview", self._team),
                "leads_overview": section("leads_overview", self._leads),
                "deals_overview": section("deals_overview", self._deals),
                "customers_overview": section("customers_overview", self._customers),
                "support_tickets_overview": section("support_tickets_overview", self._tickets),
                "academy": section("academy", self._academy),
            }
            if errors:
                data["errors"] = errors

            return Response({"status": True,
                             "message": "Partner dashboard details fetched successfully",
                             "data": data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": False,
                             "message": f"Failed to fetch partner dashboard: {e}"},
                            status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------- partner lookup
    def _resolve_partner(self, request, params):
        partner_id = (params.get("Partner_Id") or params.get("partner_id")
                      or params.get("Partner") or params.get("id"))
        if partner_id:
            pid = str(partner_id)
            if pid.isdigit():
                lookup = Q(id=int(pid)) | Q(Partner_Id=pid)
            else:
                lookup = Q(Partner_Id=pid) | Q(Partner_Code=pid)
            partner = Partner.objects.filter(lookup, Is_Deleted=False).first()
            if partner:
                return partner

        # academy helper (reads ?Partner= / logged-in user)
        partner = _get_partner(request)
        if partner:
            return partner

        user = getattr(request, "user", None)
        return getattr(user, "Partner_Id", None) if user else None

    # ------------------------------------------------------- 1. details
    def _partner_details(self, partner):
        return {
            "id": partner.id,
            "Partner_Id": partner.Partner_Id,
            "Partner_Code": partner.Partner_Code,
            "Partner_Name": partner.Trade_Name or partner.Legal_Name,
            "Legal_Name": partner.Legal_Name,
            "Trade_Name": partner.Trade_Name,
            "Tier": partner.Tier,
            "Status": partner.Status,
            "Country": partner.Country,
            "City": partner.City,
            "Primary_Contact_Name": partner.Primary_Contact_Name,
            "Primary_Email": partner.Primary_Email,
            "Primary_Phone": partner.Primary_Phone,
            "Website": partner.Website,
            "Rating": float(partner.Rating) if partner.Rating is not None else 0.0,
            "Partner_Type": partner.Partner_Type,
            "Created_Date": partner.Created_Date,
        }

    @staticmethod
    def _partner_q(partner):
        return Q(Partner_Id=partner) | Q(Partner_Id__Partner_Id=partner.Partner_Id)

    # ------------------------------------------------------- 2. team
    def _team(self, partner):
        qs = PartnerTeamMember.objects.filter(Partner_Id=partner, Is_Deleted=False)
        return {
            "total_members": qs.count(),
            "active_members": qs.filter(Is_Active=True).count(),
            "members_list": list(qs.order_by("-pk").values(
                "id", "PartnerTeamMember_id", "First_Name", "Last_Name",
                "Email", "Phone_Number", "Role", "Designation", "Profile_Image",
                "Is_Primary_User", "Is_Active", "Created_Date")),
        }

    # ------------------------------------------------------- 3. leads
    def _leads(self, partner):
        qs = Leads.objects.filter(self._partner_q(partner), Is_Deleted=False)
        if qs.exists():
            return {
                "source": "Leads",
                "total_leads": qs.count(),
                "status_counts": _count_by(qs, "Lead_Status"),
                "stage_counts": _count_by(qs, "Lead_Stage"),
                "leads_list": list(qs.order_by("-pk")[:15].values(
                    "id", "LeadId", "LeadFirstName", "LeadLastName", "CompanyName",
                    "EmailId", "PhoneNo", "Lead_Status", "Lead_Stage", "Created_Date")),
            }

        # fallback: partner-customer leads
        qs = PartnerCustomerLead.objects.filter(self._partner_q(partner), Is_Deleted=False)
        return {
            "source": "PartnerCustomerLead",
            "total_leads": qs.count(),
            "status_counts": _count_by(qs, "lead_status"),
            "stage_counts": _count_by(qs, "Lead_Stage"),
            "leads_list": list(qs.order_by("-pk")[:15].values(
                "id", "lead_code", "customer_name", "company_name",
                "email", "phone", "lead_status", "Lead_Stage", "created_at")),
        }

    # ------------------------------------------------------- 4. deals
    def _deals(self, partner):
        qs = Deal.objects.filter(self._partner_q(partner), Is_Deleted=False)
        return {
            "total_deals": qs.count(),
            "deals_pipeline_value": qs.aggregate(total=Sum("Amount"))["total"] or 0,
            "stage_counts": _count_by(qs, "Deal_Stage"),
            "deals_list": list(qs.order_by("-pk")[:10].values(
                "id", "Deal_Id", "Deal_Name", "Deal_Type", "Amount", "Deal_Stage", "ExpClosing_Date")),
        }

    # ------------------------------------------------------- 5. customers
    def _customers(self, partner):
        qs = Account.objects.filter(self._partner_q(partner), Is_Deleted=False)
        return {
            "total_customers": qs.count(),
            "customers_list": list(qs.order_by("-pk")[:10].values(
                "id", "Account_Id", "Contact_Name", "Account_Owner", "Phone_Number", "Mail", "City")),
        }

    # ------------------------------------------------------- 6. tickets
    def _tickets(self, partner):
        qs = TicketManagement.objects.filter(self._partner_q(partner), Is_Deleted=False)
        return {
            "total_tickets": qs.count(),
            "status_counts": _count_by(qs, "Ticket_Status"),
            "priority_counts": _count_by(qs, "Priority"),
            "tickets_list": list(qs.order_by("-pk")[:15].values(
                "id", "TicketManagement_Id", "Related_Module", "Ticket_Status",
                "Priority", "Category", "Ticket_Description", "Created_Date", "Assigned_Person")),
        }

    # ------------------------------------------------------- 7. academy
    def _academy(self, partner):
        partner_products = _partner_products(partner)

        # products
        products = []
        all_total = all_done = 0
        for product in partner_products:
            progress, states, total, done, current = _product_summary(partner, product)
            all_total += total
            all_done += done
            if total and done >= total:
                product_status = "Completed"
            elif progress:
                product_status = "In Progress"
            else:
                product_status = "Not Started"
            products.append({
                **_certificate_info(partner, product, total, done),
                "Product_Name": product,
                "Total_Modules": len({video.Module_id for video, _ in states}),
                "Total_Videos": total,
                "Completed_Videos": done,
                "Progress_Percentage": round(done * 100 / total) if total else 0,
                "Total_Duration_Seconds": sum(video.Duration_Seconds or 0 for video, _ in states),
                "Watched_Seconds": sum(row.Watched_Seconds for row in progress.values()),
                "Status": product_status,
                "Next_Video": _video_brief(current),
            })

        # progress rows
        rows = VideoProgress.objects.filter(Enrollment__Partner=partner, Is_Deleted=False) \
                                    .select_related("Video__Module")
        total_watched = rows.aggregate(s=Sum("Watched_Seconds"))["s"] or 0

        # continue watching
        last = rows.filter(Status="In Progress", Video__Is_Deleted=False, Video__Status="Published") \
                   .order_by("-Last_Watched_Date").first()
        continue_watching = None
        if last and last.Video.Module and last.Video.Module.Product_Name in partner_products:
            video = last.Video
            continue_watching = {
                **_video_brief(video),
                "Product_Name": video.Module.Product_Name,
                "Watch_Percentage": _num(last.Watch_Percentage),
                "Resume_At_Seconds": last.Last_Position_Seconds,
                "Last_Watched_Date": last.Last_Watched_Date,
            }

        # recent activity
        recent = [{
            "Video": row.Video_id,
            "Video_Title": row.Video.Video_Title,
            "Product_Name": row.Video.Module.Product_Name if row.Video.Module else None,
            "Completed_Date": row.Completed_Date,
        } for row in rows.filter(Status="Completed").order_by("-Completed_Date")[:5]]

        # module enrollments
        enrollments = ModuleEnrollment.objects.filter(Partner=partner, Is_Deleted=False)

        # certificates
        certificates = list(Certificate.objects.filter(
            Partner=partner, Is_Deleted=False, Status__in=("Issued", "Revoked", "Expired"),
        ).order_by("-id").values("id", "Certificate_Number", "Product_Name", "Status", "Issued_Date"))

        # notifications
        notes = AcademyNotification.objects.filter(Partner=partner, Is_Deleted=False)
        latest = list(notes.order_by("-id")[:5].values(
            "id", "Title", "Message", "Notification_Type", "Is_Read", "Created_Date"))

        return {
            "Summary": {
                "Overall_Percentage": round(all_done * 100 / all_total) if all_total else 0,
                "Total_Products": len(products),
                "Products_Completed": sum(1 for p in products if p["Status"] == "Completed"),
                "Products_In_Progress": sum(1 for p in products if p["Status"] == "In Progress"),
                "Total_Videos": all_total,
                "Videos_Completed": all_done,
                "Modules_Completed": enrollments.filter(Status="Completed").count(),
                "Modules_In_Progress": enrollments.filter(Status="In Progress").count(),
                "Total_Watch_Seconds": total_watched,
                "Total_Watch_Time": _hours_minutes(total_watched),
                "Certificates_Issued": sum(1 for c in certificates if c["Status"] == "Issued"),
                "Certificates_Ready_To_Claim": sum(1 for p in products if p.get("Certificate_Status") == "Eligible"),
                "Unread_Notifications": notes.filter(Is_Read=False).count(),
            },
            "Continue_Watching": continue_watching,
            "Products": products,
            "Certificates": certificates,
            "Recent_Activity": recent,
            "Notifications": latest,
        }


from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from django.db.models import Q, Count, Sum, Avg

class PartnerTeamMemberDashboardAPIView(APIView):
    """
    API 3: Dashboard for Partner Team Member.
    Uses Partner_Id and PartnerTeamMember_Id in payload / query params.
    """
    authentication_classes = [JWTAuthentication]

    def _build_dashboard(self, params):
        partner_id = params.get('Partner_Id') or params.get('partner_id')
        member_id = params.get('PartnerTeamMember_Id') or params.get('TeamMember_Id') or params.get('id')

        member = None
        if member_id:
            if str(member_id).isdigit():
                member = PartnerTeamMember.objects.filter(
                    Q(id=int(member_id)) | Q(PartnerTeamMember_id=f"PTT{str(member_id).zfill(9)}") | Q(PartnerTeamMember_id=str(member_id)),
                    Is_Deleted=False
                ).first()
            else:
                member = PartnerTeamMember.objects.filter(
                    Q(PartnerTeamMember_id=member_id) | Q(Email__iexact=member_id),
                    Is_Deleted=False
                ).first()

        if not member and partner_id:
            if str(partner_id).isdigit():
                p_filter = Q(Partner_Id=int(partner_id))
            else:
                p_filter = Q(Partner_Id__Partner_Id=partner_id) | Q(Partner_Id__Partner_Code=partner_id)
            member = PartnerTeamMember.objects.filter(p_filter, Is_Deleted=False).order_by('-Is_Primary_User', '-pk').first()

        if not member:
            return {
                "status": False,
                "message": "PartnerTeamMember_Id or valid member not found"
            }, 404

        # 1. Member details
        partner_obj = member.Partner_Id
        if not partner_obj and partner_id:
            if str(partner_id).isdigit():
                partner_obj = Partner.objects.filter(id=int(partner_id), Is_Deleted=False).first()
            else:
                partner_obj = Partner.objects.filter(Q(Partner_Id=partner_id) | Q(Partner_Code=partner_id), Is_Deleted=False).first()
        if not partner_obj:
            partner_obj = Partner.objects.filter(Is_Deleted=False).first()
        member_details = {
            "id": member.id,
            "PartnerTeamMember_id": member.PartnerTeamMember_id,
            "First_Name": member.First_Name,
            "Last_Name": member.Last_Name,
            "Full_Name": f"{member.First_Name or ''} {member.Last_Name or ''}".strip(),
            "Email": member.Email,
            "Phone_Number": member.Phone_Number,
            "Role": member.Role,
            "Designation": member.Designation,
            "Profile_Image": str(member.Profile_Image) if member.Profile_Image else '',
            "Is_Primary_User": member.Is_Primary_User,
            "Is_Active": member.Is_Active,
            "Created_Date": member.Created_Date,
            "Partner": {
                "id": partner_obj.id,
                "Partner_Id": partner_obj.Partner_Id,
                "Legal_Name": partner_obj.Legal_Name,
                "Trade_Name": partner_obj.Trade_Name,
                "Partner_Code": partner_obj.Partner_Code,
                "Tier": partner_obj.Tier,
            } if partner_obj else None
        }

        # 2. Support tickets
        if partner_obj:
            tickets_qs = TicketManagement.objects.filter(
                Q(PartnerTeamMember_Id=member) | Q(Partner_Id=partner_obj),
                Is_Deleted=False
            )
        else:
            tickets_qs = TicketManagement.objects.filter(PartnerTeamMember_Id=member, Is_Deleted=False)

        total_tickets = tickets_qs.count()
        ticket_status_counts = dict(tickets_qs.values('Ticket_Status').annotate(count=Count('id')).values_list('Ticket_Status', 'count'))
        ticket_priority_counts = dict(tickets_qs.values('Priority').annotate(count=Count('id')).values_list('Priority', 'count'))
        tickets_list = list(tickets_qs.order_by('-pk')[:15].values(
            'id', 'TicketManagement_Id', 'Related_Module', 'Ticket_Status',
            'Priority', 'Category', 'Ticket_Description', 'Created_Date', 'Assigned_Person'
        ))

        # 3a. Module enrollments
        enrollments_filter = Q(PartnerTeamMember=member)
        if partner_obj:
            enrollments_filter |= Q(Partner=partner_obj)
        enrollments_qs = ModuleEnrollment.objects.filter(enrollments_filter, Is_Deleted=False)

        total_enrolled_modules = enrollments_qs.count()
        completed_modules = enrollments_qs.filter(Status__iexact='Completed').count()
        in_progress_modules = enrollments_qs.filter(Status__iexact='In Progress').count()
        not_started_modules = enrollments_qs.filter(Status__iexact='Not Started').count()
        avg_completion = float(enrollments_qs.aggregate(avg=Avg('Completion_Percentage'))['avg'] or 0.0)

        modules_list = []
        for enr in enrollments_qs.order_by('-pk')[:15]:
            module = enr.Module
            modules_list.append({
                "Enrollment_Id": enr.Enrollment_Id,
                "Module_Id": module.TrainingProduct_Id if module else None,
                "Module_Title": module.Title if module else '',
                "Module_Name": module.Module_Name if module else '',
                "Product_Name": module.Product_Name if module else '',
                "Status": enr.Status,
                "Completion_Percentage": float(enr.Completion_Percentage) if enr.Completion_Percentage else 0.0,
                "Started_Date": enr.Started_Date,
                "Completed_Date": enr.Completed_Date,
                "Last_Accessed_Date": enr.Last_Accessed_Date,
            })

        # 3b. Video progress
        progress_qs = VideoProgress.objects.filter(Enrollment__in=enrollments_qs, Is_Deleted=False)
        total_videos_tracked = progress_qs.count()
        completed_videos = progress_qs.filter(Status__iexact='Completed').count()
        in_progress_videos = progress_qs.filter(Status__iexact='In Progress').count()
        total_watched_seconds = progress_qs.aggregate(total=Sum('Watched_Seconds'))['total'] or 0
        total_watched_minutes = round(total_watched_seconds / 60, 2)

        videos_list = []
        for prog in progress_qs.order_by('-pk')[:20]:
            videos_list.append({
                "VideoProgress_Id": prog.VideoProgress_Id,
                "Video_Title": prog.Video.Video_Title if prog.Video else '',
                "Duration_Seconds": prog.Video.Duration_Seconds if prog.Video else 0,
                "Watched_Seconds": prog.Watched_Seconds,
                "Watch_Percentage": float(prog.Watch_Percentage) if prog.Watch_Percentage else 0.0,
                "Status": prog.Status,
                "Last_Watched_Date": prog.Last_Watched_Date,
                "Completed_Date": prog.Completed_Date,
            })

        # 3c. Certificates
        cert_filter = Q(PartnerTeamMember=member)
        if partner_obj:
            cert_filter |= Q(Partner=partner_obj)
        cert_qs = Certificate.objects.filter(cert_filter, Is_Deleted=False)

        total_certificates = cert_qs.count()
        issued_certificates = cert_qs.filter(Status__iexact='Issued').count()
        is_certified = issued_certificates > 0

        certificates_list = []
        for cert in cert_qs.order_by('-pk'):
            certificates_list.append({
                "Certificate_Id": cert.Certificate_Id,
                "Certificate_Number": cert.Certificate_Number,
                "Product_Name": cert.Product_Name,
                "Status": cert.Status,
                "Issued_Date": cert.Issued_Date,
                "Expiry_Date": cert.Expiry_Date,
                "Certificate_File": str(cert.Certificate_File) if cert.Certificate_File else '',
            })

        # 3d. Notifications
        noti_filter = Q(PartnerTeamMember=member)
        if partner_obj:
            noti_filter |= Q(Partner=partner_obj)
        noti_qs = AcademyNotification.objects.filter(noti_filter, Is_Deleted=False)
        unread_notifications = noti_qs.filter(Is_Read=False).count()

        serialize = {
            "status": True,
            "message": "Partner team member dashboard details fetched successfully",
            "data": {
                "member_details": member_details,
                "support_tickets_overview": {
                    "total_tickets": total_tickets,
                    "status_counts": ticket_status_counts,
                    "priority_counts": ticket_priority_counts,
                    "tickets_list": tickets_list
                },
                "training_academy_overview": {
                    "summary": {
                        "total_enrolled_modules": total_enrolled_modules,
                        "completed_modules": completed_modules,
                        "in_progress_modules": in_progress_modules,
                        "not_started_modules": not_started_modules,
                        "average_completion_percentage": avg_completion,
                        "total_videos_tracked": total_videos_tracked,
                        "completed_videos": completed_videos,
                        "in_progress_videos": in_progress_videos,
                        "total_watched_seconds": total_watched_seconds,
                        "total_watched_minutes": total_watched_minutes,
                        "is_certified": is_certified,
                        "total_certificates": total_certificates,
                        "issued_certificates": issued_certificates,
                        "unread_notifications": unread_notifications
                    },
                    "enrolled_modules": modules_list,
                    "videos_progress": videos_list,
                    "certificates": certificates_list
                }
            }
        }
        return serialize, 200

    def get(self, request, *args, **kwargs):
        try:
            serialize, code = self._build_dashboard(request.query_params)
            return HttpResponse(JSONRenderer().render(serialize), content_type='application/json', status=code)
        except Exception as e:
            serialize = {
                "status": False,
                "message": f"Failed to fetch partner team member dashboard: {str(e)}"
            }
            return HttpResponse(JSONRenderer().render(serialize), content_type='application/json', status=400)

    def post(self, request, *args, **kwargs):
        try:
            serialize, code = self._build_dashboard(request.data)
            return HttpResponse(JSONRenderer().render(serialize), content_type='application/json', status=code)
        except Exception as e:
            serialize = {
                "status": False,
                "message": f"Failed to fetch partner team member dashboard: {str(e)}"
            }
            return HttpResponse(JSONRenderer().render(serialize), content_type='application/json', status=400)




from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError


class SuperadminTicketManagementList(ListAPIView):
    serializer_class = TicketManagementSerializers

    def get_queryset(self):
        return TicketManagement.objects.filter(
            Is_Deleted=False,
            Partner_Id__isnull=False,
            PartnerTeamMember_Id__isnull=True,
        ).order_by('-id')


class PartnerMyTicketManagementList(ListAPIView):
    serializer_class = TicketManagementSerializers

    def get_queryset(self):
        partner_id = self.request.query_params.get('partner_id')
        if not partner_id:
            raise ValidationError({"partner_id": "This query parameter is required."})

        return TicketManagement.objects.filter(
            Is_Deleted=False,
            Partner_Id=partner_id,
        ).select_related('Partner_Id').order_by('-id')


class PartnerAllTeamTicketManagementList(ListAPIView):
    serializer_class = TicketManagementSerializers

    def get_queryset(self):
        partner_id = self.request.query_params.get('partner_id')
        if not partner_id:
            raise ValidationError({"partner_id": "This query parameter is required."})

        return TicketManagement.objects.filter(
            Is_Deleted=False,
            Partner_Id=partner_id,
            PartnerTeamMember_Id__isnull=False,
        ).select_related('Partner_Id', 'PartnerTeamMember_Id', 'Assigned_To').order_by('-pk')


class PartnerTeamMemberTicketManagementList(ListAPIView):
    serializer_class = TicketManagementSerializers

    def get_queryset(self):
        team_member_id = self.request.query_params.get('partnerTeamUser_id')
        if not team_member_id:
            raise ValidationError({"partnerTeamUser_id": "This query parameter is required."})

        return TicketManagement.objects.filter(
            Is_Deleted=False,
            PartnerTeamMember_Id=team_member_id,
        ).select_related('PartnerTeamMember_Id', 'Assigned_To').order_by('-id')


# =============================================================================
# SALES PERFORMANCE & COMMERCIAL VELOCITY APIS
# =============================================================================
import datetime
import calendar


def format_inr(amount):
    """
    Format numeric value into Indian currency format: ₹1,50,000 or ₹0
    """
    if amount is None:
        return '₹0'
    try:
        val = float(amount)
    except (ValueError, TypeError):
        return '₹0'
    is_neg = val < 0
    val = abs(val)
    if val.is_integer():
        int_part = str(int(val))
        dec_part = ''
    else:
        int_part, dec_part = f"{val:.2f}".split('.')
        dec_part = '.' + dec_part

    if len(int_part) <= 3:
        formatted = int_part
    else:
        last3 = int_part[-3:]
        rem = int_part[:-3]
        groups = []
        while len(rem) > 2:
            groups.insert(0, rem[-2:])
            rem = rem[:-2]
        if rem:
            groups.insert(0, rem)
        formatted = ','.join(groups) + ',' + last3

    res = f"₹{formatted}{dec_part}"
    return f"-{res}" if is_neg else res


def get_last_n_months_ranges(n=5):
    """
    Returns last n months relative to current date, with (MTD) for the current month.
    """
    today = datetime.date.today()
    result = []
    for i in range(n - 1, -1, -1):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        m_start = datetime.date(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        m_end = datetime.date(year, month, last_day)
        is_current = (year == today.year and month == today.month)
        month_name = calendar.month_name[month]
        label = f"{month_name} {year} (MTD)" if is_current else f"{month_name} {year}"
        result.append({
            "reporting_period": label,
            "start_date": m_start,
            "end_date": today if is_current else m_end,
            "year": year,
            "month": month,
            "is_current": is_current
        })
    return result


def compute_partner_sales_analytics(partner_obj, commission_rate=10.0, time_filter='all_time'):
    """
    Helper function to compute scorecard, monthly velocity, and account-wise sales performance for a partner.
    """
    today = datetime.date.today()
    lead_date_q = Q()
    deal_date_q = Q()

    if time_filter == 'this_month':
        m_start = datetime.date(today.year, today.month, 1)
        lead_date_q = Q(Created_Date__gte=m_start)
        deal_date_q = Q(Created_Date__gte=m_start)
    elif time_filter == 'this_year':
        y_start = datetime.date(today.year, 1, 1)
        lead_date_q = Q(Created_Date__gte=y_start)
        deal_date_q = Q(Created_Date__gte=y_start)

    partner_leads_qs = Leads.objects.filter(Partner_Id=partner_obj, Is_Deleted=False).filter(lead_date_q)
    leads_generated = partner_leads_qs.count()

    qualified_leads = partner_leads_qs.filter(
        Q(LeadQualifyStatus=True) | Q(Deal_Created=True) | Q(LeadGrowth__iexact='Up')
    ).count()

    partner_deals_qs = Deal.objects.filter(Partner_Id=partner_obj, Is_Deleted=False).filter(deal_date_q)
    won_q = Q(Deal_Stage__icontains='won') | Q(Current_Status__icontains='won')
    lost_q = Q(Deal_Stage__icontains='lost') | Q(Current_Status__icontains='lost')

    won_deals = partner_deals_qs.filter(won_q)
    lost_deals = partner_deals_qs.filter(lost_q)

    deals_won = won_deals.count()
    deals_lost = lost_deals.count()

    lead_conversion_rate = round((deals_won / leads_generated * 100), 1) if leads_generated > 0 else 0.0
    win_ratio_percentage = round((deals_won / (deals_won + deals_lost) * 100), 1) if (deals_won + deals_lost) > 0 else 0.0

    total_deal_value = float(won_deals.aggregate(total=Sum('Amount'))['total'] or 0.0)
    average_deal_value = round(total_deal_value / deals_won, 2) if deals_won > 0 else 0.0

    partner_id_strs = [str(partner_obj.id), str(partner_obj.Partner_Id or ''), str(partner_obj.Partner_Code or '')]
    comm_qs = BusinessCommission.objects.filter(
        Q(partner_id__in=partner_id_strs) | Q(approval_status__iexact='approved'),
        Is_Deleted=False
    )
    db_comm = comm_qs.aggregate(total=Sum('calculated_commission'))['total']
    if db_comm and float(db_comm) > 0:
        approved_commission = float(db_comm)
    else:
        approved_commission = round(total_deal_value * (commission_rate / 100.0), 2)

    scorecard = {
        "leads_generated": {
            "value": leads_generated,
            "label": "Total referrals & allocations"
        },
        "qualified_leads": {
            "value": qualified_leads,
            "label": "Passed customer vetting"
        },
        "lead_conversion_rate": {
            "value": f"{lead_conversion_rate}%",
            "raw_percentage": lead_conversion_rate,
            "label": "Conversion to active deals"
        },
        "deals_won_lost": {
            "won": deals_won,
            "lost": deals_lost,
            "ratio_display": f"{deals_won} / {deals_lost}",
            "win_ratio": f"Win ratio: {win_ratio_percentage}%",
            "win_ratio_percentage": win_ratio_percentage
        },
        "total_deal_value": {
            "raw": total_deal_value,
            "formatted": format_inr(total_deal_value),
            "label": "Pipeline deal bookings"
        },
        "average_deal_value": {
            "raw": average_deal_value,
            "formatted": format_inr(average_deal_value),
            "label": "Average contract size"
        },
        "approved_commission_earned": {
            "raw": approved_commission,
            "formatted": format_inr(approved_commission),
            "commission_rate_percentage": commission_rate,
            "label": "Verified partner earnings from won deals"
        }
    }

    monthly_velocity = []
    months_range = get_last_n_months_ranges(5)
    for m in months_range:
        m_start = m['start_date']
        m_end = m['end_date']

        m_leads = Leads.objects.filter(
            Partner_Id=partner_obj,
            Created_Date__range=(m_start, m_end),
            Is_Deleted=False
        ).count()

        m_won_deals = Deal.objects.filter(
            Partner_Id=partner_obj,
            Is_Deleted=False
        ).filter(won_q).filter(
            Q(Won_Deal_Date__range=(m_start, m_end)) | (Q(Won_Deal_Date__isnull=True) & Q(Created_Date__range=(m_start, m_end)))
        )

        m_won_cnt = m_won_deals.count()
        m_vol = float(m_won_deals.aggregate(total=Sum('Amount'))['total'] or 0.0)
        m_comm = round(m_vol * (commission_rate / 100.0), 2)

        monthly_velocity.append({
            "reporting_period": m['reporting_period'],
            "lead_captures": f"{m_leads} leads",
            "lead_captures_count": m_leads,
            "deals_won": f"{m_won_cnt} won",
            "deals_won_count": m_won_cnt,
            "deal_volume": format_inr(m_vol),
            "deal_volume_raw": m_vol,
            "commission_earned": format_inr(m_comm),
            "commission_earned_raw": m_comm
        })

    accounts_qs = Account.objects.filter(Partner_Id=partner_obj, Is_Deleted=False)
    account_wise_performance = []

    for acc in accounts_qs:
        acc_deals_qs = acc.Deal_Id.filter(Is_Deleted=False)
        if not acc_deals_qs.exists():
            acc_deals_qs = Deal.objects.filter(
                Q(Account_Name=acc.Contact_Name) | Q(Lead_Id=acc.Lead_Id),
                Partner_Id=partner_obj,
                Is_Deleted=False
            )

        acc_total = acc_deals_qs.count()
        acc_won = acc_deals_qs.filter(won_q)
        acc_lost = acc_deals_qs.filter(lost_q)

        acc_won_cnt = acc_won.count()
        acc_lost_cnt = acc_lost.count()
        acc_deal_vol = float(acc_won.aggregate(total=Sum('Amount'))['total'] or 0.0)
        acc_comm = round(acc_deal_vol * (commission_rate / 100.0), 2)

        acc_leads_count = 1 if acc.Lead_Id else Leads.objects.filter(
            Q(CompanyName=acc.Contact_Name) | Q(EmailId=acc.Mail),
            Partner_Id=partner_obj,
            Is_Deleted=False
        ).count()

        deal_list = []
        for d in acc_deals_qs[:10]:
            deal_list.append({
                "Deal_Id": d.Deal_Id,
                "Deal_Name": d.Deal_Name,
                "Deal_Code": d.Deal_Code,
                "Amount": d.Amount,
                "formatted_amount": format_inr(d.Amount),
                "Deal_Stage": d.Deal_Stage,
                "Current_Status": d.Current_Status,
                "Won_Deal_Date": d.Won_Deal_Date,
                "Created_Date": d.Created_Date
            })

        account_wise_performance.append({
            "account_id": acc.Account_Id,
            "account_name": acc.Contact_Name or acc.Organization_Name or acc.Account_Id,
            "contact_person": acc.Contact_Name,
            "account_owner": acc.Account_Owner,
            "phone_number": acc.Phone_Number,
            "email": acc.Mail,
            "city": acc.City,
            "state": acc.State,
            "client_type": acc.Client_Type,
            "client_status": acc.Client_Status,
            "leads_count": acc_leads_count,
            "total_deals": acc_total,
            "deals_won": acc_won_cnt,
            "deals_lost": acc_lost_cnt,
            "total_deal_value": {
                "raw": acc_deal_vol,
                "formatted": format_inr(acc_deal_vol)
            },
            "commission_earned": {
                "raw": acc_comm,
                "formatted": format_inr(acc_comm)
            },
            "deals": deal_list
        })

    return {
        "scorecard": scorecard,
        "monthly_velocity": monthly_velocity,
        "account_wise_performance": account_wise_performance
    }


class PartnerSalesPerformanceAPIView(APIView):
    """
    API: Partner Sales Performance & Scorecard Analytics
    Shows the scorecard, monthly commercial velocity, and account-wise sales performance for a partner.
    Supports GET (query params) and POST (JSON body).
    """
    def get(self, request, *args, **kwargs):
        return self._handle_sales_performance(request)

    def post(self, request, *args, **kwargs):
        return self._handle_sales_performance(request)

    def _handle_sales_performance(self, request):
        try:
            # Extract partner_id if passed in payload (JSON body) or query params
            data = request.data if isinstance(request.data, dict) else {}
            partner_id = (
                request.query_params.get('partner_id')
                or request.query_params.get('Partner_Id')
                or request.query_params.get('partnerId')
                or request.query_params.get('id')
                or data.get('partner_id')
                or data.get('Partner_Id')
                or data.get('partnerId')
                or data.get('id')
            )
            time_filter = request.query_params.get('time_filter') or data.get('time_filter') or 'all_time'
            commission_rate = float(request.query_params.get('commission_rate') or data.get('commission_rate') or 10.0)

            partner_obj = None
            if partner_id is not None and str(partner_id).strip() != '':
                str_pid = str(partner_id).strip()
                p_filter = Q(Partner_Id=str_pid) | Q(Partner_Code=str_pid) | Q(Legal_Name__iexact=str_pid)
                if str_pid.isdigit():
                    p_filter |= Q(id=int(str_pid))
                partner_obj = Partner.objects.filter(p_filter).first()
            elif hasattr(request.user, 'Partner_Id') and request.user.Partner_Id:
                partner_obj = request.user.Partner_Id
            else:
                partner_obj = Partner.objects.filter(Is_Deleted=False).first()

            if not partner_obj:
                return Response({
                    "status": False,
                    "message": "Partner not found. Please provide a valid partner_id in query parameters or request body."
                }, status=status.HTTP_404_NOT_FOUND)

            analytics = compute_partner_sales_analytics(
                partner_obj,
                commission_rate=commission_rate,
                time_filter=time_filter
            )

            partner_info = {
                "id": partner_obj.id,
                "Partner_Id": partner_obj.Partner_Id,
                "Legal_Name": partner_obj.Legal_Name,
                "Trade_Name": partner_obj.Trade_Name,
                "Partner_Code": partner_obj.Partner_Code,
                "Tier": partner_obj.Tier,
                "Status": partner_obj.Status
            }

            return Response({
                "status": True,
                "message": "Partner sales performance fetched successfully",
                "partner": partner_info,
                "time_filter": time_filter,
                "scorecard": analytics["scorecard"],
                "monthly_velocity": analytics["monthly_velocity"],
                "account_wise_sales_performance": analytics["account_wise_performance"]
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Failed to fetch partner sales performance: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)


class SuperAdminSalesPerformanceAPIView(APIView):
    """
    API: SuperAdmin Sales Performance & Commercial Velocity
    Shows overall platform scorecard, monthly commercial velocity, and partner-wise account sales performance.
    Supports GET (query params) and POST (JSON body).
    """
    def get(self, request, *args, **kwargs):
        return self._handle_superadmin_sales_performance(request)

    def post(self, request, *args, **kwargs):
        return self._handle_superadmin_sales_performance(request)

    def _handle_superadmin_sales_performance(self, request):
        try:
            # Extract partner_id if passed in payload (JSON body) or query params; if not passed, shows all partners
            data = request.data if isinstance(request.data, dict) else {}
            partner_filter_id = (
                request.query_params.get('partner_id')
                or request.query_params.get('Partner_Id')
                or request.query_params.get('partnerId')
                or request.query_params.get('id')
                or data.get('partner_id')
                or data.get('Partner_Id')
                or data.get('partnerId')
                or data.get('id')
            )
            time_filter = request.query_params.get('time_filter') or data.get('time_filter') or 'all_time'
            commission_rate = float(request.query_params.get('commission_rate') or data.get('commission_rate') or 10.0)

            partners_qs = Partner.objects.filter(Is_Deleted=False)
            if partner_filter_id is not None and str(partner_filter_id).strip() != '':
                str_pid = str(partner_filter_id).strip()
                p_filter = Q(Partner_Id=str_pid) | Q(Partner_Code=str_pid) | Q(Legal_Name__iexact=str_pid)
                if str_pid.isdigit():
                    p_filter |= Q(id=int(str_pid))
                partners_qs = partners_qs.filter(p_filter)

            won_q = Q(Deal_Stage__icontains='won') | Q(Current_Status__icontains='won')
            lost_q = Q(Deal_Stage__icontains='lost') | Q(Current_Status__icontains='lost')

            all_leads_qs = Leads.objects.filter(Is_Deleted=False)
            all_deals_qs = Deal.objects.filter(Is_Deleted=False)

            total_leads_generated = all_leads_qs.count()
            total_qualified_leads = all_leads_qs.filter(
                Q(LeadQualifyStatus=True) | Q(Deal_Created=True) | Q(LeadGrowth__iexact='Up')
            ).count()

            overall_won_deals = all_deals_qs.filter(won_q)
            overall_lost_deals = all_deals_qs.filter(lost_q)

            total_deals_won = overall_won_deals.count()
            total_deals_lost = overall_lost_deals.count()

            overall_lead_conv_rate = round((total_deals_won / total_leads_generated * 100), 1) if total_leads_generated > 0 else 0.0
            overall_win_ratio = round((total_deals_won / (total_deals_won + total_deals_lost) * 100), 1) if (total_deals_won + total_deals_lost) > 0 else 0.0

            overall_deal_val = float(overall_won_deals.aggregate(total=Sum('Amount'))['total'] or 0.0)
            overall_avg_deal_val = round(overall_deal_val / total_deals_won, 2) if total_deals_won > 0 else 0.0
            overall_comm = round(overall_deal_val * (commission_rate / 100.0), 2)

            overall_scorecard = {
                "leads_generated": {
                    "value": total_leads_generated,
                    "label": "Total referrals & allocations"
                },
                "qualified_leads": {
                    "value": total_qualified_leads,
                    "label": "Passed customer vetting"
                },
                "lead_conversion_rate": {
                    "value": f"{overall_lead_conv_rate}%",
                    "raw_percentage": overall_lead_conv_rate,
                    "label": "Conversion to active deals"
                },
                "deals_won_lost": {
                    "won": total_deals_won,
                    "lost": total_deals_lost,
                    "ratio_display": f"{total_deals_won} / {total_deals_lost}",
                    "win_ratio": f"Win ratio: {overall_win_ratio}%",
                    "win_ratio_percentage": overall_win_ratio
                },
                "total_deal_value": {
                    "raw": overall_deal_val,
                    "formatted": format_inr(overall_deal_val),
                    "label": "Pipeline deal bookings"
                },
                "average_deal_value": {
                    "raw": overall_avg_deal_val,
                    "formatted": format_inr(overall_avg_deal_val),
                    "label": "Average contract size"
                },
                "approved_commission_earned": {
                    "raw": overall_comm,
                    "formatted": format_inr(overall_comm),
                    "commission_rate_percentage": commission_rate,
                    "label": "Verified partner earnings from won deals"
                },
                "total_partners_count": partners_qs.count(),
                "total_accounts_count": Account.objects.filter(Is_Deleted=False).count()
            }

            overall_monthly_velocity = []
            months_range = get_last_n_months_ranges(5)
            for m in months_range:
                m_start = m['start_date']
                m_end = m['end_date']

                m_leads_cnt = all_leads_qs.filter(Created_Date__range=(m_start, m_end)).count()
                m_won_qs = all_deals_qs.filter(won_q).filter(
                    Q(Won_Deal_Date__range=(m_start, m_end)) | (Q(Won_Deal_Date__isnull=True) & Q(Created_Date__range=(m_start, m_end)))
                )
                m_won_c = m_won_qs.count()
                m_vol = float(m_won_qs.aggregate(total=Sum('Amount'))['total'] or 0.0)
                m_c_comm = round(m_vol * (commission_rate / 100.0), 2)

                overall_monthly_velocity.append({
                    "reporting_period": m['reporting_period'],
                    "lead_captures": f"{m_leads_cnt} leads",
                    "lead_captures_count": m_leads_cnt,
                    "deals_won": f"{m_won_c} won",
                    "deals_won_count": m_won_c,
                    "deal_volume": format_inr(m_vol),
                    "deal_volume_raw": m_vol,
                    "commission_earned": format_inr(m_c_comm),
                    "commission_earned_raw": m_c_comm
                })

            partner_wise_performance = []
            for partner_obj in partners_qs:
                p_analytics = compute_partner_sales_analytics(
                    partner_obj,
                    commission_rate=commission_rate,
                    time_filter=time_filter
                )
                partner_wise_performance.append({
                    "partner_details": {
                        "id": partner_obj.id,
                        "Partner_Id": partner_obj.Partner_Id,
                        "Legal_Name": partner_obj.Legal_Name,
                        "Trade_Name": partner_obj.Trade_Name,
                        "Partner_Code": partner_obj.Partner_Code,
                        "Tier": partner_obj.Tier,
                        "Status": partner_obj.Status
                    },
                    "scorecard": p_analytics["scorecard"],
                    "monthly_velocity": p_analytics["monthly_velocity"],
                    "account_wise_sales_performance": p_analytics["account_wise_performance"]
                })

            return Response({
                "status": True,
                "message": "SuperAdmin sales performance fetched successfully",
                "time_filter": time_filter,
                "overall_scorecard": overall_scorecard,
                "overall_monthly_velocity": overall_monthly_velocity,
                "partner_wise_sales_performance": partner_wise_performance
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Failed to fetch superadmin sales performance: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)




#-------------------- Forget and Reset Password ---------------------------

# shajitha
# 24-11-26


from django.core import signing
from django.core.mail import EmailMultiAlternatives, get_connection
from django.contrib.auth.password_validation import validate_password
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

RESET_SALT = 'pegatto-reset-password'
RESET_MAX_AGE = 15 * 60  # 15 minutes

# the reset mail is always sent from this mail (row must exist in UserMailConfiguration)
RESET_SENDER_MAIL = 'shajitha@foyertech.com'

# reset page link for each type
# RESET_URLS = {
#     'partner': 'http://localhost:3005/auth/reset-password',
#     'team': 'http://localhost:3005/auth/team-reset-password',
#     'user': 'http://localhost:3005/auth/reset-password',
# }

# live:
RESET_URLS = {
    'partner': 'https://partner.pegatto.com/auth/reset-password',
    'team': 'https://partner.pegatto.com/auth/team-reset-password',
    'user': 'https://partner.pegatto.com/auth/management-reset-password',
}


def GetResetPasswordField(user_type):
    # Django User uses 'password', Partner and PartnerTeamMember use 'Password'
    return 'password' if user_type == 'user' else 'Password'


def GetResetEmail(module, user_type):
    if user_type == 'partner':
        return module.Primary_Email
    if user_type == 'team':
        return module.Email
    return module.email


def GetResetName(module):
    return (getattr(module, 'Primary_Contact_Name', None)
            or getattr(module, 'Name', None)
            or getattr(module, 'first_name', None)
            or getattr(module, 'username', None)
            or 'User')


def FindResetAccount(user_type, identifier):
    if user_type == 'partner':
        return Partner.objects.filter(
            Q(Primary_Email__iexact=identifier) | Q(Partner_Id=identifier) | Q(Partner_Code=identifier),
            Is_Deleted=False
        ).first()
    if user_type == 'team':
        return PartnerTeamMember.objects.filter(
            Q(Email__iexact=identifier) | Q(User_Id__iexact=identifier) | Q(PartnerTeamMember_id=identifier),
            Is_Deleted=False
        ).first()
    if user_type == 'user':
        return User.objects.filter(
            Q(username__iexact=identifier) | Q(email__iexact=identifier),
            is_active=True
        ).first()
    raise ValueError("user_type must be partner, team or user")


def GenerateResetToken(module, user_type):
    # last 12 chars of the current password hash are inside the token,
    # so after the password changes the old link stops working (single use)
    current_password = getattr(module, GetResetPasswordField(user_type)) or ''
    return signing.dumps(
        {'type': user_type, 'id': module.pk, 'h': current_password[-12:]},
        salt=RESET_SALT
    )


def GetAccountFromResetToken(token):
    # returns (module, user_type) or raises ValueError with a clear message
    try:
        payload = signing.loads(token, salt=RESET_SALT, max_age=RESET_MAX_AGE)
    except signing.SignatureExpired:
        raise ValueError("Reset link has expired. Please request a new one")
    except signing.BadSignature:
        raise ValueError("Invalid reset link")

    user_type = payload['type']
    if user_type == 'partner':
        module = Partner.objects.filter(id=payload['id'], Is_Deleted=False).first()
    elif user_type == 'team':
        module = PartnerTeamMember.objects.filter(id=payload['id'], Is_Deleted=False).first()
    else:
        module = User.objects.filter(id=payload['id'], is_active=True).first()

    if not module:
        raise ValueError("Account not found")

    current_password = getattr(module, GetResetPasswordField(user_type)) or ''
    if current_password[-12:] != payload['h']:
        raise ValueError("This reset link is already used. Please request a new one")
    return module, user_type


def SendResetPasswordEmail(module, user_type, Mail_Config):
    try:
        token = GenerateResetToken(module, user_type)
        reset_link = f"{RESET_URLS[user_type]}?token={token}"
        name = GetResetName(module)

        subject = "Reset your Pegatto password"
        text_body = (
            f"Hi {name},\n\n"
            f"Use the link below to reset your password. It is valid for 15 minutes.\n{reset_link}\n\n"
            f"If you did not request this, you can ignore this mail."
        )
        html_body = f"""
        <div style="font-family:Arial,sans-serif;background:#f4f6fb;padding:30px;">
          <div style="max-width:520px;margin:auto;background:#ffffff;border-radius:12px;padding:32px;">
            <h2 style="margin:0 0 12px;color:#0f172a;">Reset your password</h2>
            <p style="color:#475569;font-size:14px;">Hi {name},</p>
            <p style="color:#475569;font-size:14px;line-height:1.6;">
              We received a request to reset your Pegatto password.
              Click the button below to set a new password. This link is valid for <b>15 minutes</b>.
            </p>
            <p style="text-align:center;margin:28px 0;">
              <a href="{reset_link}"
                 style="background:#0a64ff;color:#ffffff;text-decoration:none;padding:12px 28px;
                        border-radius:8px;font-weight:bold;font-size:14px;display:inline-block;">
                Reset Password
              </a>
            </p>
            <p style="color:#94a3b8;font-size:12px;line-height:1.6;">
              Button not working? Copy this link into your browser:<br>
              <span style="word-break:break-all;">{reset_link}</span>
            </p>
            <p style="color:#94a3b8;font-size:12px;">If you did not request this, you can safely ignore this mail.</p>
          </div>
        </div>
        """

        # SMTP connection from the UserMailConfiguration row
        smtp_port = int(Mail_Config.SMTPPort)
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=Mail_Config.SMTPHost,
            port=smtp_port,
            username=Mail_Config.MailId,
            password=Mail_Config.MailPassword,
            use_ssl=(smtp_port == 465),
            use_tls=(smtp_port != 465),
            timeout=20,
        )

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=Mail_Config.MailId,
            to=[GetResetEmail(module, user_type)],
            connection=connection,
        )
        message.attach_alternative(html_body, "text/html")
        message.send()
        return True, "Reset mail sent"
    except Exception as e:
        logger.exception("Reset password mail failed")
        return False, str(e)


# Step 1: Forgot password -> send mail with Reset Password button
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordEmail(APIView):

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            user_type = (data.get('user_type') or '').strip().lower()
            identifier = (data.get('identifier') or '').strip()

            if user_type not in ('partner', 'team', 'user'):
                return HttpResponse(JSONRenderer().render({"Error": "user_type must be partner, team or user"}),
                                    content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
            if not identifier:
                return HttpResponse(JSONRenderer().render({"Error": "identifier is required"}),
                                    content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

            module = FindResetAccount(user_type, identifier)

            if module and GetResetEmail(module, user_type):
                Mail_Config = UserMailConfiguration.objects.filter(
                    MailId__iexact=RESET_SENDER_MAIL
                ).first()
                if Mail_Config:
                    SendResetPasswordEmail(module, user_type, Mail_Config)
                else:
                    logger.error("Reset mail sender %s not found in UserMailConfiguration", RESET_SENDER_MAIL)

            # same response always, so nobody can find out which accounts exist
            return HttpResponse(JSONRenderer().render(
                {"status": True, "message": "If the account exists, a reset link has been sent to the registered email"}),
                content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"Error": str(e)}),
                                content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# Step 2: Reset page opened from the mail button
@method_decorator(csrf_exempt, name='dispatch')
class ResetPassword(APIView):

    # check the token when the reset page opens
    def get(self, request, *args, **kwargs):
        try:
            token = request.query_params.get('token')
            if not token:
                raise ValueError("token is required")
            module, user_type = GetAccountFromResetToken(token)
            return HttpResponse(JSONRenderer().render(
                {"status": True, "user_type": user_type, "email": GetResetEmail(module, user_type)}),
                content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"status": False, "Error": str(e)}),
                                content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    # save the new password
    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            token = data.get('token')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')

            if not token or not new_password or not confirm_password:
                raise ValueError("token, new_password and confirm_password are required")
            if new_password != confirm_password:
                raise ValueError("Passwords do not match")

            module, user_type = GetAccountFromResetToken(token)

            if user_type == 'user':
                validate_password(password=new_password, user=module)
            else:
                validate_password(password=new_password)

            password_field = GetResetPasswordField(user_type)
            setattr(module, password_field, make_password(new_password))
            module.save(update_fields=[password_field])

            return HttpResponse(JSONRenderer().render({"status": True, "message": "Password reset successfully"}),
                                content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return HttpResponse(JSONRenderer().render({"status": False, "Error": str(e)}),
                                content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# #-------------------- Forget and Reset Password ---------------------------

# # shajitha
# # 24-11-26


# from django.core import signing
# from django.core.mail import EmailMultiAlternatives
# from django.contrib.auth.password_validation import validate_password
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt

# RESET_SALT = 'pegatto-reset-password'
# RESET_MAX_AGE = 15 * 60  # 15 minutes

# # reset page link for each type (change the user one to your main app url)
# RESET_URLS = {
#     'partner': 'https://partner.pegatto.com/auth/reset-password',
#     'team': 'https://partner.pegatto.com/auth/team-reset-password',
#     # 'user': 'https://app.pegatto.com/auth/reset-password',
#     'user': 'http://localhost:3005/auth/reset-password',
# }
# # RESET_URLS = {
# #     'partner': 'https://partner.pegatto.com/auth/reset-password',
# #     'team': 'https://partner.pegatto.com/auth/team-reset-password',
# #     'user': 'https://partner.pegatto.com/auth/management-reset-password',
# # }

# def GetResetPasswordField(user_type):
#     # Django User uses 'password', Partner and PartnerTeamMember use 'Password'
#     return 'password' if user_type == 'user' else 'Password'


# def GetResetEmail(module, user_type):
#     if user_type == 'partner':
#         return module.Primary_Email
#     if user_type == 'team':
#         return module.Email
#     return module.email


# def GetResetName(module):
#     return (getattr(module, 'Primary_Contact_Name', None)
#             or getattr(module, 'Name', None)
#             or getattr(module, 'first_name', None)
#             or getattr(module, 'username', None)
#             or 'User')


# def FindResetAccount(user_type, identifier):
#     if user_type == 'partner':
#         return Partner.objects.filter(
#             Q(Primary_Email__iexact=identifier) | Q(Partner_Id=identifier) | Q(Partner_Code=identifier),
#             Is_Deleted=False
#         ).first()
#     if user_type == 'team':
#         return PartnerTeamMember.objects.filter(
#             Q(Email__iexact=identifier) | Q(User_Id__iexact=identifier) | Q(PartnerTeamMember_id=identifier),
#             Is_Deleted=False
#         ).first()
#     if user_type == 'user':
#         return User.objects.filter(
#             Q(username__iexact=identifier) | Q(email__iexact=identifier),
#             is_active=True
#         ).first()
#     raise ValueError("user_type must be partner, team or user")


# def GenerateResetToken(module, user_type):
#     # last 12 chars of the current password hash are inside the token,
#     # so after the password changes the old link stops working (single use)
#     current_password = getattr(module, GetResetPasswordField(user_type)) or ''
#     return signing.dumps(
#         {'type': user_type, 'id': module.pk, 'h': current_password[-12:]},
#         salt=RESET_SALT
#     )


# def GetAccountFromResetToken(token):
#     # returns (module, user_type) or raises ValueError with a clear message
#     try:
#         payload = signing.loads(token, salt=RESET_SALT, max_age=RESET_MAX_AGE)
#     except signing.SignatureExpired:
#         raise ValueError("Reset link has expired. Please request a new one")
#     except signing.BadSignature:
#         raise ValueError("Invalid reset link")

#     user_type = payload['type']
#     if user_type == 'partner':
#         module = Partner.objects.filter(id=payload['id'], Is_Deleted=False).first()
#     elif user_type == 'team':
#         module = PartnerTeamMember.objects.filter(id=payload['id'], Is_Deleted=False).first()
#     else:
#         module = User.objects.filter(id=payload['id'], is_active=True).first()

#     if not module:
#         raise ValueError("Account not found")

#     current_password = getattr(module, GetResetPasswordField(user_type)) or ''
#     if current_password[-12:] != payload['h']:
#         raise ValueError("This reset link is already used. Please request a new one")
#     return module, user_type


# def SendResetPasswordEmail(module, user_type, sender_mailid):
#     try:
#         token = GenerateResetToken(module, user_type)
#         reset_link = f"{RESET_URLS[user_type]}?token={token}"
#         name = GetResetName(module)

#         subject = "Reset your Pegatto password"
#         text_body = (
#             f"Hi {name},\n\n"
#             f"Use the link below to reset your password. It is valid for 15 minutes.\n{reset_link}\n\n"
#             f"If you did not request this, you can ignore this mail."
#         )
#         html_body = f"""
#         <div style="font-family:Arial,sans-serif;background:#f4f6fb;padding:30px;">
#           <div style="max-width:520px;margin:auto;background:#ffffff;border-radius:12px;padding:32px;">
#             <h2 style="margin:0 0 12px;color:#0f172a;">Reset your password</h2>
#             <p style="color:#475569;font-size:14px;">Hi {name},</p>
#             <p style="color:#475569;font-size:14px;line-height:1.6;">
#               We received a request to reset your Pegatto password.
#               Click the button below to set a new password. This link is valid for <b>15 minutes</b>.
#             </p>
#             <p style="text-align:center;margin:28px 0;">
#               <a href="{reset_link}"
#                  style="background:#0a64ff;color:#ffffff;text-decoration:none;padding:12px 28px;
#                         border-radius:8px;font-weight:bold;font-size:14px;display:inline-block;">
#                 Reset Password
#               </a>
#             </p>
#             <p style="color:#94a3b8;font-size:12px;line-height:1.6;">
#               Button not working? Copy this link into your browser:<br>
#               <span style="word-break:break-all;">{reset_link}</span>
#             </p>
#             <p style="color:#94a3b8;font-size:12px;">If you did not request this, you can safely ignore this mail.</p>
#           </div>
#         </div>
#         """

#         # NOTE: if your SendPartnerCredentialsEmail builds a connection from
#         # UserMailConfiguration, create the same connection here and pass connection=connection
#         message = EmailMultiAlternatives(
#             subject=subject,
#             body=text_body,
#             from_email=sender_mailid,
#             to=[GetResetEmail(module, user_type)],
#         )
#         message.attach_alternative(html_body, "text/html")
#         message.send()
#         return True, "Reset mail sent"
#     except Exception as e:
#         return False, str(e)


# # Step 1: Forgot password -> send mail with Reset Password button
# @method_decorator(csrf_exempt, name='dispatch')
# class ForgotPasswordEmail(APIView):

#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             user_type = (data.get('user_type') or '').strip().lower()
#             identifier = (data.get('identifier') or '').strip()

#             if user_type not in ('partner', 'team', 'user'):
#                 return HttpResponse(JSONRenderer().render({"Error": "user_type must be partner, team or user"}),
#                                     content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#             if not identifier:
#                 return HttpResponse(JSONRenderer().render({"Error": "identifier is required"}),
#                                     content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#             module = FindResetAccount(user_type, identifier)

#             if module and GetResetEmail(module, user_type):
#                 Mail_Config = UserMailConfiguration.objects.first()
#                 if Mail_Config:
#                     SendResetPasswordEmail(module, user_type, Mail_Config.MailId)

#             # same response always, so nobody can find out which accounts exist
#             return HttpResponse(JSONRenderer().render(
#                 {"status": True, "message": "If the account exists, a reset link has been sent to the registered email"}),
#                 content_type='application/json', status=status.HTTP_200_OK)
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"Error": str(e)}),
#                                 content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# # Step 2: Reset page opened from the mail button
# @method_decorator(csrf_exempt, name='dispatch')
# class ResetPassword(APIView):

#     # check the token when the reset page opens
#     def get(self, request, *args, **kwargs):
#         try:
#             token = request.query_params.get('token')
#             if not token:
#                 raise ValueError("token is required")
#             module, user_type = GetAccountFromResetToken(token)
#             return HttpResponse(JSONRenderer().render(
#                 {"status": True, "user_type": user_type, "email": GetResetEmail(module, user_type)}),
#                 content_type='application/json', status=status.HTTP_200_OK)
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"status": False, "Error": str(e)}),
#                                 content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     # save the new password
#     def patch(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             token = data.get('token')
#             new_password = data.get('new_password')
#             confirm_password = data.get('confirm_password')

#             if not token or not new_password or not confirm_password:
#                 raise ValueError("token, new_password and confirm_password are required")
#             if new_password != confirm_password:
#                 raise ValueError("Passwords do not match")

#             module, user_type = GetAccountFromResetToken(token)

#             if user_type == 'user':
#                 validate_password(password=new_password, user=module)
#             else:
#                 validate_password(password=new_password)

#             password_field = GetResetPasswordField(user_type)
#             setattr(module, password_field, make_password(new_password))
#             module.save(update_fields=[password_field])

#             return HttpResponse(JSONRenderer().render({"status": True, "message": "Password reset successfully"}),
#                                 content_type='application/json', status=status.HTTP_200_OK)
#         except Exception as e:
#             return HttpResponse(JSONRenderer().render({"status": False, "Error": str(e)}),
#                                 content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



# import smtplib
# import ssl
# import logging

# from email.message import EmailMessage

# logger = logging.getLogger(__name__)


# def test_partner_smtp_connection(mail_config, send_test_email=False):

#     connection = None

#     try:
#         host = (mail_config.SMTPHost or "").strip()
#         port = int(mail_config.SMTPPort or 0)
#         username = (mail_config.MailId or "").strip()
#         password = (mail_config.MailPassword or "").replace(" ", "")

#         if not host:
#             return False, "SMTP host is missing."

#         if not username:
#             return False, "Email address is missing."

#         if not password:
#             return False, "Email App Password is missing."

#         if port not in [465, 587]:
#             return False, "Use SMTP port 465 or 587."

#         ssl_context = ssl.create_default_context()

#         # PORT 465: SSL connection
#         if port == 465:

#             connection = smtplib.SMTP_SSL(
#                 host=host,
#                 port=465,
#                 timeout=30,
#                 context=ssl_context
#             )

#         # PORT 587: STARTTLS connection
#         elif port == 587:

#             connection = smtplib.SMTP(
#                 host=host,
#                 port=587,
#                 timeout=30
#             )

#             connection.ehlo()
#             connection.starttls(context=ssl_context)
#             connection.ehlo()

#         # Gmail login
#         connection.login(username, password)

#         # Optional test email
#         if send_test_email:

#             message = EmailMessage()
#             message["Subject"] = "Partner SMTP Configuration Test"
#             message["From"] = username
#             message["To"] = username

#             message.set_content(
#                 "Your partner SMTP configuration is working successfully."
#             )

#             connection.send_message(message)

#         connection.quit()

#         return True, "SMTP connection successful."

#     except smtplib.SMTPAuthenticationError:
#         logger.exception("SMTP authentication failed")
#         return False, "Gmail authentication failed. Check your Google App Password."

#     except smtplib.SMTPConnectError:
#         logger.exception("SMTP connection error")
#         return False, "Could not connect to Gmail SMTP server."

#     except (TimeoutError, OSError):
#         logger.exception("SMTP network error")
#         return False, "SMTP connection failed. Check server internet access, firewall and SSL/TLS settings."

#     except Exception as error:
#         logger.exception("SMTP error")
#         return False, f"SMTP error: {str(error)}"

#     finally:
#         if connection:
#             try:
#                 connection.quit()
#             except Exception:
#                 try:
#                     connection.close()
#                 except Exception:
#                     pass


# import smtplib
# import ssl
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

# def verify_smtp_login(host, port, mail_id, password):
#     """Raises an error if the mail server does not accept the login."""
#     host = (host or '').strip()
#     port = int(str(port).strip())
#     password = (password or '').replace(' ', '').strip()

#     if port == 465:
#         server = smtplib.SMTP_SSL(host, port, timeout=20)
#     else:
#         server = smtplib.SMTP(host, port, timeout=20)
#         server.starttls()
#     try:
#         server.login((mail_id or '').strip(), password)
#     finally:
#         try:
#             server.quit()
#         except Exception:
#             pass


# class PartnerMailConfigurationCRUD(APIView):

#     # POST - save the partner's mail settings (login is checked before saving)
#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data.copy()

#             partner_id = data.get('Partner_Id')
#             if not partner_id:
#                 raise ValueError("Partner_Id is required")

#             if PartnerMailConfiguration.objects.filter(Partner_Id=partner_id, Is_Deleted=False).exists():
#                 raise ValueError("Mail configuration already exists for this partner. Use PUT or PATCH")

#             try:
#                 verify_smtp_login(data.get('SMTPHost'), data.get('SMTPPort'),
#                                   data.get('MailId'), data.get('MailPassword'))
#             except Exception as e:
#                 raise ValueError("Mail login failed: " + str(e))

#             data['MailPassword'] = (data.get('MailPassword') or '').replace(' ', '').strip()

#             serialize = PartnerMailConfigurationSerializer(data=data)
#             if serialize.is_valid():
#                 module = serialize.save()
#                 output = JSONRenderer().render(PartnerMailConfigurationSerializers(module).data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)

#             output = JSONRenderer().render(serialize.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     # GET - by id or by Partner_Id (password is never returned)
#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             if data.get('id'):
#                 module = PartnerMailConfiguration.objects.get(id=data['id'], Is_Deleted=False)
#             elif data.get('Partner_Id'):
#                 module = PartnerMailConfiguration.objects.get(Partner_Id=data['Partner_Id'], Is_Deleted=False)
#             else:
#                 raise ValueError("id or Partner_Id is required")

#             serialize = PartnerMailConfigurationSerializers(module)
#             output = JSONRenderer().render(serialize.data)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#         except PartnerMailConfiguration.DoesNotExist:
#             output = JSONRenderer().render({"Error": "Mail configuration not found"})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     # PUT - full update
#     def put(self, request, *args, **kwargs):
#         try:
#             data = request.data.copy()
#             module = PartnerMailConfiguration.objects.get(id=data['id'], Is_Deleted=False)

#             try:
#                 verify_smtp_login(data.get('SMTPHost'), data.get('SMTPPort'),
#                                   data.get('MailId'), data.get('MailPassword'))
#             except Exception as e:
#                 raise ValueError("Mail login failed: " + str(e))

#             data['MailPassword'] = (data.get('MailPassword') or '').replace(' ', '').strip()
#             data['Updated_Date'] = timezone.now()

#             serialize = PartnerMailConfigurationSerializer(instance=module, data=data)
#             if serialize.is_valid():
#                 module = serialize.save()
#                 output = JSONRenderer().render(PartnerMailConfigurationSerializers(module).data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)

#             output = JSONRenderer().render(serialize.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except PartnerMailConfiguration.DoesNotExist:
#             output = JSONRenderer().render({"Error": "Mail configuration not found"})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     # PATCH - partial update (login is re-checked when any mail setting changes)
#     def patch(self, request, *args, **kwargs):
#         try:
#             data = request.data.copy()
#             module = PartnerMailConfiguration.objects.get(id=data['id'], Is_Deleted=False)

#             if any(key in data for key in ('SMTPHost', 'SMTPPort', 'MailId', 'MailPassword')):
#                 try:
#                     verify_smtp_login(
#                         data.get('SMTPHost', module.SMTPHost),
#                         data.get('SMTPPort', module.SMTPPort),
#                         data.get('MailId', module.MailId),
#                         data.get('MailPassword', module.MailPassword),
#                     )
#                 except Exception as e:
#                     raise ValueError("Mail login failed: " + str(e))

#             if data.get('MailPassword'):
#                 data['MailPassword'] = data['MailPassword'].replace(' ', '').strip()
#             data['Updated_Date'] = timezone.now()

#             serialize = PartnerMailConfigurationSerializer(instance=module, data=data, partial=True)
#             if serialize.is_valid():
#                 module = serialize.save()
#                 output = JSONRenderer().render(PartnerMailConfigurationSerializers(module).data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)

#             output = JSONRenderer().render(serialize.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except PartnerMailConfiguration.DoesNotExist:
#             output = JSONRenderer().render({"Error": "Mail configuration not found"})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

#     # DELETE - soft delete
#     def delete(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             module = PartnerMailConfiguration.objects.get(id=data['id'], Is_Deleted=False)
#             module.Is_Deleted = True
#             module.save(update_fields=['Is_Deleted'])

#             output = JSONRenderer().render({"Message": "Mail configuration deleted successfully"})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#         except PartnerMailConfiguration.DoesNotExist:
#             output = JSONRenderer().render({"Error": "Mail configuration not found"})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             output = JSONRenderer().render({"Error": str(e)})
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

# import smtplib
# import ssl

# def send_partner_mail(mail_config, recipient_email, subject, message):

#     try:
#         smtp = smtplib.SMTP(
#             mail_config.SMTPHost,
#             int(mail_config.SMTPPort)
#         )

#         smtp.starttls(context=ssl.create_default_context())

#         smtp.login(
#             mail_config.MailId,
#             mail_config.MailPassword
#         )

#         smtp.sendmail(
#             mail_config.MailId,
#             recipient_email,
#             message
#         )

#         smtp.quit()

#         return True

#     except Exception as e:
#         return str(e)



import smtplib
import ssl
import logging

from email.message import EmailMessage

logger = logging.getLogger(__name__)


def get_smtp_connection(mail_config):

    host = (mail_config.SMTPHost or '').strip()
    port = int(mail_config.SMTPPort or 0)
    username = (mail_config.MailId or '').strip()
    password = (mail_config.MailPassword or '').replace(' ', '').strip()

    if not host:
        raise ValueError("SMTPHost is required.")

    if not username:
        raise ValueError("MailId is required.")

    if not password:
        raise ValueError("MailPassword is required.")

    if port not in [465, 587]:
        raise ValueError("SMTPPort must be 465 or 587.")

    ssl_context = ssl.create_default_context()

    # Gmail port 465 uses SSL
    if port == 465:

        connection = smtplib.SMTP_SSL(
            host=host,
            port=465,
            timeout=30,
            context=ssl_context
        )

    # Gmail port 587 uses STARTTLS
    else:

        connection = smtplib.SMTP(
            host=host,
            port=587,
            timeout=30
        )

        connection.ehlo()
        connection.starttls(context=ssl_context)
        connection.ehlo()

    connection.login(username, password)

    return connection


def verify_smtp_login(mail_config):

    connection = None

    try:
        connection = get_smtp_connection(mail_config)

        return True, "SMTP login successful."

    except smtplib.SMTPAuthenticationError:
        logger.exception("SMTP authentication failed")
        return False, "Gmail authentication failed. Check your Google App Password."

    except (smtplib.SMTPException, OSError, TimeoutError) as error:
        logger.exception("SMTP connection failed")
        return False, f"SMTP connection failed: {str(error)}"

    except Exception as error:
        logger.exception("SMTP verification failed")
        return False, str(error)

    finally:
        if connection:
            try:
                connection.quit()
            except Exception:
                try:
                    connection.close()
                except Exception:
                    pass


def send_partner_mail(mail_config, recipient_email, subject, message):

    connection = None

    try:

        if not recipient_email:
            return False, "Recipient email is missing."

        connection = get_smtp_connection(mail_config)

        sender_email = mail_config.MailId.strip()

        email_message = EmailMessage()
        email_message["Subject"] = subject
        email_message["From"] = sender_email
        email_message["To"] = recipient_email
        email_message["Reply-To"] = sender_email

        email_message.set_content(message)

        connection.send_message(email_message)

        return True, "Email sent successfully."

    except smtplib.SMTPAuthenticationError:
        logger.exception("SMTP authentication failed")
        return False, "Gmail authentication failed. Check the App Password."

    except (smtplib.SMTPException, OSError, TimeoutError) as error:
        logger.exception("Partner email sending failed")
        return False, f"Email sending failed: {str(error)}"

    except Exception as error:
        logger.exception("Partner email error")
        return False, str(error)

    finally:
        if connection:
            try:
                connection.quit()
            except Exception:
                try:
                    connection.close()
                except Exception:
                    pass


def send_smtp_test_email(mail_config):

    return send_partner_mail(
        mail_config=mail_config,
        recipient_email=mail_config.MailId,
        subject="Partner SMTP Configuration Test",
        message=(
            "Your Partner SMTP configuration is working successfully.\n\n"
            "This is a test email from your application."
        )
    )



import logging

from django.http import HttpResponse
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.renderers import JSONRenderer

from .models import PartnerMailConfiguration

logger = logging.getLogger(__name__)


def partner_mail_response(data, http_status):
    output = JSONRenderer().render(data)

    return HttpResponse(
        output,
        content_type='application/json',
        status=http_status
    )


class PartnerMailConfigurationCRUD(APIView):

    # --------------------------------------------------
    # POST - CREATE PARTNER MAIL CONFIGURATION
    # --------------------------------------------------

    def post(self, request, *args, **kwargs):

        try:

            data = request.data.copy()

            partner_id = data.get('Partner_Id')

            if not partner_id:
                return partner_mail_response(
                    {"Error": "Partner_Id is required."},
                    status.HTTP_400_BAD_REQUEST
                )

            existing = PartnerMailConfiguration.objects.filter(
                Partner_Id=partner_id,
                Is_Deleted=False
            ).exists()

            if existing:
                return partner_mail_response(
                    {
                        "Error": "Mail configuration already exists for this partner. Use PUT or PATCH."
                    },
                    status.HTTP_400_BAD_REQUEST
                )

            # Save configuration first.
            # SMTP login is tested through the separate test API.

            serializer = PartnerMailConfigurationSerializer(
                data=data
            )

            if serializer.is_valid():

                module = serializer.save()

                return partner_mail_response(
                    {
                        "Message": "Partner mail configuration saved successfully. Please test the SMTP connection.",
                        "id": module.id,
                        "Partner_Id": module.Partner_Id_id,
                        "MailId": module.MailId
                    },
                    status.HTTP_201_CREATED
                )

            return partner_mail_response(
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )

        except Exception as error:

            logger.exception("Partner mail configuration creation failed")

            return partner_mail_response(
                {"Error": str(error)},
                status.HTTP_400_BAD_REQUEST
            )

    # --------------------------------------------------
    # GET - GET CONFIGURATION BY ID OR PARTNER ID
    # --------------------------------------------------

    def get(self, request, *args, **kwargs):

        try:

            data = request.query_params

            if data.get('id'):

                module = PartnerMailConfiguration.objects.get(
                    id=data.get('id'),
                    Is_Deleted=False
                )

            elif data.get('Partner_Id'):

                module = PartnerMailConfiguration.objects.get(
                    Partner_Id=data.get('Partner_Id'),
                    Is_Deleted=False
                )

            else:

                return partner_mail_response(
                    {
                        "Error": "Please provide id or Partner_Id."
                    },
                    status.HTTP_400_BAD_REQUEST
                )

            serializer = PartnerMailConfigurationSerializer(module)

            return partner_mail_response(
                serializer.data,
                status.HTTP_200_OK
            )

        except PartnerMailConfiguration.DoesNotExist:

            return partner_mail_response(
                {"Error": "Mail configuration not found."},
                status.HTTP_404_NOT_FOUND
            )

        except Exception as error:

            logger.exception("Partner mail configuration GET failed")

            return partner_mail_response(
                {"Error": str(error)},
                status.HTTP_400_BAD_REQUEST
            )

    # --------------------------------------------------
    # PUT - COMPLETE UPDATE
    # --------------------------------------------------

    def put(self, request, *args, **kwargs):

        try:

            data = request.data.copy()

            configuration_id = data.get('id')

            if not configuration_id:
                return partner_mail_response(
                    {"Error": "id is required."},
                    status.HTTP_400_BAD_REQUEST
                )

            module = PartnerMailConfiguration.objects.get(
                id=configuration_id,
                Is_Deleted=False
            )

            data['Updated_Date'] = timezone.now()

            serializer = PartnerMailConfigurationSerializer(
                instance=module,
                data=data
            )

            if serializer.is_valid():

                module = serializer.save()

                return partner_mail_response(
                    {
                        "Message": "Partner mail configuration updated successfully.",
                        "id": module.id,
                        "Partner_Id": module.Partner_Id_id,
                        "MailId": module.MailId
                    },
                    status.HTTP_200_OK
                )

            return partner_mail_response(
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )

        except PartnerMailConfiguration.DoesNotExist:

            return partner_mail_response(
                {"Error": "Mail configuration not found."},
                status.HTTP_404_NOT_FOUND
            )

        except Exception as error:

            logger.exception("Partner mail configuration PUT failed")

            return partner_mail_response(
                {"Error": str(error)},
                status.HTTP_400_BAD_REQUEST
            )

    # --------------------------------------------------
    # PATCH - PARTIAL UPDATE
    # --------------------------------------------------

    def patch(self, request, *args, **kwargs):

        try:

            data = request.data.copy()

            configuration_id = data.get('id')

            if not configuration_id:
                return partner_mail_response(
                    {"Error": "id is required."},
                    status.HTTP_400_BAD_REQUEST
                )

            module = PartnerMailConfiguration.objects.get(
                id=configuration_id,
                Is_Deleted=False
            )

            data['Updated_Date'] = timezone.now()

            serializer = PartnerMailConfigurationSerializer(
                instance=module,
                data=data,
                partial=True
            )

            if serializer.is_valid():

                module = serializer.save()

                return partner_mail_response(
                    {
                        "Message": "Partner mail configuration updated successfully.",
                        "id": module.id,
                        "Partner_Id": module.Partner_Id_id,
                        "MailId": module.MailId
                    },
                    status.HTTP_200_OK
                )

            return partner_mail_response(
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )

        except PartnerMailConfiguration.DoesNotExist:

            return partner_mail_response(
                {"Error": "Mail configuration not found."},
                status.HTTP_404_NOT_FOUND
            )

        except Exception as error:

            logger.exception("Partner mail configuration PATCH failed")

            return partner_mail_response(
                {"Error": str(error)},
                status.HTTP_400_BAD_REQUEST
            )

    # --------------------------------------------------
    # DELETE - SOFT DELETE
    # --------------------------------------------------

    def delete(self, request, *args, **kwargs):

        try:

            configuration_id = request.query_params.get('id')

            if not configuration_id:
                return partner_mail_response(
                    {"Error": "id is required."},
                    status.HTTP_400_BAD_REQUEST
                )

            module = PartnerMailConfiguration.objects.get(
                id=configuration_id,
                Is_Deleted=False
            )

            module.Is_Deleted = True
            module.Updated_Date = timezone.now()

            module.save(
                update_fields=['Is_Deleted', 'Updated_Date']
            )

            return partner_mail_response(
                {
                    "Message": "Partner mail configuration deleted successfully."
                },
                status.HTTP_200_OK
            )

        except PartnerMailConfiguration.DoesNotExist:

            return partner_mail_response(
                {"Error": "Mail configuration not found."},
                status.HTTP_404_NOT_FOUND
            )

        except Exception as error:

            logger.exception("Partner mail configuration DELETE failed")

            return partner_mail_response(
                {"Error": str(error)},
                status.HTTP_400_BAD_REQUEST
            )


# ======================================================
# TEST SMTP CONNECTION API
# ======================================================

class PartnerMailConfigurationTestConnection(APIView):

    def post(self, request, *args, **kwargs):

        try:

            configuration_id = request.data.get('id')

            if not configuration_id:
                return partner_mail_response(
                    {"Error": "id is required."},
                    status.HTTP_400_BAD_REQUEST
                )

            module = PartnerMailConfiguration.objects.get(
                id=configuration_id,
                Is_Deleted=False
            )

            # First verify SMTP login
            success, message = verify_smtp_login(module)

            if not success:

                return partner_mail_response(
                    {
                        "SMTP_Status": "Failed",
                        "MailId": module.MailId,
                        "Error": message
                    },
                    status.HTTP_400_BAD_REQUEST
                )

            # Send test email only if requested
            send_test = request.data.get(
                'send_test_email',
                False
            )

            if send_test:

                email_success, email_message = send_smtp_test_email(
                    module
                )

                if not email_success:

                    return partner_mail_response(
                        {
                            "SMTP_Status": "Connected",
                            "Test_Email_Status": "Failed",
                            "Error": email_message
                        },
                        status.HTTP_400_BAD_REQUEST
                    )

                return partner_mail_response(
                    {
                        "SMTP_Status": "Connected",
                        "Test_Email_Status": "Sent",
                        "MailId": module.MailId,
                        "Message": "SMTP connection successful and test email sent."
                    },
                    status.HTTP_200_OK
                )

            return partner_mail_response(
                {
                    "SMTP_Status": "Connected",
                    "MailId": module.MailId,
                    "Message": "SMTP login successful."
                },
                status.HTTP_200_OK
            )

        except PartnerMailConfiguration.DoesNotExist:

            return partner_mail_response(
                {"Error": "Mail configuration not found."},
                status.HTTP_404_NOT_FOUND
            )

        except Exception as error:

            logger.exception("SMTP test API failed")

            return partner_mail_response(
                {"Error": str(error)},
                status.HTTP_400_BAD_REQUEST
            )






# ==================== PARTNER COMMISSION UTILS ====================
# create_partner_commission / calculate_invoice_commissions / mark_invoice_payment_received
# can be imported from this views.py into your Sales Order / Invoice flow.

DEFAULT_COMMISSION_PERCENTAGE = {
    'Implementation': Decimal('80.00'),
    'Product': Decimal('20.00'),
    'Extension': Decimal('20.00'),
}

COMMISSION_TYPE_LIST = ['Implementation', 'Product', 'Extension']
ACTIVE_INVOICE_STATUS = ['Submitted', 'Under Review', 'Approved']   # blocks a new invoice
INVOICE_ALLOWED_STATUS = ['Eligible', 'Rejected']                   # partner can raise invoice


def round_amount(value):
    return Decimal(value or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def get_active_commission_rule(commission_type):
    today = timezone.now().date()
    return PartnerCommissionRule.objects.filter(
        Commission_Type=commission_type,
        Is_Active=True,
        Is_Deleted=False,
        Effective_From__lte=today,
    ).filter(
        Q(Effective_To__isnull=True) | Q(Effective_To__gte=today)
    ).order_by('-Effective_From', '-id').first()


def calculate_commission(commission_type, sales_order_value):
    rule = get_active_commission_rule(commission_type)
    if rule and rule.Commission_Percentage is not None:
        percentage = Decimal(rule.Commission_Percentage)
    else:
        percentage = DEFAULT_COMMISSION_PERCENTAGE.get(commission_type, Decimal('0.00'))
    amount = round_amount(Decimal(sales_order_value or 0) * percentage / Decimal('100'))
    return rule, percentage, amount


def check_invoice_eligibility(commission):
    # Implementation      -> implementation completed + customer sign-off
    # Product / Extension -> customer payment received by Foyer
    if commission.Commission_Type == 'Implementation':
        if not commission.Implementation_Completed:
            return False, 'Waiting for implementation completion'
        if not commission.Customer_Signoff_Received:
            return False, 'Waiting for customer sign-off'
        return True, 'Eligible to raise invoice'

    if commission.Commission_Type in ['Product', 'Extension']:
        if not commission.Customer_Payment_Received:
            return False, 'Waiting for customer payment'
        return True, 'Eligible to raise invoice'

    return False, 'Invalid commission type'


def refresh_commission_eligibility(commission):
    # Only moves Pending <-> Eligible. Once invoice is submitted, status is not touched here.
    if commission.Commission_Status not in ['Pending', 'Eligible']:
        return commission

    is_eligible, _ = check_invoice_eligibility(commission)
    if is_eligible:
        commission.Eligibility_Status = 'Eligible'
        commission.Commission_Status = 'Eligible'
        if not commission.Eligible_Date:
            commission.Eligible_Date = timezone.now()
    else:
        commission.Eligibility_Status = 'Not Eligible'
        commission.Commission_Status = 'Pending'
        commission.Eligible_Date = None

    commission.Updated_Date = timezone.now()
    commission.save()
    return commission


def create_partner_commission(Partner_Id, Commission_Type, Sales_Order_Value, Customer_Id=None,
                              Invoice_Id=None, InstanceRequest_Id=None, Product_Id=None):
    # Pass model objects, e.g. Partner_Id=partner_obj, Customer_Id=account_obj
    rule, percentage, amount = calculate_commission(Commission_Type, Sales_Order_Value)
    commission = PartnerCommission.objects.create(
        Partner_Id=Partner_Id,
        Customer_Id=Customer_Id,
        Invoice_Id=Invoice_Id,
        InstanceRequest_Id=InstanceRequest_Id,
        Product_Id=Product_Id,
        Rule_Id=rule,
        Commission_Type=Commission_Type,
        Sales_Order_Value=round_amount(Sales_Order_Value),
        Commission_Percentage=percentage,
        Commission_Amount=amount,
        Eligibility_Status='Not Eligible',
        Commission_Status='Pending',
    )
    return refresh_commission_eligibility(commission)


def calculate_invoice_commissions(invoice, partner, customer, items, instance_request=None, save=True):
    """
    Called when Super Admin creates the customer's Invoice (customer requested product / implementation).
    items = [{"Commission_Type": "Implementation", "Amount": 100000},
             {"Commission_Type": "Product", "Product_Id": 3, "Amount": 50000}]
    Amount = implementation value / product value from the sales order (NOT the full invoice total).
    save=False -> only calculate (preview), nothing stored.
    Same Invoice + Commission_Type + Product again -> updates the existing row (no duplicates),
    unless an invoice is already raised on it.
    """
    results = []
    for item in items:
        commission_type = item.get('Commission_Type')
        amount_value = round_amount(item.get('Amount'))
        product = ProductMaster.objects.filter(id=item.get('Product_Id')).first() if item.get('Product_Id') else None
        rule, percentage, amount = calculate_commission(commission_type, amount_value)

        row = {
            'Commission_Type': commission_type,
            'Product_Id': product.id if product else None,
            'Sales_Order_Value': str(amount_value),
            'Commission_Percentage': str(percentage),
            'Commission_Amount': str(amount),
            'Rule_Id': rule.id if rule else None,
            'Action': 'Calculated',
        }

        if save:
            existing = PartnerCommission.objects.filter(
                Invoice_Id=invoice, Commission_Type=commission_type, Product_Id=product, Is_Deleted=False).first()

            if existing and existing.Commission_Status not in ['Pending', 'Eligible']:
                row['Action'] = 'Skipped'
                row['Message'] = f'Commission already {existing.Commission_Status}, not recalculated'
                commission = existing
            elif existing:
                existing.Partner_Id = partner
                existing.Customer_Id = customer
                existing.InstanceRequest_Id = instance_request
                existing.Rule_Id = rule
                existing.Sales_Order_Value = amount_value
                existing.Commission_Percentage = percentage
                existing.Commission_Amount = amount
                existing.save()
                commission = refresh_commission_eligibility(existing)
                row['Action'] = 'Updated'
            else:
                commission = create_partner_commission(
                    Partner_Id=partner, Commission_Type=commission_type, Sales_Order_Value=amount_value,
                    Customer_Id=customer, Invoice_Id=invoice, InstanceRequest_Id=instance_request, Product_Id=product)
                row['Action'] = 'Created'

            row['id'] = commission.id
            row['PartnerCommission_id'] = commission.PartnerCommission_id
            row['Commission_Status'] = commission.Commission_Status

        results.append(row)
    return results

def validate_commission_payload(partner_id, customer_id, items, instance_request_id=None):
    """
    Checks Partner / Customer / Items before anything is saved.
    Returns (partner, customer, instance_request, items). Raises ValueError with a clear message.
    Used by PartnerCommissionCalculate and by InvoiceCRUD.post.
    """
    partner = Partner.objects.filter(id=partner_id).first() if partner_id else None
    if not partner:
        raise ValueError("Commission: Partner not found")
    customer = Account.objects.filter(id=customer_id).first() if customer_id else None
    if not customer:
        raise ValueError("Commission: Customer not found")
    instance_request = InstanceRequest.objects.filter(id=instance_request_id).first() if instance_request_id else None

    if isinstance(items, str):
        items = json.loads(items)          # form-data sends the list as a JSON string
    if not isinstance(items, list) or not items:
        raise ValueError("Commission: Items is required")

    for index, item in enumerate(items, start=1):
        if item.get('Commission_Type') not in COMMISSION_TYPE_LIST:
            raise ValueError(f"Commission item {index}: Commission_Type must be one of {COMMISSION_TYPE_LIST}")
        validate_amount(item.get('Amount'), f"Commission item {index}: Amount")
        if item['Commission_Type'] in ['Product', 'Extension']:
            if not item.get('Product_Id'):
                raise ValueError(f"Commission item {index}: Product_Id is required for Product / Extension")
            if not ProductMaster.objects.filter(id=item['Product_Id']).exists():
                raise ValueError(f"Commission item {index}: Product not found")

    return partner, customer, instance_request, items

def mark_invoice_payment_received(invoice):
    # Call from your customer Invoice payment flow when Foyer receives the payment.
    # Product / Extension commissions of that invoice become Eligible.
    commissions = PartnerCommission.objects.filter(
        Invoice_Id=invoice, Commission_Type__in=['Product', 'Extension'],
        Commission_Status='Pending', Is_Deleted=False)
    for commission in commissions:
        commission.Customer_Payment_Received = True
        commission.save()
        refresh_commission_eligibility(commission)
    return commissions.count()


def get_commission_invoice_info(commission):
    # Extra fields shown on the Partner Portal for each commission row
    status_message = {
        'Invoice Submitted': 'Invoice submitted, awaiting approval',
        'Approved': 'Invoice approved, awaiting payment',
        'Paid': 'Commission paid',
        'Rejected': 'Invoice rejected, you can submit a new invoice',
    }
    is_eligible, message = check_invoice_eligibility(commission)
    active_invoice = commission.commission_invoices.filter(
        Is_Deleted=False, Approval_Status__in=ACTIVE_INVOICE_STATUS).exists()

    return {
        'Can_Raise_Invoice': commission.Commission_Status in INVOICE_ALLOWED_STATUS and is_eligible and not active_invoice,
        'Invoice_Eligibility_Message': status_message.get(commission.Commission_Status, message),
    }


def get_commission_summary(queryset):
    # Dashboard cards
    summary = {
        'Total_Commission': Decimal('0.00'),
        'Pending_Commission': Decimal('0.00'),
        'Eligible_Commission': Decimal('0.00'),
        'Invoice_Submitted': Decimal('0.00'),
        'Approved_Commission': Decimal('0.00'),
        'Rejected_Commission': Decimal('0.00'),
        'Paid_Commission': Decimal('0.00'),
        'Total_Count': 0,
    }
    status_key = {
        'Pending': 'Pending_Commission',
        'Eligible': 'Eligible_Commission',
        'Invoice Submitted': 'Invoice_Submitted',
        'Approved': 'Approved_Commission',
        'Rejected': 'Rejected_Commission',
        'Paid': 'Paid_Commission',
    }
    for row in queryset.values('Commission_Status', 'Commission_Amount'):
        amount = Decimal(row['Commission_Amount'] or 0)
        summary['Total_Commission'] += amount
        summary['Total_Count'] += 1
        key = status_key.get(row['Commission_Status'])
        if key:
            summary[key] += amount

    return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in summary.items()}


def get_data(request):
    # plain dict (safe with file uploads, request.data.copy() breaks on files)
    return request.data.dict() if hasattr(request.data, 'dict') else dict(request.data)


def error_response(message, code=status.HTTP_400_BAD_REQUEST):
    output = JSONRenderer().render({"Error": message})
    return HttpResponse(output, content_type='application/json', status=code)


def commission_with_info(module):
    # depth=1 data + Can_Raise_Invoice / Invoice_Eligibility_Message / Latest_Invoice
    data = dict(PartnerCommissionSerializers(module).data)
    data.update(get_commission_invoice_info(module))
    latest_invoice = module.commission_invoices.filter(Is_Deleted=False).order_by('-id').first()
    data['Latest_Invoice'] = PartnerCommissionInvoiceSerializer(latest_invoice).data if latest_invoice else None
    return data


def validate_percentage(value):
    try:
        percentage = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError("Commission_Percentage is required")
    if percentage < 0 or percentage > 100:
        raise ValueError("Commission_Percentage must be between 0 and 100")
    return percentage


def validate_amount(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError(f"{field} is required")
    if amount <= 0:
        raise ValueError(f"{field} must be greater than 0")
    return amount


# Fields the client is never allowed to set directly on PartnerCommission
COMMISSION_PROTECTED_FIELDS = ['Rule_Id', 'Commission_Percentage', 'Commission_Amount', 'Eligibility_Status',
                               'Commission_Status', 'Eligible_Date', 'PartnerCommission_id', 'Is_Deleted']

# Fields the partner is never allowed to set directly on PartnerCommissionInvoice
INVOICE_PROTECTED_FIELDS = ['Approval_Status', 'Approved_By', 'Approved_Date', 'Rejection_Reason', 'Payment_Status',
                            'Payment_Date', 'Payment_Reference_No', 'PartnerCommissionInvoice_id', 'Is_Deleted']


# ==================== Partner Commission Rule ====================

class PartnerCommissionRuleCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = get_data(request)
            if data.get('Commission_Type') not in COMMISSION_TYPE_LIST:
                return error_response(f"Commission_Type must be one of {COMMISSION_TYPE_LIST}")
            validate_percentage(data.get('Commission_Percentage'))
            if data.get('Effective_From') and data.get('Effective_To') and str(data['Effective_To']) < str(data['Effective_From']):
                return error_response("Effective_To cannot be before Effective_From")

            data['Created_By'] = request.user.id if request.user.is_authenticated else None
            data['Updated_By'] = data['Created_By']
            serializer = PartnerCommissionRuleSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response(str(e))

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerCommissionRule.objects.get(id=id)
            serializer = PartnerCommissionRuleSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))

    def put(self, request, *args, **kwargs):
        try:
            data = get_data(request)
            id = data['id']
            module = PartnerCommissionRule.objects.get(id=id)
            if data.get('Commission_Type') and data['Commission_Type'] not in COMMISSION_TYPE_LIST:
                return error_response(f"Commission_Type must be one of {COMMISSION_TYPE_LIST}")
            if data.get('Commission_Percentage') not in [None, '']:
                validate_percentage(data['Commission_Percentage'])

            data['Updated_By'] = request.user.id if request.user.is_authenticated else None
            data['Updated_Date'] = timezone.now()
            serializer = PartnerCommissionRuleSerializer(instance=module, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response(str(e))

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerCommissionRule.objects.get(id=id)
            serializer = PartnerCommissionRuleSerializer(module, {"Is_Deleted": True, "Is_Active": False, "Updated_Date": timezone.now()}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))

    def patch(self, request, *args, **kwargs):
        try:
            data = get_data(request)
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerCommissionRule.objects.get(id=id)
            if data.get('Commission_Type') and data['Commission_Type'] not in COMMISSION_TYPE_LIST:
                raise ValueError(f"Commission_Type must be one of {COMMISSION_TYPE_LIST}")
            if data.get('Commission_Percentage') not in [None, '']:
                validate_percentage(data['Commission_Percentage'])
            data['Updated_By'] = request.user.id if request.user.is_authenticated else None
            data['Updated_Date'] = timezone.now()
            serializer = PartnerCommissionRuleSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerCommissionRule.DoesNotExist:
            return Response({"Error": "PartnerCommissionRule not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PartnerCommissionRuleSearch(ListAPIView):
    queryset = PartnerCommissionRule.objects.all()
    serializer_class = PartnerCommissionRuleSerializers

    def get_queryset(self):
        try:
            data = self.request.GET.get('search', '')
            module = PartnerCommissionRule.objects.filter(
                (
                    Q(PartnerCommissionRule_id__icontains=data) |
                    Q(Commission_Type__icontains=data)
                ) &
                Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching partner commission rules: {str(e)}")


class PartnerCommissionRuleFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            data1 = {"Is_Deleted": False}
            if data.get("Commission_Type"):
                data1["Commission_Type"] = data["Commission_Type"]
            if data.get("Is_Active") is not None:
                data1["Is_Active"] = data["Is_Active"]
            if data.get("Effective_From"):
                data1["Effective_From__range"] = data["Effective_From"]
            if data.get("Created_By"):
                data1["Created_By_id"] = data["Created_By"]
            if data.get("Created_Date"):
                data1["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(model=PartnerCommissionRule, serializer=PartnerCommissionRuleSerializers, data=data1, page=page, Operator='and')
        except Exception as e:
            raise Exception(f"Error while fetching partner commission rules: {str(e)}")


class PartnerCommissionRuleList(ListAPIView):
    queryset = PartnerCommissionRule.objects.all()
    serializer_class = PartnerCommissionRuleSerializers

    def get_queryset(self):
        try:
            module = PartnerCommissionRule.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class PartnerCommissionRulewithoutpagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerCommissionRule.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = PartnerCommissionRuleSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))


# ==================== Partner Commission ====================

class PartnerCommissionCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = get_data(request)
            for key in COMMISSION_PROTECTED_FIELDS:
                data.pop(key, None)

            if not data.get('Partner_Id'):
                return error_response("Partner_Id is required")
            if data.get('Commission_Type') not in COMMISSION_TYPE_LIST:
                return error_response(f"Commission_Type must be one of {COMMISSION_TYPE_LIST}")
            if data['Commission_Type'] in ['Product', 'Extension'] and not data.get('Product_Id'):
                return error_response("Product_Id is required for Product / Extension commission")
            sales_order_value = validate_amount(data.get('Sales_Order_Value'), 'Sales_Order_Value')

            # Percentage + amount always come from the rule (80% / 20% / 20%)
            rule, percentage, amount = calculate_commission(data['Commission_Type'], sales_order_value)
            data['Rule_Id'] = rule.id if rule else None
            data['Commission_Percentage'] = percentage
            data['Commission_Amount'] = amount
            data['Eligibility_Status'] = 'Not Eligible'
            data['Commission_Status'] = 'Pending'

            serializer = PartnerCommissionSerializer(data=data)
            if serializer.is_valid():
                module = serializer.save()
                refresh_commission_eligibility(module)
                output = JSONRenderer().render(PartnerCommissionSerializer(module).data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response(str(e))

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerCommission.objects.get(id=id)
            output = JSONRenderer().render(commission_with_info(module))
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        try:
            data = get_data(request)
            id = data['id']
            module = PartnerCommission.objects.select_for_update().get(id=id)
            if module.Commission_Status in ['Invoice Submitted', 'Approved', 'Paid']:
                return error_response(f"Commission cannot be changed once {module.Commission_Status}")

            for key in COMMISSION_PROTECTED_FIELDS:
                data.pop(key, None)

            # Sales order value / type changed -> recalculate from rule
            if 'Sales_Order_Value' in data or 'Commission_Type' in data:
                commission_type = data.get('Commission_Type', module.Commission_Type)
                if commission_type not in COMMISSION_TYPE_LIST:
                    return error_response(f"Commission_Type must be one of {COMMISSION_TYPE_LIST}")
                sales_order_value = validate_amount(data.get('Sales_Order_Value', module.Sales_Order_Value), 'Sales_Order_Value')
                rule, percentage, amount = calculate_commission(commission_type, sales_order_value)
                data['Rule_Id'] = rule.id if rule else None
                data['Commission_Percentage'] = percentage
                data['Commission_Amount'] = amount

            data['Updated_Date'] = timezone.now()
            serializer = PartnerCommissionSerializer(instance=module, data=data, partial=True)
            if serializer.is_valid():
                module = serializer.save()
                refresh_commission_eligibility(module)
                output = JSONRenderer().render(PartnerCommissionSerializer(module).data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response(str(e))

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerCommission.objects.get(id=id)
            if module.Commission_Status in ['Invoice Submitted', 'Approved', 'Paid']:
                return error_response(f"Commission cannot be deleted once {module.Commission_Status}")
            serializer = PartnerCommissionSerializer(module, {"Is_Deleted": True, "Updated_Date": timezone.now()}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        try:
            data = get_data(request)
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerCommission.objects.select_for_update().get(id=id)
            if module.Commission_Status in ['Invoice Submitted', 'Approved', 'Paid']:
                raise ValueError(f"Commission cannot be changed once {module.Commission_Status}")

            for key in COMMISSION_PROTECTED_FIELDS:
                data.pop(key, None)
            if 'Sales_Order_Value' in data or 'Commission_Type' in data:
                commission_type = data.get('Commission_Type', module.Commission_Type)
                if commission_type not in COMMISSION_TYPE_LIST:
                    raise ValueError(f"Commission_Type must be one of {COMMISSION_TYPE_LIST}")
                sales_order_value = validate_amount(data.get('Sales_Order_Value', module.Sales_Order_Value), 'Sales_Order_Value')
                rule, percentage, amount = calculate_commission(commission_type, sales_order_value)
                data['Rule_Id'] = rule.id if rule else None
                data['Commission_Percentage'] = percentage
                data['Commission_Amount'] = amount

            data['Updated_Date'] = timezone.now()
            serializer = PartnerCommissionSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            module = serializer.save()
            refresh_commission_eligibility(module)
            return Response(PartnerCommissionSerializer(module).data, status=status.HTTP_200_OK)
        except PartnerCommission.DoesNotExist:
            return Response({"Error": "PartnerCommission not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PartnerCommissionSearch(ListAPIView):
    queryset = PartnerCommission.objects.all()
    serializer_class = PartnerCommissionSerializers

    def get_queryset(self):
        try:
            data = self.request.GET.get('search', '')
            module = PartnerCommission.objects.filter(
                (
                    Q(PartnerCommission_id__icontains=data) |
                    Q(Commission_Type__icontains=data) |
                    Q(Commission_Status__icontains=data) |
                    Q(Eligibility_Status__icontains=data)
                ) &
                Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching partner commissions: {str(e)}")


class PartnerCommissionFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            data1 = {"Is_Deleted": False}
            if data.get("Partner_Id"):
                data1["Partner_Id_id"] = data["Partner_Id"]
            if data.get("Customer_Id"):
                data1["Customer_Id_id"] = data["Customer_Id"]
            if data.get("Product_Id"):
                data1["Product_Id_id"] = data["Product_Id"]
            if data.get("Commission_Type"):
                data1["Commission_Type"] = data["Commission_Type"]
            if data.get("Commission_Status"):
                data1["Commission_Status"] = data["Commission_Status"]
            if data.get("Eligibility_Status"):
                data1["Eligibility_Status"] = data["Eligibility_Status"]
            if data.get("Created_Date"):
                data1["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(model=PartnerCommission, serializer=PartnerCommissionSerializers, data=data1, page=page, Operator='and')
        except Exception as e:
            raise Exception(f"Error while fetching partner commissions: {str(e)}")


class PartnerCommissionList(ListAPIView):
    queryset = PartnerCommission.objects.all()
    serializer_class = PartnerCommissionSerializers

    def get_queryset(self):
        try:
            module = PartnerCommission.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class PartnerCommissionwithoutpagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerCommission.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = PartnerCommissionSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))


# ==================== Partner Commission Dashboard (Partner Portal) ====================

class PartnerCommissionDashboard(APIView):
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            module = PartnerCommission.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            if data.get('Partner_Id'):
                module = module.filter(Partner_Id_id=data['Partner_Id'])

            summary = get_commission_summary(module)   # cards always show full totals
            if data.get('Commission_Type'):
                module = module.filter(Commission_Type=data['Commission_Type'])
            if data.get('Commission_Status'):
                module = module.filter(Commission_Status=data['Commission_Status'])

            output = JSONRenderer().render({
                "Summary": summary,
                "Commissions": [commission_with_info(obj) for obj in module],
            })
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))


# ==================== Partner Commission Invoice ====================

# class PartnerCommissionInvoiceCRUD(APIView):
#     parser_classes = [MultiPartParser, FormParser, JSONParser]

#     @transaction.atomic
#     def post(self, request, *args, **kwargs):
#         try:
#             data = get_data(request)
#             for key in INVOICE_PROTECTED_FIELDS:
#                 data.pop(key, None)

#             commission = PartnerCommission.objects.select_for_update().get(id=data.get('PartnerCommission_Id'), Is_Deleted=False)
#             if str(commission.Partner_Id_id) != str(data.get('Partner_Id')):
#                 return error_response("This commission does not belong to this partner", status.HTTP_403_FORBIDDEN)
#             if commission.Commission_Status not in INVOICE_ALLOWED_STATUS:
#                 return error_response(f"Invoice cannot be raised. Commission status is {commission.Commission_Status}")
#             is_eligible, message = check_invoice_eligibility(commission)
#             if not is_eligible:
#                 return error_response(message)
#             if commission.commission_invoices.filter(Is_Deleted=False, Approval_Status__in=ACTIVE_INVOICE_STATUS).exists():
#                 return error_response("An invoice is already submitted for this commission")

#             # partner_invoice_no = (data.get('Partner_Invoice_No') or '').strip()
#             # if not partner_invoice_no:
#             #     return error_response("Partner_Invoice_No is required")
#             if not data.get('Partner_Invoice_Date'):
#                 return error_response("Partner_Invoice_Date is required")
#             # invoice_file = request.FILES.get('Invoice_File')
#             # if not invoice_file:
#             #     return error_response("Invoice_File is required")
#             invoice_amount = validate_amount(data.get('Invoice_Amount'), 'Invoice_Amount')
#             if invoice_amount > Decimal(commission.Commission_Amount or 0):
#                 return error_response(f"Invoice_Amount cannot exceed commission amount {commission.Commission_Amount}")
#             if PartnerCommissionInvoice.objects.filter(
#                     Q(Partner_Id_id=commission.Partner_Id_id) & Q(Is_Deleted=False)
#             ).exclude(Approval_Status='Rejected').exists():
#                 return error_response("This invoice number is already used")

#             data['Partner_Id'] = commission.Partner_Id_id
#             data['Created_By'] = commission.Partner_Id_id
#             # data['Partner_Invoice_No'] = partner_invoice_no
#             # data['Invoice_File'] = invoice_file
#             # data['Invoice_File_Name'] = invoice_file.name[:100]
#             data['Approval_Status'] = 'Submitted'
#             data['Payment_Status'] = 'Pending'

#             serializer = PartnerCommissionInvoiceSerializer(data=data)
#             if serializer.is_valid():
#                 serializer.save()
#                 commission.Commission_Status = 'Invoice Submitted'
#                 commission.Updated_Date = timezone.now()
#                 commission.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except PartnerCommission.DoesNotExist:
#             return error_response("PartnerCommission not found", status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return error_response(str(e))

#     def get(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             id = data['id']
#             module = PartnerCommissionInvoice.objects.get(id=id)
#             serializer = PartnerCommissionInvoiceSerializers(module)
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#         except Exception as e:
#             return error_response(str(e))

#     def put(self, request, *args, **kwargs):
#         try:
#             data = get_data(request)
#             id = data['id']
#             module = PartnerCommissionInvoice.objects.get(id=id)
#             if module.Approval_Status != 'Submitted':
#                 return error_response(f"Invoice cannot be changed once {module.Approval_Status}")

#             for key in INVOICE_PROTECTED_FIELDS + ['Partner_Id', 'PartnerCommission_Id', 'Created_By']:
#                 data.pop(key, None)
#             if 'Invoice_Amount' in data:
#                 invoice_amount = validate_amount(data['Invoice_Amount'], 'Invoice_Amount')
#                 if invoice_amount > Decimal(module.PartnerCommission_Id.Commission_Amount or 0):
#                     return error_response(f"Invoice_Amount cannot exceed commission amount {module.PartnerCommission_Id.Commission_Amount}")
#             if request.FILES.get('Invoice_File'):
#                 data['Invoice_File'] = request.FILES['Invoice_File']
#                 data['Invoice_File_Name'] = request.FILES['Invoice_File'].name[:100]

#             data['Updated_Date'] = timezone.now()
#             serializer = PartnerCommissionInvoiceSerializer(instance=module, data=data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 output = JSONRenderer().render(serializer.data)
#                 return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#             output = JSONRenderer().render(serializer.errors)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return error_response(str(e))

#     @transaction.atomic
#     def delete(self, request, *args, **kwargs):
#         try:
#             data = request.query_params
#             id = data['id']
#             module = PartnerCommissionInvoice.objects.get(id=id)
#             if module.Approval_Status != 'Submitted':
#                 return error_response(f"Invoice cannot be deleted once {module.Approval_Status}")
#             serializer = PartnerCommissionInvoiceSerializer(module, {"Is_Deleted": True, "Updated_Date": timezone.now()}, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 # invoice withdrawn -> commission goes back to Eligible
#                 commission = module.PartnerCommission_Id
#                 commission.Commission_Status = 'Eligible'
#                 commission.Updated_Date = timezone.now()
#                 commission.save()
#             output = JSONRenderer().render(serializer.data)
#             return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
#         except Exception as e:
#             return error_response(str(e))

#     def patch(self, request, *args, **kwargs):
#         try:
#             data = get_data(request)
#             if not data:
#                 raise TypeError("Request data cannot be empty")
#             id = data.get('id')
#             module = PartnerCommissionInvoice.objects.get(id=id)
#             if module.Approval_Status != 'Submitted':
#                 raise ValueError(f"Invoice cannot be changed once {module.Approval_Status}")

#             for key in INVOICE_PROTECTED_FIELDS + ['Partner_Id', 'PartnerCommission_Id', 'Created_By']:
#                 data.pop(key, None)
#             if 'Invoice_Amount' in data:
#                 invoice_amount = validate_amount(data['Invoice_Amount'], 'Invoice_Amount')
#                 if invoice_amount > Decimal(module.PartnerCommission_Id.Commission_Amount or 0):
#                     raise ValueError(f"Invoice_Amount cannot exceed commission amount {module.PartnerCommission_Id.Commission_Amount}")
#             if request.FILES.get('Invoice_File'):
#                 data['Invoice_File'] = request.FILES['Invoice_File']
#                 data['Invoice_File_Name'] = request.FILES['Invoice_File'].name[:100]

#             data['Updated_Date'] = timezone.now()
#             serializer = PartnerCommissionInvoiceSerializer(instance=module, data=data, partial=True)
#             serializer.is_valid(raise_exception=True)
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except PartnerCommissionInvoice.DoesNotExist:
#             return Response({"Error": "PartnerCommissionInvoice not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== Partner Commission Invoice ====================

class PartnerCommissionInvoiceCRUD(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            data = get_data(request)
            for key in INVOICE_PROTECTED_FIELDS:
                data.pop(key, None)

            commission = PartnerCommission.objects.select_for_update().get(id=data.get('PartnerCommission_Id'), Is_Deleted=False)
            if str(commission.Partner_Id_id) != str(data.get('Partner_Id')):
                return error_response("This commission does not belong to this partner", status.HTTP_403_FORBIDDEN)
            if commission.Commission_Status not in INVOICE_ALLOWED_STATUS:
                return error_response(f"Invoice cannot be raised. Commission status is {commission.Commission_Status}")
            is_eligible, message = check_invoice_eligibility(commission)
            if not is_eligible:
                return error_response(message)
            if commission.commission_invoices.filter(Is_Deleted=False, Approval_Status__in=ACTIVE_INVOICE_STATUS).exists():
                return error_response("An invoice is already submitted for this commission")

            partner_invoice_no = (data.get('Partner_Invoice_No') or '').strip()
            if not data.get('Partner_Invoice_Date'):
                return error_response("Partner_Invoice_Date is required")
            invoice_file = request.FILES.get('Invoice_File')
            invoice_amount = validate_amount(data.get('Invoice_Amount'), 'Invoice_Amount')
            if invoice_amount > Decimal(commission.Commission_Amount or 0):
                return error_response(f"Invoice_Amount cannot exceed commission amount {commission.Commission_Amount}")

            # duplicate check only when the partner gives an invoice number
            if partner_invoice_no and PartnerCommissionInvoice.objects.filter(
                    Q(Partner_Id_id=commission.Partner_Id_id) &
                    Q(Partner_Invoice_No__iexact=partner_invoice_no) &
                    Q(Is_Deleted=False)
            ).exclude(Approval_Status='Rejected').exists():
                return error_response("This invoice number is already used")

            data['Partner_Id'] = commission.Partner_Id_id
            data['Created_By'] = commission.Partner_Id_id
            data['Partner_Invoice_No'] = partner_invoice_no or None
            if invoice_file:
                data['Invoice_File'] = invoice_file
                data['Invoice_File_Name'] = invoice_file.name[:100]
            data['Approval_Status'] = 'Submitted'
            data['Payment_Status'] = 'Pending'

            serializer = PartnerCommissionInvoiceSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                commission.Commission_Status = 'Invoice Submitted'
                commission.Updated_Date = timezone.now()
                commission.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except PartnerCommission.DoesNotExist:
            return error_response("PartnerCommission not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error_response(str(e))

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerCommissionInvoice.objects.get(id=id)
            serializer = PartnerCommissionInvoiceSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))

    def put(self, request, *args, **kwargs):
        try:
            data = get_data(request)
            id = data['id']
            module = PartnerCommissionInvoice.objects.get(id=id)
            if module.Approval_Status != 'Submitted':
                return error_response(f"Invoice cannot be changed once {module.Approval_Status}")

            for key in INVOICE_PROTECTED_FIELDS + ['Partner_Id', 'PartnerCommission_Id', 'Created_By']:
                data.pop(key, None)
            if 'Invoice_Amount' in data:
                invoice_amount = validate_amount(data['Invoice_Amount'], 'Invoice_Amount')
                if invoice_amount > Decimal(module.PartnerCommission_Id.Commission_Amount or 0):
                    return error_response(f"Invoice_Amount cannot exceed commission amount {module.PartnerCommission_Id.Commission_Amount}")
            if request.FILES.get('Invoice_File'):
                data['Invoice_File'] = request.FILES['Invoice_File']
                data['Invoice_File_Name'] = request.FILES['Invoice_File'].name[:100]

            data['Updated_Date'] = timezone.now()
            serializer = PartnerCommissionInvoiceSerializer(instance=module, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response(str(e))

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = PartnerCommissionInvoice.objects.get(id=id)
            if module.Approval_Status != 'Submitted':
                return error_response(f"Invoice cannot be deleted once {module.Approval_Status}")
            serializer = PartnerCommissionInvoiceSerializer(module, {"Is_Deleted": True, "Updated_Date": timezone.now()}, partial=True)
            if serializer.is_valid():
                serializer.save()
                # invoice withdrawn -> commission goes back to Eligible
                commission = module.PartnerCommission_Id
                commission.Commission_Status = 'Eligible'
                commission.Updated_Date = timezone.now()
                commission.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))

    def patch(self, request, *args, **kwargs):
        try:
            data = get_data(request)
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = PartnerCommissionInvoice.objects.get(id=id)
            if module.Approval_Status != 'Submitted':
                raise ValueError(f"Invoice cannot be changed once {module.Approval_Status}")

            for key in INVOICE_PROTECTED_FIELDS + ['Partner_Id', 'PartnerCommission_Id', 'Created_By']:
                data.pop(key, None)
            if 'Invoice_Amount' in data:
                invoice_amount = validate_amount(data['Invoice_Amount'], 'Invoice_Amount')
                if invoice_amount > Decimal(module.PartnerCommission_Id.Commission_Amount or 0):
                    raise ValueError(f"Invoice_Amount cannot exceed commission amount {module.PartnerCommission_Id.Commission_Amount}")
            if request.FILES.get('Invoice_File'):
                data['Invoice_File'] = request.FILES['Invoice_File']
                data['Invoice_File_Name'] = request.FILES['Invoice_File'].name[:100]

            data['Updated_Date'] = timezone.now()
            serializer = PartnerCommissionInvoiceSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PartnerCommissionInvoice.DoesNotExist:
            return Response({"Error": "PartnerCommissionInvoice not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PartnerCommissionInvoiceSearch(ListAPIView):
    queryset = PartnerCommissionInvoice.objects.all()
    serializer_class = PartnerCommissionInvoiceSerializers

    def get_queryset(self):
        try:
            data = self.request.GET.get('search', '')
            module = PartnerCommissionInvoice.objects.filter(
                (
                    Q(PartnerCommissionInvoice_id__icontains=data) |
                    Q(Partner_Invoice_No__icontains=data) |
                    Q(Approval_Status__icontains=data) |
                    Q(Payment_Status__icontains=data) |
                    Q(Payment_Reference_No__icontains=data)
                ) &
                Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching partner commission invoices: {str(e)}")


class PartnerCommissionInvoiceFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            data1 = {"Is_Deleted": False}
            if data.get("Partner_Id"):
                data1["Partner_Id_id"] = data["Partner_Id"]
            if data.get("PartnerCommission_Id"):
                data1["PartnerCommission_Id_id"] = data["PartnerCommission_Id"]
            if data.get("Approval_Status"):
                data1["Approval_Status"] = data["Approval_Status"]
            if data.get("Payment_Status"):
                data1["Payment_Status"] = data["Payment_Status"]
            if data.get("Approved_By"):
                data1["Approved_By_id"] = data["Approved_By"]
            if data.get("Partner_Invoice_Date"):
                data1["Partner_Invoice_Date__range"] = data["Partner_Invoice_Date"]
            if data.get("Created_Date"):
                data1["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(model=PartnerCommissionInvoice, serializer=PartnerCommissionInvoiceSerializers, data=data1, page=page, Operator='and')
        except Exception as e:
            raise Exception(f"Error while fetching partner commission invoices: {str(e)}")


class PartnerCommissionInvoiceList(ListAPIView):
    queryset = PartnerCommissionInvoice.objects.all()
    serializer_class = PartnerCommissionInvoiceSerializers

    def get_queryset(self):
        try:
            module = PartnerCommissionInvoice.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class PartnerCommissionInvoicewithoutpagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = PartnerCommissionInvoice.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = PartnerCommissionInvoiceSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))


# ==================== Partner Commission Invoice Approval (Super Admin) ====================

class PartnerCommissionInvoiceApproval(APIView):
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            approval_status = data.get('Approval_Status')
            rejection_reason = (data.get('Rejection_Reason') or '').strip()

            if approval_status not in ['Under Review', 'Approved', 'Rejected']:
                return error_response("Approval_Status must be Under Review, Approved or Rejected")
            if approval_status == 'Rejected' and not rejection_reason:
                return error_response("Rejection_Reason is required when rejecting")

            module = PartnerCommissionInvoice.objects.select_for_update().get(id=id, Is_Deleted=False)
            if module.Approval_Status in ['Approved', 'Rejected']:
                return error_response(f"Invoice is already {module.Approval_Status}")

            data1 = {"Approval_Status": approval_status, "Updated_Date": timezone.now()}
            commission = module.PartnerCommission_Id
            if approval_status == 'Approved':
                data1["Approved_By"] = data.get('Approved_By')
                data1["Approved_Date"] = timezone.now()
                data1["Rejection_Reason"] = None
                commission.Commission_Status = 'Approved'
            elif approval_status == 'Rejected':
                data1["Rejection_Reason"] = rejection_reason
                commission.Commission_Status = 'Rejected'   # partner can submit a new invoice

            serializer = PartnerCommissionInvoiceSerializer(instance=module, data=data1, partial=True)
            if serializer.is_valid():
                serializer.save()
                commission.Updated_Date = timezone.now()
                commission.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except PartnerCommissionInvoice.DoesNotExist:
            return error_response("PartnerCommissionInvoice not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error_response(str(e))


# ==================== Partner Commission Invoice Payment (Super Admin) ====================

class PartnerCommissionInvoicePayment(APIView):
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            payment_status = data.get('Payment_Status')
            payment_reference_no = (data.get('Payment_Reference_No') or '').strip()

            if payment_status not in ['Processing', 'Paid']:
                return error_response("Payment_Status must be Processing or Paid")
            if payment_status == 'Paid' and not payment_reference_no:
                return error_response("Payment_Reference_No is required when marking Paid")

            module = PartnerCommissionInvoice.objects.select_for_update().get(id=id, Is_Deleted=False)
            if module.Approval_Status != 'Approved':
                return error_response("Only approved invoices can be paid")
            if module.Payment_Status == 'Paid':
                return error_response("Invoice is already paid")

            data1 = {"Payment_Status": payment_status, "Updated_Date": timezone.now()}
            if payment_reference_no:
                data1["Payment_Reference_No"] = payment_reference_no
            if payment_status == 'Paid':
                data1["Payment_Date"] = data.get('Payment_Date') or timezone.now()

            serializer = PartnerCommissionInvoiceSerializer(instance=module, data=data1, partial=True)
            if serializer.is_valid():
                serializer.save()
                if payment_status == 'Paid':
                    commission = module.PartnerCommission_Id
                    commission.Commission_Status = 'Paid'
                    commission.Updated_Date = timezone.now()
                    commission.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except PartnerCommissionInvoice.DoesNotExist:
            return error_response("PartnerCommissionInvoice not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error_response(str(e))


# ==================== Partner Commission Calculation (Super Admin Invoice) ====================

class PartnerCommissionCalculate(APIView):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            data = request.data

            invoice = Invoice.objects.filter(id=data.get('Invoice_Id')).first()
            if not invoice:
                return error_response("Invoice not found", status.HTTP_404_NOT_FOUND)
            partner = Partner.objects.filter(id=data.get('Partner_Id')).first()
            if not partner:
                return error_response("Partner not found", status.HTTP_404_NOT_FOUND)
            customer = Account.objects.filter(id=data.get('Customer_Id')).first()
            if not customer:
                return error_response("Customer not found", status.HTTP_404_NOT_FOUND)
            instance_request = InstanceRequest.objects.filter(id=data.get('InstanceRequest_Id')).first() if data.get('InstanceRequest_Id') else None

            items = data.get('Items') or []
            if not isinstance(items, list) or not items:
                return error_response("Items is required")

            # validate every line first, so nothing is saved if one line is wrong
            for index, item in enumerate(items, start=1):
                if item.get('Commission_Type') not in COMMISSION_TYPE_LIST:
                    return error_response(f"Item {index}: Commission_Type must be one of {COMMISSION_TYPE_LIST}")
                validate_amount(item.get('Amount'), f"Item {index}: Amount")
                if item['Commission_Type'] in ['Product', 'Extension']:
                    if not item.get('Product_Id'):
                        return error_response(f"Item {index}: Product_Id is required for Product / Extension")
                    if not ProductMaster.objects.filter(id=item['Product_Id']).exists():
                        return error_response(f"Item {index}: Product not found", status.HTTP_404_NOT_FOUND)

            save = data.get('Save', True) not in [False, 'false', 'False', 0, '0']
            results = calculate_invoice_commissions(invoice, partner, customer, items, instance_request, save=save)

            total = sum(Decimal(row['Commission_Amount']) for row in results)
            output = JSONRenderer().render({
                "Invoice_Id": invoice.id,
                "Partner_Id": partner.id,
                "Customer_Id": customer.id,
                "Saved": save,
                "Total_Commission_Amount": str(total),
                "Commissions": results,
            })
            return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED if save else status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))


# ==================== Eligible Commissions for Invoice (Partner - My Invoice create dropdown) ====================

class PartnerCommissionEligibleForInvoice(APIView):
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            partner_id = data['Partner_Id']
            module = PartnerCommission.objects.filter(
                Q(Partner_Id_id=partner_id) &
                Q(Commission_Status__in=INVOICE_ALLOWED_STATUS) &
                Q(Is_Deleted=False)
            ).exclude(
                id__in=PartnerCommissionInvoice.objects.filter(
                    Is_Deleted=False, Approval_Status__in=ACTIVE_INVOICE_STATUS
                ).values('PartnerCommission_Id')
            ).order_by('-id')
            output = JSONRenderer().render([commission_with_info(obj) for obj in module])
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(str(e))







