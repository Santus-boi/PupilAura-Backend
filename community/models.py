
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify


class CommunityGroup(models.Model):

    class GroupType(models.TextChoices):
        SCHOOL = "school", "School Group"
        EXAM = "exam", "Exam Prep Group"
        TECH = "tech", "Tech Academy Group"
        INTEREST = "interest", "General Interest Group"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True)
    description = models.TextField()

    group_type = models.CharField(
        max_length=20,
        choices=GroupType.choices,
    )

    school_class = models.ForeignKey(
        "learning.SchoolClass",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_groups",
    )

    exam = models.ForeignKey(
        "exam_prep.Exam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_groups",
    )

    exam_subject = models.ForeignKey(
        "exam_prep.ExamSubject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_groups",
    )

    tech_course = models.ForeignKey(
        "tech.TechCourse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_groups",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_groups_created",
    )

    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_groups_reviewed",
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Community Group"
        verbose_name_plural = "Community Groups"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "community-group"
            slug = base_slug
            counter = 1

            while CommunityGroup.objects.filter(
                slug=slug
            ).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"

            self.slug = slug

        super().save(*args, **kwargs)

    def clean(self):
        errors = {}

        if self.group_type == self.GroupType.SCHOOL:
            if not self.school_class_id:
                errors["school_class"] = (
                    "A school group must be linked to a school class."
                )

            if self.exam_id or self.exam_subject_id or self.tech_course_id:
                errors["group_type"] = (
                    "A school group cannot have Exam Prep or Tech Academy context."
                )

        elif self.group_type == self.GroupType.EXAM:
            if not self.exam_id:
                errors["exam"] = (
                    "An Exam Prep group must be linked to an exam."
                )

            if self.school_class_id or self.tech_course_id:
                errors["group_type"] = (
                    "An Exam Prep group cannot have school or Tech Academy context."
                )

            if (
                self.exam_subject_id
                and self.exam_id
                and self.exam_subject.exam_id != self.exam_id
            ):
                errors["exam_subject"] = (
                    "The selected subject must belong to the selected exam."
                )

        elif self.group_type == self.GroupType.TECH:
            if not self.tech_course_id:
                errors["tech_course"] = (
                    "A Tech Academy group must be linked to a Tech course."
                )

            if self.school_class_id or self.exam_id or self.exam_subject_id:
                errors["group_type"] = (
                    "A Tech Academy group cannot have school or Exam Prep context."
                )

        elif self.group_type == self.GroupType.INTEREST:
            if (
                self.school_class_id
                or self.exam_id
                or self.exam_subject_id
                or self.tech_course_id
            ):
                errors["group_type"] = (
                    "A general interest group cannot have a learning context."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name


class GroupMembership(models.Model):

    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        CARETAKER = "caretaker", "Caretaker"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        REJECTED = "rejected", "Rejected"
        BANNED = "banned", "Banned"

    group = models.ForeignKey(
        CommunityGroup,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_memberships_reviewed",
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)

    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-joined_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"],
                name="unique_community_group_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.group} ({self.status})"


class GroupPost(models.Model):

    group = models.ForeignKey(
        CommunityGroup,
        on_delete=models.CASCADE,
        related_name="posts",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["group", "-created_at"]),
        ]

    def __str__(self):
        return f"Post by {self.author} in {self.group}"


class GroupComment(models.Model):

    post = models.ForeignKey(
        GroupPost,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_comments",
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"


# ==========================================================
# COMMUNITY GROUP CHAT
# ==========================================================

class ChatMessage(models.Model):
    """
    Stores individual messages in a Community group conversation.

    Designed to support future real-time messaging with
    Django Channels and WebSockets.
    """

    group = models.ForeignKey(
        CommunityGroup,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_chat_messages",
    )

    content = models.TextField()

    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
    )

    is_edited = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["group", "created_at"],
                name="community_chat_group_time_idx",
            ),
            models.Index(
                fields=["sender", "created_at"],
                name="community_chat_sender_time_idx",
            ),
        ]

    def clean(self):
        if self.reply_to_id and self.group_id:
            if self.reply_to.group_id != self.group_id:
                raise ValidationError({
                    "reply_to": (
                        "You can only reply to a message in the same group."
                    )
                })

        if self.pk and self.reply_to_id == self.pk:
            raise ValidationError({
                "reply_to": "A message cannot reply to itself."
            })

    def __str__(self):
        return f"Message by {self.sender} in {self.group}"


class ChatMessageReaction(models.Model):
    """
    Stores emoji reactions added to individual chat messages.
    """

    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="reactions",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_chat_reactions",
    )

    emoji = models.CharField(max_length=16)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user", "emoji"],
                name="unique_chat_message_user_emoji",
            )
        ]
        indexes = [
            models.Index(
                fields=["message", "created_at"],
                name="community_chat_reaction_idx",
            ),
        ]

    def __str__(self):
        return f"{self.emoji} by {self.user} on message {self.message_id}"


# ==========================================================
# STUDY BUDDY PROFILES
# ==========================================================

