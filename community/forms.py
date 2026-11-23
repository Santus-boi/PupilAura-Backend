
from django import forms
from django.utils.text import slugify

from .models import (
    CommunityGroup,
    GroupPost,
    GroupComment,
    StudyBuddyProfile,
    StudyBuddyRequest,
)

from learning.models import SchoolClass
from exam_prep.models import Exam, ExamSubject
from tech.models import TechCourse, TechEnrollment


# ==========================================================
# COMMUNITY GROUP FORM
# ==========================================================

class CommunityGroupForm(forms.ModelForm):

    class Meta:
        model = CommunityGroup
        fields = [
            "name",
            "description",
            "group_type",
            "school_class",
            "exam",
            "exam_subject",
            "tech_course",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter a group name",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "What is this group about?",
            }),
            "group_type": forms.Select(attrs={
                "class": "form-select",
                "id": "id_group_type",
            }),
            "school_class": forms.Select(attrs={
                "class": "form-select",
                "data-community-context": "school",
            }),
            "exam": forms.Select(attrs={
                "class": "form-select",
                "data-community-context": "exam",
            }),
            "exam_subject": forms.Select(attrs={
                "class": "form-select",
                "data-community-context": "exam",
            }),
            "tech_course": forms.Select(attrs={
                "class": "form-select",
                "data-community-context": "tech",
            }),
        }

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.student = student

        self.fields["school_class"].queryset = SchoolClass.objects.none()
        self.fields["tech_course"].queryset = TechCourse.objects.none()

        self.fields["exam"].queryset = Exam.objects.filter(
            published=True
        ).order_by("order", "name")

        self.fields["exam_subject"].queryset = ExamSubject.objects.none()

        profile = None

        if student:
            profile = getattr(student, "student_profile", None)

        if profile and profile.school_class_id:
            self.fields["school_class"].queryset = SchoolClass.objects.filter(
                pk=profile.school_class_id
            )

        if student:
            enrolled_course_ids = TechEnrollment.objects.filter(
                student=student,
                course__published=True,
            ).values_list("course_id", flat=True)

            self.fields["tech_course"].queryset = TechCourse.objects.filter(
                pk__in=enrolled_course_ids,
                published=True,
            ).order_by("title")

        available_types = [
            CommunityGroup.GroupType.EXAM,
            CommunityGroup.GroupType.INTEREST,
        ]

        if self.fields["school_class"].queryset.exists():
            available_types.append(CommunityGroup.GroupType.SCHOOL)

        if self.fields["tech_course"].queryset.exists():
            available_types.append(CommunityGroup.GroupType.TECH)

        self.fields["group_type"].choices = [
            (value, label)
            for value, label in CommunityGroup.GroupType.choices
            if value in available_types
        ]

        if self.is_bound:
            exam_id = self.data.get(self.add_prefix("exam"))

            if exam_id:
                self.fields["exam_subject"].queryset = (
                    ExamSubject.objects.filter(
                        exam_id=exam_id,
                        published=True,
                    ).order_by("order", "name")
                )

        elif self.instance and self.instance.pk and self.instance.exam_id:
            self.fields["exam_subject"].queryset = (
                ExamSubject.objects.filter(
                    exam=self.instance.exam,
                    published=True,
                ).order_by("order", "name")
            )

    def clean(self):
        cleaned_data = super().clean()

        group_type = cleaned_data.get("group_type")

        if group_type == CommunityGroup.GroupType.SCHOOL:
            cleaned_data["exam"] = None
            cleaned_data["exam_subject"] = None
            cleaned_data["tech_course"] = None

        elif group_type == CommunityGroup.GroupType.EXAM:
            cleaned_data["school_class"] = None
            cleaned_data["tech_course"] = None

        elif group_type == CommunityGroup.GroupType.TECH:
            cleaned_data["school_class"] = None
            cleaned_data["exam"] = None
            cleaned_data["exam_subject"] = None

        elif group_type == CommunityGroup.GroupType.INTEREST:
            cleaned_data["school_class"] = None
            cleaned_data["exam"] = None
            cleaned_data["exam_subject"] = None
            cleaned_data["tech_course"] = None

        school_class = cleaned_data.get("school_class")
        exam = cleaned_data.get("exam")
        exam_subject = cleaned_data.get("exam_subject")
        tech_course = cleaned_data.get("tech_course")

        if group_type == CommunityGroup.GroupType.SCHOOL:
            if not school_class:
                self.add_error(
                    "school_class",
                    "You must have an assigned school class to create this group."
                )
            elif not self.fields["school_class"].queryset.filter(
                pk=school_class.pk
            ).exists():
                self.add_error(
                    "school_class",
                    "You can only create a group for your assigned class."
                )

        elif group_type == CommunityGroup.GroupType.TECH:
            if not tech_course:
                self.add_error(
                    "tech_course",
                    "You must select a Tech course you are enrolled in."
                )
            elif not self.fields["tech_course"].queryset.filter(
                pk=tech_course.pk
            ).exists():
                self.add_error(
                    "tech_course",
                    "You can only create a group for a course you are enrolled in."
                )

        elif group_type == CommunityGroup.GroupType.EXAM:
            if not exam:
                self.add_error("exam", "Please select an exam.")

            if exam_subject and exam and exam_subject.exam_id != exam.pk:
                self.add_error(
                    "exam_subject",
                    "Select a subject belonging to the chosen exam."
                )

        name = cleaned_data.get("name")

        if name:
            base_slug = slugify(name) or "community-group"
            slug = base_slug
            counter = 1

            queryset = CommunityGroup.objects.all()

            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            while queryset.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.instance.slug = slug

        return cleaned_data


