
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db.models import Prefetch

from .forms import (
    CommunityGroupForm,
    GroupPostForm,
    GroupCommentForm,
    StudyBuddyProfileForm,
    StudyBuddyRequestForm,
    PrivateMessageForm,
)

from .models import (
    CommunityGroup,
    GroupMembership,
    GroupPost,
    GroupComment,
    ChatMessage,
    ChatMessageReaction,
    StudyBuddyProfile,
    StudyBuddyRequest,
    PrivateConversation,
    PrivateMessage,
    StudyBuddyRequest,
)


# ==========================================================
# PERMISSION HELPERS
# ==========================================================

def is_student(user):
    return (
        user.is_authenticated
        and getattr(user, "role", None) == "student"
    )


def is_admin(user):
    return (
        user.is_authenticated
        and (
            getattr(user, "role", None) == "admin"
            or user.is_staff
            or user.is_superuser
        )
    )


def can_manage_group_memberships(group, user):
    if is_admin(user):
        return True

    return GroupMembership.objects.filter(
        group=group,
        user=user,
        role=GroupMembership.Role.CARETAKER,
        status=GroupMembership.Status.ACTIVE,
    ).exists()


def active_membership(group, user):
    return GroupMembership.objects.filter(
        group=group,
        user=user,
        status=GroupMembership.Status.ACTIVE,
    ).exists()


def get_approved_group(slug):
    return get_object_or_404(
        CommunityGroup,
        slug=slug,
        review_status=CommunityGroup.ReviewStatus.APPROVED,
    )


def require_active_group_member(request, group):
    """
    Checks whether the current user has active membership
    in the supplied Community group.
    """
    if not is_student(request.user):
        return False

    return active_membership(group, request.user)


# ==========================================================
# COMMUNITY DASHBOARD
# ==========================================================

@login_required
def community_dashboard(request):
    if not is_student(request.user):
        return redirect("/")

    user = request.user

    # Active groups the student belongs to.
    active_memberships = (
        GroupMembership.objects
        .filter(
            user=user,
            status=GroupMembership.Status.ACTIVE,
        )
        .select_related("group")
        .order_by("-joined_at")
    )

    joined_group_ids = list(
        active_memberships.values_list("group_id", flat=True)
    )

    # Membership requests awaiting action in groups
    # created or managed by this student.
    managed_group_ids = CommunityGroup.objects.filter(
        created_by=user
    ).values_list("id", flat=True)

    caretaker_group_ids = GroupMembership.objects.filter(
        user=user,
        role=GroupMembership.Role.CARETAKER,
        status=GroupMembership.Status.ACTIVE,
    ).values_list("group_id", flat=True)

    pending_requests_count = (
        GroupMembership.objects
        .filter(
            group_id__in=list(managed_group_ids) + list(caretaker_group_ids),
            status=GroupMembership.Status.PENDING,
            role=GroupMembership.Role.MEMBER,
        )
        .exclude(user=user)
        .count()
    )

    # Available approved groups the student has not joined.
    available_groups = (
        CommunityGroup.objects
        .filter(
            review_status=CommunityGroup.ReviewStatus.APPROVED,
        )
        .exclude(
            memberships__user=user,
        )
        .select_related(
            "created_by",
            "school_class",
            "exam",
            "exam_subject",
            "tech_course",
        )
        .order_by("-created_at")
    )

    available_groups_count = available_groups.count()
    recommended_groups = available_groups[:6]

    # Discussion and chat activity from groups the student
    # is currently an active member of.
    if joined_group_ids:
        discussions_count = GroupPost.objects.filter(
            group_id__in=joined_group_ids
        ).count()

        comments_count = GroupComment.objects.filter(
            post__group_id__in=joined_group_ids
        ).count()

        messages_count = ChatMessage.objects.filter(
            group_id__in=joined_group_ids
        ).count()

        recent_posts = list(
            GroupPost.objects
            .filter(group_id__in=joined_group_ids)
            .select_related("author", "group")
            .order_by("-created_at")[:5]
        )

        recent_messages = list(
            ChatMessage.objects
            .filter(group_id__in=joined_group_ids)
            .select_related("sender", "group")
            .order_by("-created_at")[:5]
        )

    else:
        discussions_count = 0
        comments_count = 0
        messages_count = 0
        recent_posts = []
        recent_messages = []

    # Combine recent discussions and messages.
    recent_activity = []

    for post in recent_posts:
        post.activity_type = "discussion"
        post.activity_group = post.group
        post.activity_author = post.author
        recent_activity.append(post)

    for chat_message in recent_messages:
        chat_message.activity_type = "message"
        chat_message.activity_group = chat_message.group
        chat_message.activity_author = chat_message.sender
        recent_activity.append(chat_message)

    recent_activity.sort(
        key=lambda item: item.created_at,
        reverse=True,
    )

    recent_activity = recent_activity[:8]

    # Groups created by the current student.
    created_groups = (
        CommunityGroup.objects
        .filter(created_by=user)
        .order_by("-created_at")[:5]
    )

    context = {
        "nav_active": "dashboard",
        "active_memberships": active_memberships[:6],
        "joined_groups_count": len(joined_group_ids),
        "created_groups": created_groups,
        "created_groups_count": CommunityGroup.objects.filter(
            created_by=user
        ).count(),
        "pending_requests_count": pending_requests_count,
        "available_groups": recommended_groups,
        "available_groups_count": available_groups_count,
        "discussions_count": discussions_count,
        "comments_count": comments_count,
        "messages_count": messages_count,
        "recent_activity": recent_activity,
    }

    return render(
        request,
        "community/dashboard.html",
        context,
    )


