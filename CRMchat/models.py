from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from CRMUserAdmin.models import *
from CRMSuperAdmin.models import *

# Create your models here.
class ChatRoom(models.Model): # Is this chat is private or group
    ROOM_TYPE = (
        ("private", "Private"),
        ("group", "Group"),
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE, default="private")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    # Defect_Id = models.OneToOneField(DefectTracking,on_delete=models.CASCADE,null=True,blank=True)
    # Ticket_Id = models.OneToOneField(TicketManagement,on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return f"{self.room_type} - {self.id}"

    class Meta:
        db_table = "ChatRoom"


class ChatParticipant(models.Model):  # It stores the user belongs to which room
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='CreatedChatParticipant')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)

    class Meta:
        unique_together = ("room", "user")
        db_table = "ChatParticipant"

class Message(models.Model):

    MESSAGE_TYPE = (
        ("text", "Text"),
        ("image", "Image"),
        ("video", "Video"),
        ("document", "Document"),
        ("audio", "Audio"),
    )

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")

    sender = models.ForeignKey(User, on_delete=models.CASCADE)

    message = models.TextField(blank=True, null=True)

    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE, default="text")

    reply_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replies"
    )
    is_edited = models.BooleanField(default=False)

    is_deleted_for_everyone = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sender} - {self.room}"
    class Meta:
        db_table = "Message"


class MessageEditHistory(models.Model):

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="edit_history")

    old_message = models.TextField()

    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table="MessageEditHistory"


class MessageAttachment(models.Model):

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")

    # file = models.FileField(upload_to="chat_attachments/")
    file=models.FileField(blank=True,null=True)

    file_type = models.CharField(max_length=50)

    file_size = models.IntegerField(null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table="MessageAttachment"



class MessageReadStatus(models.Model):

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="read_status")

    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='CreatedMessageReadStatus')

    is_read = models.BooleanField(default=False)

    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("message", "user")
        db_table="MessageReadStatus"


class MessageVisibility(models.Model):

    message = models.ForeignKey(Message, on_delete=models.CASCADE,related_name='CreatedMessageVisibility')

    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='CreatedMessage')

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("message", "user")
        db_table="MessageVisibility"

class MessageReaction(models.Model):

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    reaction = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user")
        db_table="MessageReaction"

class ChatNotificationSetting(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_settings', blank=True, null=True)
    Room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="notification_settings", blank = True, null=True)
    Enable_Notifications = models.BooleanField(default=True)
    Notification_Sound = models.FileField(blank=True,null=True)
    Is_Deleted = models.BooleanField(default=False)
    # Volume_Percent = models.CharField(max_length=100, blank=True, null=True)
    Created_Date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    Updated_Date =  models.DateTimeField(default=timezone.now, blank=True, null=True)

    class Meta:
        db_table = "ChatNotificationSetting"