# ==========================================================
# GROUP POST FORM
# ==========================================================

class GroupPostForm(forms.ModelForm):

    class Meta:
        model = GroupPost
        fields = ["content"]

        widgets = {
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Share something with your group...",
            }),
        }


# ==========================================================
# GROUP COMMENT FORM
# ==========================================================

class GroupCommentForm(forms.ModelForm):

    class Meta:
        model = GroupComment
        fields = ["content"]

        widgets = {
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Write a comment...",
            }),
        }


# ==========================================================
# STUDY BUDDY PROFILE FORM
# ==========================================================

class StudyBuddyProfileForm(forms.ModelForm):

    class Meta:
        model = StudyBuddyProfile
        fields = [
            "bio",
            "subjects",
            "interests",
            "availability",
            "study_mode",
            "is_discoverable",
        ]

        widgets = {
            "bio": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "maxlength": 1000,
                "placeholder": (
                    "Introduce yourself and describe your learning goals..."
                ),
            }),
            "subjects": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": (
                    "e.g. Mathematics, English, Physics, Biology"
                ),
            }),
            "interests": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": (
                    "e.g. Programming, Science, Business, Reading"
                ),
            }),
            "availability": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": (
                    "e.g. Weekday evenings, Saturday mornings"
                ),
            }),
            "study_mode": forms.Select(attrs={
                "class": "form-select",
            }),
            "is_discoverable": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_subjects(self):
        subjects = self.cleaned_data.get("subjects", "").strip()

        if len(subjects) > 1000:
            raise forms.ValidationError(
                "Your subjects list cannot exceed 1000 characters."
            )

        return subjects

    def clean_interests(self):
        interests = self.cleaned_data.get("interests", "").strip()

        if len(interests) > 1000:
            raise forms.ValidationError(
                "Your interests cannot exceed 1000 characters."
            )

        return interests


# ==========================================================
# STUDY BUDDY REQUEST FORM
# ==========================================================

class StudyBuddyRequestForm(forms.ModelForm):

    class Meta:
        model = StudyBuddyRequest
        fields = ["message"]

        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "maxlength": 500,
                "placeholder": (
                    "Introduce yourself and explain why you would "
                    "like to study together..."
                ),
            }),
        }


from django import forms
from .models import PrivateMessage


class PrivateMessageForm(forms.ModelForm):
    class Meta:
        model = PrivateMessage
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Write your message...",
                "rows": 2,
                "maxlength": 5000,
            }),
        }

    def clean_content(self):
        content = self.cleaned_data["content"].strip()

        if not content:
            raise forms.ValidationError("Message cannot be empty.")

        if len(content) > 5000:
            raise forms.ValidationError(
                "Message cannot exceed 5000 characters."
            )

        return content