# ==========================================================
# COMMUNITY HOMEPAGE
# ==========================================================

@login_required
def community_home(request):
    if not is_student(request.user):
        return redirect("/")

    groups = (
        CommunityGroup.objects
        .filter(
            review_status=CommunityGroup.ReviewStatus.APPROVED
        )
        .select_related(
            "created_by",
            "school_class",
            "exam",
            "exam_subject",
            "tech_course",
        )
        .order_by("-created_at")
    )

    memberships = {
        membership.group_id: membership.status
        for membership in GroupMembership.objects.filter(
            user=request.user,
        ).only("group_id", "status")
    }

    for group in groups:
        group.current_membership_status = memberships.get(group.id)

    return render(
        request,
        "community/home.html",
        {
            "groups": groups,
            "nav_active": "community",
        },
    )


# ==========================================================
# CREATE COMMUNITY GROUP
# ==========================================================

@login_required
def create_group(request):
    if not is_student(request.user):
        return redirect("/")

    if request.method == "POST":
        form = CommunityGroupForm(
            request.POST,
            student=request.user,
        )

        if form.is_valid():
            try:
                with transaction.atomic():
                    group = form.save(commit=False)

                    group.created_by = request.user
                    group.review_status = (
                        CommunityGroup.ReviewStatus.PENDING
                    )
                    group.reviewed_by = None
                    group.reviewed_at = None

                    if not group.slug:
                        base_slug = (
                            slugify(group.name) or "community-group"
                        )
                        slug = base_slug
                        counter = 1

                        while CommunityGroup.objects.filter(
                            slug=slug
                        ).exists():
                            counter += 1
                            slug = f"{base_slug}-{counter}"

                        group.slug = slug

                    group.full_clean()
                    group.save()

                    GroupMembership.objects.get_or_create(
                        group=group,
                        user=request.user,
                        defaults={
                            "role": GroupMembership.Role.MEMBER,
                            "status": GroupMembership.Status.ACTIVE,
                        },
                    )

                messages.success(
                    request,
                    "Your group has been submitted for administrative review.",
                )

                return redirect("community:my_groups")

            except ValidationError as error:
                if hasattr(error, "message_dict"):
                    for field, errors in error.message_dict.items():
                        if field in form.fields:
                            for error_message in errors:
                                form.add_error(
                                    field,
                                    error_message,
                                )
                        else:
                            for error_message in errors:
                                form.add_error(
                                    None,
                                    error_message,
                                )
                else:
                    for error_message in error.messages:
                        form.add_error(None, error_message)

    else:
        form = CommunityGroupForm(student=request.user)

    return render(
        request,
        "community/create_group.html",
        {
            "form": form,
            "nav_active": "community",
        },
    )


# ==========================================================
# MY GROUPS
# ==========================================================

@login_required
def my_groups(request):
    if not is_student(request.user):
        return redirect("/")

    memberships = (
        GroupMembership.objects
        .filter(user=request.user)
        .select_related("group")
        .order_by("-joined_at")
    )

    return render(
        request,
        "community/my_groups.html",
        {
            "memberships": memberships,
            "nav_active": "community",
        },
    )


