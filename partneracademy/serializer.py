
from rest_framework import serializers
from .models import *


class TrainingProductModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingProductModule
        fields = '__all__'


class TrainingProductModuleSerializers(serializers.ModelSerializer):
    class Meta:
        model = TrainingProductModule
        fields = '__all__'
        depth = 1


class TrainingVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingVideo
        fields = '__all__'


class TrainingVideoSerializers(serializers.ModelSerializer):
    class Meta:
        model = TrainingVideo
        fields = '__all__'
        depth = 1


class ModuleEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleEnrollment
        fields = '__all__'


class ModuleEnrollmentSerializers(serializers.ModelSerializer):
    class Meta:
        model = ModuleEnrollment
        fields = '__all__'
        depth = 1


class VideoProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoProgress
        fields = '__all__'


class VideoProgressSerializers(serializers.ModelSerializer):
    class Meta:
        model = VideoProgress
        fields = '__all__'
        depth = 1


class VideoWatchSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoWatchSession
        fields = '__all__'


class VideoWatchSessionSerializers(serializers.ModelSerializer):
    class Meta:
        model = VideoWatchSession
        fields = '__all__'
        depth = 1


class VideoWatchIntervalSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoWatchInterval
        fields = '__all__'


class VideoWatchIntervalSerializers(serializers.ModelSerializer):
    class Meta:
        model = VideoWatchInterval
        fields = '__all__'
        depth = 1


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'


class CertificateSerializers(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'
        depth = 1


class AcademyNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademyNotification
        fields = '__all__'


class AcademyNotificationSerializers(serializers.ModelSerializer):
    class Meta:
        model = AcademyNotification
        fields = '__all__'
        depth = 1


class TechnicalDocumentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalDocumentation
        fields = '__all__'


class TechnicalDocumentationSerializers(serializers.ModelSerializer):
    class Meta:
        model = TechnicalDocumentation
        fields = '__all__'
        depth = 1



class PartnerFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerFAQ
        fields = '__all__'


class PartnerFAQSerializers(serializers.ModelSerializer):
    class Meta:
        model = PartnerFAQ
        fields = '__all__'
        depth = 1
