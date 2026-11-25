from rest_framework import serializers
from .models import *

class ChatRoom_serializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = '__all__'

class ChatParticipant_serializer(serializers.ModelSerializer):

    class Meta:
        model = ChatParticipant
        fields = '__all__'


class Message_serializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = '__all__'

class MessageEditHistory_serializer(serializers.ModelSerializer):

    class Meta:
        model = MessageEditHistory
        fields = '__all__'


class MessageAttachment_serializer(serializers.ModelSerializer):

    class Meta:
        model = MessageAttachment
        fields = '__all__'



class MessageReadStatus_serializer(serializers.ModelSerializer):

    class Meta:
        model = MessageReadStatus
        fields = '__all__'


class MessageVisibility_serializer(serializers.ModelSerializer):

    class Meta:
        model = MessageVisibility
        fields = '__all__'


class MessageReaction_serializer(serializers.ModelSerializer):

    class Meta:
        model = MessageReaction
        fields = '__all__'

class ChatNotificationSetting_serializer(serializers.ModelSerializer):

    class Meta:
        model = ChatNotificationSetting
        fields = '__all__'

class Message_serializers(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        depth = 1