# ==========================================================
# GROUP DETAILS
# ==========================================================

@login_required
def group_detail(request, slug):
    if not is_student(request.user):
        return redirect("/")

    group = get_object_or_404(
        CommunityGroup.objects.select_related(
            "created_by",
            "school_class",
            "exam",
            "exam_subject",
            "tech_course",
        ),
        slug=slug,
        review_status=CommunityGroup.ReviewStatus.APPROVED,
    )

    membership = GroupMembership.objects.filter(
        group=group,
        user=request.user,
    ).first()

    is_member = (
        membership is not None
        and membership.status == GroupMembership.Status.ACTIVE
    )

    can_manage_memberships = can_manage_group_memberships(
        group,
        request.user,
    )

    pending_memberships = GroupMembership.objects.none()
    active_memberships = GroupMembership.objects.none()

    if can_manage_memberships:
        pending_memberships = (
            GroupMembership.objects
            .filter(
                group=group,
                status=GroupMembership.Status.PENDING,
                role=GroupMembership.Role.MEMBER,
            )
            .select_related("user")
            .order_by("joined_at")
        )

        active_memberships = (
            GroupMembership.objects
            .filter(
                group=group,
                status=GroupMembership.Status.ACTIVE,
                role=GroupMembership.Role.MEMBER,
            )
            .select_related("user")
            .order_by("joined_at")
        )

    posts = (
        GroupPost.objects
        .filter(group=group)
        .select_related("author")
        .prefetch_related(
            Prefetch(
                "comments",
                queryset=GroupComment.objects.select_related("author"),
            )
        )
        if is_member
        else GroupPost.objects.none()
    )

    return render(
        request,
        "community/group_detail.html",
        {
            "group": group,
            "membership": membership,
            "is_member": is_member,
            "posts": posts,
            "post_form": GroupPostForm(),
            "comment_form": GroupCommentForm(),
            "can_manage_memberships": can_manage_memberships,
            "pending_memberships": pending_memberships,
            "active_memberships": active_memberships,
            "nav_active": "community",
        },
    )


# ==========================================================
# REQUEST TO JOIN A GROUP
# ==========================================================

@login_required
@require_POST
def request_to_join(request, slug):
    if not is_student(request.user):
        return redirect("/")

    group = get_approved_group(slug)

    membership, created = GroupMembership.objects.get_or_create(
        group=group,
        user=request.user,
        defaults={
            "role": GroupMembership.Role.MEMBER,
            "status": GroupMembership.Status.PENDING,
        },
    )

    if created:
        messages.success(
            request,
            "Your request to join this group has been submitted.",
        )

    elif membership.status == GroupMembership.Status.PENDING:
        messages.info(
            request,
            "Your membership request is still awaiting approval.",
        )

    elif membership.status == GroupMembership.Status.ACTIVE:
        messages.info(
            request,
            "You are already a member of this group.",
        )

    else:
        messages.warning(
            request,
            "You cannot request membership in this group at the moment.",
        )

    return redirect("community:group_detail", slug=slug)


# ==========================================================
# MANAGE GROUP MEMBERSHIPS
# ==========================================================