class StudyBuddyProfile(models.Model):
    """
    A student's discoverable study-partner profile.

    Students control whether their profile appears in
    Study Buddy searches.
    """

    class StudyMode(models.TextChoices):
        ONLINE = "online", "Online"
        IN_PERSON = "in_person", "In Person"
        EITHER = "either", "Either"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_buddy_profile",
    )

    bio = models.TextField(
        blank=True,
        max_length=1000,
        help_text="Briefly introduce yourself and your learning goals.",
    )

    subjects = models.TextField(
        blank=True,
        help_text="Subjects you want to study, separated by commas.",
    )

    interests = models.TextField(
        blank=True,
        help_text="Your academic or learning interests.",
    )

    availability = models.CharField(
        max_length=255,
        blank=True,
        help_text="For example: Weekdays evenings or weekends.",
    )

    study_mode = models.CharField(
        max_length=20,
        choices=StudyMode.choices,
        default=StudyMode.EITHER,
    )

    is_discoverable = models.BooleanField(
        default=True,
        help_text="Allow other students to find your study profile.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Study Buddy Profile"
        verbose_name_plural = "Study Buddy Profiles"

    def __str__(self):
        return f"Study profile: {self.user}"


# ==========================================================
# STUDY BUDDY REQUESTS
# ==========================================================

class StudyBuddyRequest(models.Model):
    """
    Manages requests between students who want to study together.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_buddy_requests_sent",
    )

    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_buddy_requests_received",
    )

    message = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional introduction message.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"],
                name="unique_study_buddy_request_direction",
            )
        ]
        indexes = [
            models.Index(
                fields=["to_user", "status", "-created_at"],
                name="study_buddy_received_idx",
            ),
            models.Index(
                fields=["from_user", "status", "-created_at"],
                name="study_buddy_sent_idx",
            ),
        ]

    def clean(self):
        errors = {}

        if self.from_user_id and self.to_user_id:
            if self.from_user_id == self.to_user_id:
                errors["to_user"] = (
                    "You cannot send a study request to yourself."
                )

            if self.status in [
                self.Status.PENDING,
                self.Status.ACCEPTED,
            ]:
                existing_request = StudyBuddyRequest.objects.filter(
                    Q(
                        from_user_id=self.from_user_id,
                        to_user_id=self.to_user_id,
                    )
                    | Q(
                        from_user_id=self.to_user_id,
                        to_user_id=self.from_user_id,
                    ),
                    status__in=[
                        self.Status.PENDING,
                        self.Status.ACCEPTED,
                    ],
                ).exclude(pk=self.pk)

                if existing_request.exists():
                    errors["to_user"] = (
                        "An active or accepted study buddy request "
                        "already exists between these students."
                    )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.status in [
            self.Status.ACCEPTED,
            self.Status.DECLINED,
            self.Status.CANCELLED,
        ] and not self.responded_at:
            self.responded_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.from_user} → {self.to_user} "
            f"({self.status})"
        )


# ==========================================================
# PRIVATE STUDENT CONVERSATIONS
# ==========================================================

class PrivateConversation(models.Model):
    """
    A private one-to-one conversation between students
    with an accepted Study Buddy request.
    """

    buddy_request = models.OneToOneField(
        StudyBuddyRequest,
        on_delete=models.PROTECT,
        related_name="private_conversation",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-last_message_at", "-created_at"]
        verbose_name = "Private Conversation"
        verbose_name_plural = "Private Conversations"

    def clean(self):
        if self.buddy_request_id:
            if self.buddy_request.status != StudyBuddyRequest.Status.ACCEPTED:
                raise ValidationError({
                    "buddy_request": (
                        "A private conversation requires an accepted "
                        "Study Buddy request."
                    )
                })

    def includes_user(self, user):
        return (
            user.pk in [
                self.buddy_request.from_user_id,
                self.buddy_request.to_user_id,
            ]
        )

    def other_participant(self, user):
        if user.pk == self.buddy_request.from_user_id:
            return self.buddy_request.to_user

        if user.pk == self.buddy_request.to_user_id:
            return self.buddy_request.from_user

        return None

    def __str__(self):
        return (
            f"Private conversation: "
            f"{self.buddy_request.from_user} and "
            f"{self.buddy_request.to_user}"
        )


# ==========================================================
# PRIVATE MESSAGES
# ==========================================================

class PrivateMessage(models.Model):
    """
    Individual messages exchanged inside a private conversation.
    """

    conversation = models.ForeignKey(
        PrivateConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_private_messages_sent",
    )

    content = models.TextField()

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    is_edited = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["conversation", "created_at"],
                name="private_msg_conversation_idx",
            ),
            models.Index(
                fields=["sender", "created_at"],
                name="private_msg_sender_time_idx",
            ),
            models.Index(
                fields=["conversation", "is_read"],
                name="private_msg_read_idx",
            ),
        ]

    def clean(self):
        errors = {}

        if self.conversation_id and self.sender_id:
            conversation = self.conversation
            request = conversation.buddy_request

            if self.sender_id not in [
                request.from_user_id,
                request.to_user_id,
            ]:
                errors["sender"] = (
                    "You are not a participant in this conversation."
                )

            if request.status != StudyBuddyRequest.Status.ACCEPTED:
                errors["conversation"] = (
                    "Messages can only be sent within an accepted "
                    "Study Buddy relationship."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        PrivateConversation.objects.filter(
            pk=self.conversation_id
        ).update(
            last_message_at=self.created_at,
            updated_at=timezone.now(),
        )

    def __str__(self):
        return (
            f"Private message by {self.sender} "
            f"in conversation {self.conversation_id}"
        )
