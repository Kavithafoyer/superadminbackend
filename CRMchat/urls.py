from django.urls import path
from CRMchat.views import *

urlpatterns=[
path('ChatRoomCRUD/',ChatRoomCRUD.as_view()),
path('ChatRoomListwithPagination/',ChatRoomListwithPagination.as_view()),
path('ChatRoomSearch/',ChatRoomSearch.as_view()),

path('ChatParticipantCRUD/',ChatParticipantCRUD.as_view()),
path('ChatParticipantList/',ChatParticipantListwithPagination.as_view()),
path('ChatParticipantSearch/',ChatParticipantSearch.as_view()),


path('MessageCRUD/',MessageCRUD.as_view()),
path('MessageList/',MessageListwithPagination.as_view()),
path('MessageSearch/',MessageSearch.as_view()),

path('MessageEditHistoryCRUD/',MessageEditHistoryCRUD.as_view()),
path('MessageEditHistoryList/',MessageEditHistoryListwithPagination.as_view()),
path('MessageEditHistorySearch/',MessageEditHistorySearch.as_view()),

path('MessageAttachmentCRUD/',MessageAttachmentCRUD.as_view()),
path('MessageAttachmentList/',MessageAttachmentListwithPagination.as_view()),
path('MessageAttachmentSearch/',MessageAttachmentSearch.as_view()),

path('MessageReadStatusCRUD/',MessageReadStatusCRUD.as_view()),
path('MessageReadStatusList/',MessageReadStatusListwithPagination.as_view()),
path('MessageReadStatusSearch/',MessageReadStatusSearch.as_view()),

path('MessageVisibilityCRUD/',MessageVisibilityCRUD.as_view()),
path('MessageVisibilityList/',MessageVisibilityListwithPagination.as_view()),
path('MessageVisibilitySearch/',MessageVisibilitySearch.as_view()),

path('MessageReactionCRUD/',MessageReactionCRUD.as_view()),
path('MessageReactionList/',MessageReactionListwithPagination.as_view()),
path('MessageReactionSearch/',MessageReactionSearch.as_view()),

path('CheckPrivateRoom/',CheckPrivateRoom.as_view()),
path('UserChatList/',UserChatList.as_view()),
# path('CheckUserInRoom/',CheckUserInRoom.as_view()),


]