@login_required
@require_POST
def manage_membership(request, slug, membership_id, action):
    if not is_student(request.user) and not is_admin(request.user):
        return redirect("/")

    group = get_approved_group(slug)

    if not can_manage_group_memberships(group, request.user):
        messages.error(
            request,
            "You are not authorized to manage this group's memberships.",
        )
        return redirect("community:group_detail", slug=slug)

    membership = get_object_or_404(
        GroupMembership.objects.select_related("user"),
        pk=membership_id,
        group=group,
    )

    if not is_admin(request.user):
        if (
            membership.user_id == request.user.id
            or membership.user_id == group.created_by_id
            or membership.role == GroupMembership.Role.CARETAKER
        ):
            messages.error(
                request,
                "You cannot manage this membership.",
            )
            return redirect("community:group_detail", slug=slug)

    if action == "approve":
        if membership.status != GroupMembership.Status.PENDING:
            messages.warning(
                request,
                "This request is no longer pending.",
            )
        else:
            membership.status = GroupMembership.Status.ACTIVE
            membership.reviewed_by = request.user
            membership.reviewed_at = timezone.now()

            membership.save(
                update_fields=[
                    "status",
                    "reviewed_by",
                    "reviewed_at",
                    "updated_at",
                ]
            )

            messages.success(request, "Membership approved.")

    elif action == "reject":
        if membership.status != GroupMembership.Status.PENDING:
            messages.warning(
                request,
                "Only pending requests can be rejected.",
            )
        else:
            membership.status = GroupMembership.Status.REJECTED
            membership.reviewed_by = request.user
            membership.reviewed_at = timezone.now()

            membership.save(
                update_fields=[
                    "status",
                    "reviewed_by",
                    "reviewed_at",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                "Membership request rejected.",
            )

    elif action == "ban":
        if membership.status != GroupMembership.Status.ACTIVE:
            messages.warning(
                request,
                "Only active members can be restricted.",
            )
        else:
            membership.status = GroupMembership.Status.BANNED
            membership.reviewed_by = request.user
            membership.reviewed_at = timezone.now()

            membership.save(
                update_fields=[
                    "status",
                    "reviewed_by",
                    "reviewed_at",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                "Member has been restricted.",
            )

    else:
        messages.error(request, "Invalid membership action.")

    return redirect("community:group_detail", slug=slug)


# ==========================================================
# CREATE GROUP DISCUSSION POST
# ==========================================================

@login_required
@require_POST
def create_post(request, slug):
    if not is_student(request.user):
        return redirect("/")

    group = get_approved_group(slug)

    if not active_membership(group, request.user):
        messages.error(
            request,
            "You must be an active member to publish a discussion.",
        )
        return redirect("community:group_detail", slug=slug)

    form = GroupPostForm(request.POST)

    if form.is_valid():
        post = form.save(commit=False)
        post.group = group
        post.author = request.user
        post.save()

        messages.success(
            request,
            "Your discussion has been published.",
        )
    else:
        messages.error(
            request,
            "Please enter a valid discussion.",
        )

    return redirect("community:group_detail", slug=slug)


# ==========================================================
# CREATE DISCUSSION COMMENT
# ==========================================================

@login_required
@require_POST
def create_comment(request, slug, post_id):
    if not is_student(request.user):
        return redirect("/")

    group = get_approved_group(slug)

    post = get_object_or_404(
        GroupPost,
        pk=post_id,
        group=group,
    )

    if not active_membership(group, request.user):
        messages.error(
            request,
            "You must be an active member to comment.",
        )
        return redirect("community:group_detail", slug=slug)

    form = GroupCommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()

        messages.success(
            request,
            "Your comment has been added.",
        )
    else:
        messages.error(
            request,
            "Please enter a valid comment.",
        )

    return redirect("community:group_detail", slug=slug)


# ==========================================================
# DEDICATED GROUP CHAT PAGE
# ==========================================================

@login_required
def group_chat(request, slug):
    """
    Displays the dedicated conversation page for a group.

    Only active student members of approved groups can
    access the conversation.
    """

    if not is_student(request.user):
        return redirect("/")

    group = get_object_or_404(
        CommunityGroup.objects.select_related("created_by"),
        slug=slug,
        review_status=CommunityGroup.ReviewStatus.APPROVED,
    )

    membership = GroupMembership.objects.filter(
        group=group,
        user=request.user,
        status=GroupMembership.Status.ACTIVE,
    ).first()

    if not membership:
        messages.error(
            request,
            "You must be an active member to access this group chat.",
        )
        return redirect("community:group_detail", slug=slug)

    # Load the latest 100 messages, then restore chronological order.
    latest_messages = list(
        ChatMessage.objects
        .filter(group=group)
        .select_related(
            "sender",
            "reply_to",
            "reply_to__sender",
        )
        .prefetch_related(
            Prefetch(
                "reactions",
                queryset=ChatMessageReaction.objects.select_related("user"),
            )
        )
        .order_by("-created_at")[:100]
    )

    chat_messages = list(reversed(latest_messages))

    members = (
        GroupMembership.objects
        .filter(
            group=group,
            status=GroupMembership.Status.ACTIVE,
        )
        .select_related("user")
        .order_by("joined_at")
    )

    return render(
        request,
        "community/group_chat.html",
        {
            "group": group,
            "membership": membership,
            "chat_messages": chat_messages,
            "members": members,
            "member_count": members.count(),
            "nav_active": "community",
        },
    )


# ==========================================================
# SEND GROUP CHAT MESSAGE
# ==========================================================

@login_required
@require_POST
def send_chat_message(request, slug):
    """
    Saves a new chat message.

    Supports replying to another message through the
    optional reply_to POST field.
    """

    if not is_student(request.user):
        return redirect("/")

    group = get_approved_group(slug)

    if not active_membership(group, request.user):
        messages.error(
            request,
            "You must be an active member to send messages.",
        )
        return redirect("community:group_detail", slug=slug)

    content = request.POST.get("content", "").strip()

    if not content:
        messages.warning(
            request,
            "You cannot send an empty message.",
        )
        return redirect("community:group_chat", slug=slug)

    if len(content) > 5000:
        messages.error(
            request,
            "Your message cannot exceed 5,000 characters.",
        )
        return redirect("community:group_chat", slug=slug)

    reply_to = None
    reply_to_id = request.POST.get("reply_to", "").strip()

    if reply_to_id:
        try:
            reply_to = ChatMessage.objects.get(
                pk=int(reply_to_id),
                group=group,
            )
        except (ValueError, ChatMessage.DoesNotExist):
            messages.error(
                request,
                "The message you are replying to could not be found.",
            )
            return redirect("community:group_chat", slug=slug)

    try:
        chat_message = ChatMessage(
            group=group,
            sender=request.user,
            content=content,
            reply_to=reply_to,
        )

        chat_message.full_clean()
        chat_message.save()

        messages.success(
            request,
            "Message sent.",
        )

    except ValidationError as error:
        for error_message in error.messages:
            messages.error(request, error_message)

    return redirect("community:group_chat", slug=slug)


# ==========================================================
# CHAT MESSAGE REACTIONS
# ==========================================================

@login_required
@require_POST
def toggle_chat_reaction(request, slug, message_id):
    """
    Adds or removes an emoji reaction from a chat message.

    A user can have one instance of each emoji reaction
    on an individual message.
    """

    if not is_student(request.user):
        return redirect("/")

    group = get_approved_group(slug)

    if not active_membership(group, request.user):
        messages.error(
            request,
            "You must be an active member to react to messages.",
        )
        return redirect("community:group_detail", slug=slug)

    chat_message = get_object_or_404(
        ChatMessage,
        pk=message_id,
        group=group,
    )

    emoji = request.POST.get("emoji", "").strip()

    allowed_emojis = {
        "👍",
        "❤️",
        "😂",
        "😮",
        "😢",
        "🔥",
        "👏",
        "🎉",
    }

    if emoji not in allowed_emojis:
        messages.error(
            request,
            "That reaction is not supported.",
        )
        return redirect("community:group_chat", slug=slug)

    reaction = ChatMessageReaction.objects.filter(
        message=chat_message,
        user=request.user,
        emoji=emoji,
    ).first()

    if reaction:
        reaction.delete()
    else:
        ChatMessageReaction.objects.create(
            message=chat_message,
            user=request.user,
            emoji=emoji,
        )

    return redirect("community:group_chat", slug=slug)


# ==========================================================
# STUDY BUDDY DISCOVERY
# ==========================================================

@login_required
def study_buddy_discover(request):
    """
    Allows students to discover other students who want
    study partners.
    """

    if not is_student(request.user):
        return redirect("/")

    profiles = (
        StudyBuddyProfile.objects
        .filter(
            is_discoverable=True,
            user__role="student",
        )
        .exclude(user=request.user)
        .select_related("user")
        .order_by("-updated_at")
    )

    search_query = request.GET.get("q", "").strip()
    study_mode = request.GET.get("mode", "").strip()

    if search_query:
        profiles = profiles.filter(
            Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(subjects__icontains=search_query)
            | Q(interests__icontains=search_query)
            | Q(bio__icontains=search_query)
        )

    valid_modes = {
        value for value, label in StudyBuddyProfile.StudyMode.choices
    }

    if study_mode in valid_modes:
        profiles = profiles.filter(study_mode=study_mode)

    # Exclude students with whom the current user already
    # has an accepted partnership or pending request.
    unavailable_user_ids = StudyBuddyRequest.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status__in=[
            StudyBuddyRequest.Status.PENDING,
            StudyBuddyRequest.Status.ACCEPTED,
        ],
    ).values_list("from_user_id", "to_user_id")

    unavailable_ids = set()

    for from_id, to_id in unavailable_user_ids:
        unavailable_ids.add(
            to_id if from_id == request.user.id else from_id
        )

    profiles = profiles.exclude(user_id__in=unavailable_ids)

    return render(
        request,
        "community/study_buddies/discover.html",
        {
            "profiles": profiles,
            "search_query": search_query,
            "selected_mode": study_mode,
            "study_modes": StudyBuddyProfile.StudyMode.choices,
            "nav_active": "study_buddies",
        },
    )


# ==========================================================
# MY STUDY BUDDY PROFILE
# ==========================================================

@login_required
def study_buddy_profile(request):
    """
    Creates or updates the current student's Study Buddy profile.
    """

    if not is_student(request.user):
        return redirect("/")

    profile, created = StudyBuddyProfile.objects.get_or_create(
        user=request.user,
    )

    if request.method == "POST":
        form = StudyBuddyProfileForm(
            request.POST,
            instance=profile,
        )

        if form.is_valid():
            buddy_profile = form.save(commit=False)
            buddy_profile.user = request.user
            buddy_profile.save()

            messages.success(
                request,
                "Your Study Buddy profile has been updated.",
            )

            return redirect("community:study_buddy_profile")

    else:
        form = StudyBuddyProfileForm(instance=profile)

    return render(
        request,
        "community/study_buddies/profile.html",
        {
            "form": form,
            "profile": profile,
            "nav_active": "study_buddies",
        },
    )


# ==========================================================
# SEND STUDY BUDDY REQUEST
# ==========================================================

@login_required
@require_POST
def send_study_buddy_request(request, user_id):
    """
    Sends a study partnership request to another discoverable
    student.

    Previous declined or cancelled requests can be sent again.
    """

    if not is_student(request.user):
        return redirect("/")

    if user_id == request.user.id:
        messages.error(
            request,
            "You cannot send a study request to yourself.",
        )
        return redirect("community:study_buddy_discover")

    # Require the sender to create a Study Buddy profile first.
    if not StudyBuddyProfile.objects.filter(
        user=request.user,
        is_discoverable=True,
    ).exists():
        messages.warning(
            request,
            "Create and enable your Study Buddy profile before sending requests.",
        )
        return redirect("community:study_buddy_profile")

    recipient_profile = get_object_or_404(
        StudyBuddyProfile.objects.select_related("user"),
        user_id=user_id,
        user__role="student",
        is_discoverable=True,
    )

    recipient = recipient_profile.user

    form = StudyBuddyRequestForm(request.POST)

    if not form.is_valid():
        messages.error(
            request,
            "Please check your introduction message and try again.",
        )
        return redirect("community:study_buddy_discover")

    try:
        with transaction.atomic():

            # Lock any active request between these two students.
            existing_active_request = (
                StudyBuddyRequest.objects
                .select_for_update()
                .filter(
                    Q(
                        from_user=request.user,
                        to_user=recipient,
                    )
                    | Q(
                        from_user=recipient,
                        to_user=request.user,
                    ),
                    status__in=[
                        StudyBuddyRequest.Status.PENDING,
                        StudyBuddyRequest.Status.ACCEPTED,
                    ],
                )
                .first()
            )

            if existing_active_request:
                messages.info(
                    request,
                    "A pending request or accepted partnership already exists between you.",
                )
                return redirect("community:study_buddy_discover")

            # Reuse an earlier request in the same direction
            # instead of violating the unique database constraint.
            buddy_request = (
                StudyBuddyRequest.objects
                .filter(
                    from_user=request.user,
                    to_user=recipient,
                )
                .first()
            )

            if buddy_request:
                buddy_request.message = form.cleaned_data["message"]
                buddy_request.status = StudyBuddyRequest.Status.PENDING
                buddy_request.responded_at = None
                buddy_request.created_at = timezone.now()

                buddy_request.save(
                    update_fields=[
                        "message",
                        "status",
                        "responded_at",
                        "created_at",
                        "updated_at",
                    ]
                )

            else:
                buddy_request = StudyBuddyRequest.objects.create(
                    from_user=request.user,
                    to_user=recipient,
                    message=form.cleaned_data["message"],
                )

        messages.success(
            request,
            "Your Study Buddy request has been sent.",
        )

    except ValidationError as error:
        for error_message in error.messages:
            messages.error(request, error_message)

    return redirect("community:study_buddy_discover")


# ==========================================================
# STUDY BUDDY REQUESTS
# ==========================================================

@login_required
def study_buddy_requests(request):
    """
    Displays received and sent Study Buddy requests.
    """

    if not is_student(request.user):
        return redirect("/")

    received_requests = (
        StudyBuddyRequest.objects
        .filter(
            to_user=request.user,
            status=StudyBuddyRequest.Status.PENDING,
        )
        .select_related("from_user")
        .order_by("-created_at")
    )

    sent_requests = (
        StudyBuddyRequest.objects
        .filter(
            from_user=request.user,
            status=StudyBuddyRequest.Status.PENDING,
        )
        .select_related("to_user")
        .order_by("-created_at")
    )

    return render(
        request,
        "community/study_buddies/requests.html",
        {
            "received_requests": received_requests,
            "sent_requests": sent_requests,
            "received_count": received_requests.count(),
            "sent_count": sent_requests.count(),
            "nav_active": "study_buddies",
        },
    )


# ==========================================================
# MANAGE STUDY BUDDY REQUEST
# ==========================================================

@login_required
@require_POST
def manage_study_buddy_request(request, request_id, action):
    """
    Allows:
    - Recipient to accept or decline.
    - Sender to cancel a pending request.
    """

    if not is_student(request.user):
        return redirect("/")

    with transaction.atomic():
        buddy_request = get_object_or_404(
            StudyBuddyRequest.objects.select_for_update(),
            pk=request_id,
        )

        if buddy_request.status != StudyBuddyRequest.Status.PENDING:
            messages.warning(
                request,
                "This request is no longer pending.",
            )
            return redirect("community:study_buddy_requests")

        # Only the recipient can accept or decline.
        if action in ["accept", "decline"]:

            if buddy_request.to_user_id != request.user.id:
                messages.error(
                    request,
                    "You are not authorized to respond to this request.",
                )
                return redirect("community:study_buddy_requests")

            if action == "accept":

                # Prevent an accepted partnership in the reverse
                # direction from creating a duplicate partnership.
                reverse_accepted = StudyBuddyRequest.objects.filter(
                    from_user=request.user,
                    to_user=buddy_request.from_user,
                    status=StudyBuddyRequest.Status.ACCEPTED,
                ).exclude(pk=buddy_request.pk).exists()

                if reverse_accepted:
                    messages.warning(
                        request,
                        "An accepted study partnership already exists.",
                    )
                    return redirect("community:study_buddy_requests")

                buddy_request.status = StudyBuddyRequest.Status.ACCEPTED
                buddy_request.save(
                    update_fields=["status", "responded_at", "updated_at"]
                )

                messages.success(
                    request,
                    "Study Buddy request accepted. You are now study partners.",
                )

            elif action == "decline":

                buddy_request.status = StudyBuddyRequest.Status.DECLINED
                buddy_request.save(
                    update_fields=["status", "responded_at", "updated_at"]
                )

                messages.success(
                    request,
                    "Study Buddy request declined.",
                )

        # Only the sender can cancel a pending request.
        elif action == "cancel":

            if buddy_request.from_user_id != request.user.id:
                messages.error(
                    request,
                    "Only the sender can cancel this request.",
                )
                return redirect("community:study_buddy_requests")

            buddy_request.status = StudyBuddyRequest.Status.CANCELLED
            buddy_request.save(
                update_fields=["status", "responded_at", "updated_at"]
            )

            messages.success(
                request,
                "Study Buddy request cancelled.",
            )

        else:
            messages.error(
                request,
                "Invalid Study Buddy request action.",
            )

    return redirect("community:study_buddy_requests")


# ==========================================================
# MY STUDY PARTNERS
# ==========================================================

@login_required
def study_buddy_partners(request):
    """
    Displays all accepted Study Buddy partnerships.
    """

    if not is_student(request.user):
        return redirect("/")

    partnerships = (
        StudyBuddyRequest.objects
        .filter(
            Q(from_user=request.user) | Q(to_user=request.user),
            status=StudyBuddyRequest.Status.ACCEPTED,
        )
        .select_related("from_user", "to_user")
        .order_by("-responded_at")
    )

    partners = []

    for partnership in partnerships:
        partner = (
            partnership.to_user
            if partnership.from_user_id == request.user.id
            else partnership.from_user
        )

        profile = StudyBuddyProfile.objects.filter(
            user=partner,
        ).first()

        partners.append({
            "user": partner,
            "profile": profile,
            "partnership": partnership,
        })

    return render(
        request,
        "community/study_buddies/partners.html",
        {
            "partners": partners,
            "partners_count": len(partners),
            "nav_active": "study_buddies",
        },
    )


# ==========================================================
# PRIVATE STUDENT MESSAGING
# ==========================================================

@login_required
def private_message_inbox(request):
    if not is_student(request.user):
        messages.error(request, "Only students can access private messages.")
        return redirect("community:dashboard")

    conversations = (
        PrivateConversation.objects
        .filter(
            Q(buddy_request__from_user=request.user)
            | Q(buddy_request__to_user=request.user),
            buddy_request__status=StudyBuddyRequest.Status.ACCEPTED,
        )
        .select_related(
            "buddy_request",
            "buddy_request__from_user",
            "buddy_request__to_user",
        )
        .prefetch_related("messages")
        .order_by("-last_message_at", "-created_at")
    )

    conversation_items = []

    for conversation in conversations:
        other_user = conversation.other_participant(request.user)

        if not other_user:
            continue

        last_message = conversation.messages.order_by(
            "-created_at"
        ).first()

        unread_count = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()

        conversation_items.append({
            "conversation": conversation,
            "other_user": other_user,
            "last_message": last_message,
            "unread_count": unread_count,
        })

    return render(
        request,
        "community/messaging/inbox.html",
        {
            "conversation_items": conversation_items,
            "nav_active": "messages",
        },
    )


@login_required
@require_POST
def start_private_conversation(request, request_id):
    if not is_student(request.user):
        messages.error(request, "Only students can start private conversations.")
        return redirect("community:dashboard")

    buddy_request = get_object_or_404(
        StudyBuddyRequest,
        Q(from_user=request.user) | Q(to_user=request.user),
        pk=request_id,
        status=StudyBuddyRequest.Status.ACCEPTED,
    )

    try:
        conversation, created = PrivateConversation.objects.get_or_create(
            buddy_request=buddy_request,
        )

        if created:
            conversation.full_clean()

    except ValidationError:
        messages.error(
            request,
            "This private conversation could not be created.",
        )
        return redirect("community:study_buddy_partners")

    return redirect(
        "community:private_conversation_detail",
        conversation_id=conversation.pk,
    )


@login_required
def private_conversation_detail(request, conversation_id):
    if not is_student(request.user):
        messages.error(request, "Only students can access private messages.")
        return redirect("community:dashboard")

    conversation = get_object_or_404(
        PrivateConversation.objects.select_related(
            "buddy_request",
            "buddy_request__from_user",
            "buddy_request__to_user",
        ),
        Q(buddy_request__from_user=request.user)
        | Q(buddy_request__to_user=request.user),
        pk=conversation_id,
        buddy_request__status=StudyBuddyRequest.Status.ACCEPTED,
    )

    other_user = conversation.other_participant(request.user)

    if not other_user:
        messages.error(request, "You cannot access this conversation.")
        return redirect("community:private_message_inbox")

    # Mark messages from the other participant as read.
    PrivateMessage.objects.filter(
        conversation=conversation,
        is_read=False,
    ).exclude(
        sender=request.user,
    ).update(
        is_read=True,
        read_at=timezone.now(),
    )

    chat_messages = conversation.messages.select_related(
        "sender"
    ).all()

    return render(
        request,
        "community/messaging/conversation.html",
        {
            "conversation": conversation,
            "other_user": other_user,
            "chat_messages": chat_messages,
            "nav_active": "messages",
        },
    )


@login_required
@require_POST
def send_private_message(request, conversation_id):
    if not is_student(request.user):
        messages.error(request, "Only students can send private messages.")
        return redirect("community:dashboard")

    conversation = get_object_or_404(
        PrivateConversation.objects.select_related("buddy_request"),
        Q(buddy_request__from_user=request.user)
        | Q(buddy_request__to_user=request.user),
        pk=conversation_id,
        buddy_request__status=StudyBuddyRequest.Status.ACCEPTED,
    )

    content = request.POST.get("content", "").strip()

    if not content:
        messages.error(request, "Message cannot be empty.")

    elif len(content) > 5000:
        messages.error(request, "Message cannot exceed 5000 characters.")

    else:
        try:
            PrivateMessage.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
            )
            messages.success(request, "Message sent.")

        except ValidationError as error:
            messages.error(request, "; ".join(error.messages))

    return redirect(
        "community:private_conversation_detail",
        conversation_id=conversation.pk,
    )
