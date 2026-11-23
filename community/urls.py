
from django.urls import path

from . import views

app_name = "community"

urlpatterns = [
    # Community dashboard and home
    path("", views.community_home, name="home"),
    path("dashboard/", views.community_dashboard, name="dashboard"),

    # Groups
    path("create/", views.create_group, name="create_group"),
    path("my-groups/", views.my_groups, name="my_groups"),

    # Group details and membership
    path("group/<slug:slug>/", views.group_detail, name="group_detail"),
    path("group/<slug:slug>/join/", views.request_to_join, name="request_to_join"),

    path(
        "group/<slug:slug>/membership/<int:membership_id>/<str:action>/",
        views.manage_membership,
        name="manage_membership",
    ),

    # Group posts and comments
    path("group/<slug:slug>/post/", views.create_post, name="create_post"),
    path(
        "group/<slug:slug>/post/<int:post_id>/comment/",
        views.create_comment,
        name="create_comment",
    ),

    # Group chat
    path("group/<slug:slug>/chat/", views.group_chat, name="group_chat"),
    path(
        "group/<slug:slug>/chat/send/",
        views.send_chat_message,
        name="send_chat_message",
    ),
    path(
        "group/<slug:slug>/chat/message/<int:message_id>/reaction/",
        views.toggle_chat_reaction,
        name="toggle_chat_reaction",
    ),

    # ======================================================
    # STUDY BUDDIES
    # ======================================================

    path(
        "study-buddies/",
        views.study_buddy_discover,
        name="study_buddy_discover",
    ),
    path(
        "study-buddies/profile/",
        views.study_buddy_profile,
        name="study_buddy_profile",
    ),
    path(
        "study-buddies/requests/",
        views.study_buddy_requests,
        name="study_buddy_requests",
    ),
    path(
        "study-buddies/partners/",
        views.study_buddy_partners,
        name="study_buddy_partners",
    ),
    path(
        "study-buddies/send/<int:user_id>/",
        views.send_study_buddy_request,
        name="send_study_buddy_request",
    ),
    path(
        "study-buddies/request/<int:request_id>/<str:action>/",
        views.manage_study_buddy_request,
        name="manage_study_buddy_request",
    ),

# PRIVATE STUDENT MESSAGING
path(
    "messages/",
    views.private_message_inbox,
    name="private_message_inbox",
),
path(
    "messages/start/<int:request_id>/",
    views.start_private_conversation,
    name="start_private_conversation",
),
path(
    "messages/<int:conversation_id>/",
    views.private_conversation_detail,
    name="private_conversation_detail",
),
path(
    "messages/<int:conversation_id>/send/",
    views.send_private_message,
    name="send_private_message",
),

]
