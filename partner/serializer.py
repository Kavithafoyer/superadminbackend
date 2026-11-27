from rest_framework import serializers
from .models import *


# -----------------------------------------------------------------------------
# 1. PARTNER ONBOARDING & CORE
# -----------------------------------------------------------------------------

class PartnerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerApplication
        fields = '__all__'


class PartnerApplicationSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerApplication
        fields = '__all__'
        depth = 1


class KycRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = KycRecord
        fields = '__all__'


class KycRecordSerializers(serializers.ModelSerializer):
    class Meta:
        model = KycRecord
        fields = '__all__'
        depth = 1


class PartnerAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerAgreement
        fields = '__all__'


class PartnerAgreementSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerAgreement
        fields = '__all__'
        depth = 1

class AgreementTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgreementTemplate
        fields = '__all__'

# class PartnerMailConfigurationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PartnerMailConfiguration
#         fields = '__all__'


# read serializer: the password is never sent back to the frontend
class PartnerMailConfigurationSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerMailConfiguration
        exclude = ['MailPassword']


class PartnerMailConfigurationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PartnerMailConfiguration
        fields = '__all__'
        extra_kwargs = {
            'MailPassword': {'write_only': True}
        }

class AgreementTemplateSerializers(serializers.ModelSerializer):
    class Meta:
        model = AgreementTemplate
        fields = '__all__'
        depth = 1

class PartnerInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerInvitation
        fields = '__all__'


class PartnerInvitationSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerInvitation
        fields = '__all__'
        depth = 1


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = '__all__'
        extra_kwargs = {
            'Password': {'write_only': True}
        }


class PartnerSerializers(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = '__all__'
        depth = 1
        extra_kwargs = {
            'Password': {'write_only': True}
        }


class PartnerProductSupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerProductSupport
        fields = '__all__'


class PartnerProductSupportSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerProductSupport
        fields = '__all__'
        depth = 1


# -----------------------------------------------------------------------------
# 2. BUSINESS DOMAIN
# -----------------------------------------------------------------------------

class PartnerCustomerLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerCustomerLead
        fields = '__all__'


class PartnerCustomerLeadSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerCustomerLead
        fields = '__all__'
        depth = 1


class PartnerOpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerOpportunity
        fields = '__all__'


class PartnerOpportunitySerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerOpportunity
        fields = '__all__'
        depth = 1


class PartnerCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerCustomer
        fields = '__all__'


class PartnerCustomerSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerCustomer
        fields = '__all__'
        depth = 1


class BusinessCommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCommission
        fields = '__all__'


class BusinessCommissionSerializers(serializers.ModelSerializer):
    class Meta:
        model = BusinessCommission
        fields = '__all__'
        depth = 1


class PartnerPayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerPayout
        fields = '__all__'


class PartnerPayoutSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerPayout
        fields = '__all__'
        depth = 1


class BusinessResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessResource
        fields = '__all__'


class BusinessResourceSerializers(serializers.ModelSerializer):
    class Meta:
        model = BusinessResource
        fields = '__all__'
        depth = 1


# -----------------------------------------------------------------------------
# 3. DELIVERY DOMAIN
# -----------------------------------------------------------------------------

class ImplementationProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImplementationProject
        fields = '__all__'


class ImplementationProjectSerializers(serializers.ModelSerializer):
    class Meta:
        model = ImplementationProject
        fields = '__all__'
        depth = 1


class DailyWorkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyWorkUpdate
        fields = '__all__'


class DailyWorkUpdateSerializers(serializers.ModelSerializer):
    class Meta:
        model = DailyWorkUpdate
        fields = '__all__'
        depth = 1


class TenantProvisioningJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantProvisioningJob
        fields = '__all__'


class TenantProvisioningJobSerializers(serializers.ModelSerializer):
    class Meta:
        model = TenantProvisioningJob
        fields = '__all__'
        depth = 1


class PartnerTeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerTeamMember
        fields = '__all__'
        extra_kwargs = {
            'Password': {'write_only': True}
        }


class PartnerTeamMemberSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerTeamMember
        fields = '__all__'
        depth = 1
        extra_kwargs = {
            'Password': {'write_only': True}
        }


class PartnerDealSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerDeal
        fields = '__all__'


class PartnerDealSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerDeal
        fields = '__all__'
        depth = 1



class PartnerCommissionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerCommissionRule
        fields = '__all__'


class PartnerCommissionRuleSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerCommissionRule
        fields = '__all__'
        depth = 1


class PartnerCommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerCommission
        fields = '__all__'


class PartnerCommissionSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerCommission
        fields = '__all__'
        depth = 1


class PartnerCommissionInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerCommissionInvoice
        fields = '__all__'


class PartnerCommissionInvoiceSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerCommissionInvoice
        fields = '__all__'
        depth = 1



