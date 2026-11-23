
from django import forms

from tech.models import (
    TechCategory,
    TechCourse,
    TechModule,
    TechLesson,
    TechLessonVideo,
    TechLessonImage,
    TechLessonResource,
)

from exam_prep.models import (
    Exam,
    ExamSubject,
    ExamYear,
    ExamResource,
    ExamQuestion,
    ExamChoice,
)

from learning.models import (
    Course,
    EducationLevel,
    Lesson,
    LessonImage,
    LessonResource,
    CurriculumMaterial,
    LessonVideo,
    SchoolClass,
    Subject,
    Term,
    Week,
)

from play_learn.models import (
    PlayGame,
    Story,
    StoryChapter,
)


# =============================================================
# TECH CATEGORY
# =============================================================

class TechCategoryForm(forms.ModelForm):
    class Meta:
        model = TechCategory
        fields = ["name", "description", "order", "published"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter tech category name",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Describe this tech category...",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


class TechCourseForm(forms.ModelForm):
    class Meta:
        model = TechCourse
        fields = [
            "category",
            "title",
            "description",
            "thumbnail",
            "price",
            "published",
        ]
        widgets = {
            "category": forms.Select(attrs={
                "class": "form-select",
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter course title",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Describe what students will learn in this course",
                "rows": 6,
            }),
            "thumbnail": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank if free",
                "min": "0",
                "step": "0.01",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].required = False

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price


class TechModuleForm(forms.ModelForm):
    class Meta:
        model = TechModule
        fields = [
            "course",
            "title",
            "description",
            "price",
            "order",
            "published",
        ]
        widgets = {
            "course": forms.Select(attrs={
                "class": "form-select",
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter module title",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Describe what students will learn in this module",
                "rows": 5,
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank if free",
                "min": "0",
                "step": "0.01",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].required = False

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price


class TechLessonForm(forms.ModelForm):
    class Meta:
        model = TechLesson
        fields = [
            "module",
            "title",
            "description",
            "content",
            "practical",
            "project",
            "price",
            "order",
            "published",
        ]
        widgets = {
            "module": forms.Select(attrs={
                "class": "form-select",
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter lesson title",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Briefly describe this lesson",
                "rows": 4,
            }),
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter the lesson content",
                "rows": 10,
            }),
            "practical": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter practical exercises or activities",
                "rows": 8,
            }),
            "project": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Describe the project for this lesson",
                "rows": 8,
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank if free",
                "min": "0",
                "step": "0.01",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].required = False

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price


# =============================================================
# TECH LESSON VIDEO
# =============================================================

class TechLessonVideoForm(forms.ModelForm):
    class Meta:
        model = TechLessonVideo
        fields = [
            "title",
            "video_url",
            "description",
            "order",
            "published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter video title",
            }),
            "video_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://...",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe this video...",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


class TechLessonImageForm(forms.ModelForm):
    class Meta:
        model = TechLessonImage
        fields = [
            "title",
            "image",
            "caption",
            "order",
            "published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter image title",
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "caption": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Describe this image",
                "rows": 4,
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


# =============================================================
# TECH LESSON RESOURCE
# =============================================================

class TechLessonResourceForm(forms.ModelForm):
    class Meta:
        model = TechLessonResource
        fields = [
            "title",
            "file",
            "description",
            "price",
            "order",
            "published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter resource title",
            }),
            "file": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Describe this resource",
                "rows": 4,
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank if free",
                "min": "0",
                "step": "0.01",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].required = False

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price


# =============================================================
# EDUCATION LEVEL
# =============================================================

class EducationLevelForm(forms.ModelForm):
    class Meta:
        model = EducationLevel
        fields = ["name", "level_type", "order"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter education level name",
            }),
            "level_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
        }


# =============================================================
# SCHOOL CLASS
# =============================================================

class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = [
            "name",
            "education_level",
            "order",
            "price",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter class name",
            }),
            "education_level": forms.Select(attrs={
                "class": "form-select",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank if free",
                "min": "0",
                "step": "0.01",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["education_level"].queryset = (
            EducationLevel.objects.order_by("order", "name")
        )
        self.fields["price"].required = False

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price


# =============================================================
# SUBJECT
# =============================================================

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "school_class", "price"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter subject name",
            }),
            "school_class": forms.Select(attrs={
                "class": "form-select",
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank if free",
                "min": "0",
                "step": "0.01",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["school_class"].queryset = (
            SchoolClass.objects.select_related("education_level").order_by(
                "education_level__order",
                "order",
                "name",
            )
        )
        self.fields["school_class"].label_from_instance = (
            lambda obj: f"{obj.education_level.name} - {obj.name}"
        )
        self.fields["price"].required = False

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price


# =============================================================
# TERM
# =============================================================

class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ["name", "term_type", "subject", "order"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter term name",
            }),
            "term_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "subject": forms.Select(attrs={
                "class": "form-select",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = (
            Subject.objects.select_related(
                "school_class",
                "school_class__education_level",
            ).order_by(
                "school_class__education_level__order",
                "school_class__order",
                "name",
            )
        )
        self.fields["subject"].label_from_instance = lambda obj: (
            f"{obj.school_class.education_level.name} - "
            f"{obj.school_class.name} - {obj.name}"
            if obj.school_class else obj.name
        )


# =============================================================
# WEEK
# =============================================================

class WeekForm(forms.ModelForm):
    class Meta:
        model = Week
        fields = [
            "term",
            "number",
            "title",
            "overview",
            "activities",
        ]
        widgets = {
            "term": forms.Select(attrs={
                "class": "form-select",
            }),
            "number": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Optional week title",
            }),
            "overview": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Enter the general overview for this week...",
            }),
            "activities": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Enter activities for this week...",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["term"].queryset = (
            Term.objects.select_related(
                "subject",
                "subject__school_class",
                "subject__school_class__education_level",
            ).order_by(
                "subject__school_class__education_level__order",
                "subject__school_class__order",
                "subject__name",
                "order",
            )
        )
        self.fields["term"].label_from_instance = lambda obj: (
            f"{obj.subject.school_class.education_level.name} - "
            f"{obj.subject.school_class.name} - "
            f"{obj.subject.name} - {obj.name}"
            if obj.subject.school_class
            else f"{obj.subject.name} - {obj.name}"
        )


# =============================================================
# LESSON
# =============================================================

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "week",
            "title",
            "description",
            "objectives",
            "content",
            "examples",
            "key_points",
            "activity",
            "practical",
            "order",
            "published",
        ]
        widgets = {
            "week": forms.Select(attrs={
                "class": "form-select",
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter lesson title",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
            }),
            "objectives": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "What should students be able to do after this lesson?",
            }),
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 10,
                "placeholder": "Enter the main teaching content...",
            }),
            "examples": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
            }),
            "key_points": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
            }),
            "activity": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
            }),
            "practical": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["week"].queryset = (
            Week.objects.select_related(
                "term",
                "term__subject",
                "term__subject__school_class",
                "term__subject__school_class__education_level",
            ).order_by(
                "term__subject__school_class__education_level__order",
                "term__subject__school_class__order",
                "term__subject__name",
                "term__order",
                "number",
            )
        )
        self.fields["week"].label_from_instance = lambda obj: (
            f"{obj.term.subject.school_class.education_level.name} - "
            f"{obj.term.subject.school_class.name} - "
            f"{obj.term.subject.name} - "
            f"{obj.term.name} - Week {obj.number}"
            if obj.term.subject.school_class
            else f"{obj.term.subject.name} - "
            f"{obj.term.name} - Week {obj.number}"
        )


# =============================================================
# LESSON VIDEO
# =============================================================

class LessonVideoForm(forms.ModelForm):
    class Meta:
        model = LessonVideo
        fields = [
            "title",
            "video_url",
            "description",
            "order",
            "published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter video title",
            }),
            "video_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://...",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe this video...",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


# =============================================================
# LESSON IMAGE / DIAGRAM
# =============================================================

class LessonImageForm(forms.ModelForm):
    class Meta:
        model = LessonImage
        fields = [
            "title",
            "image",
            "caption",
            "order",
            "published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter image or diagram title",
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "caption": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional image caption...",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


# =============================================================
# LESSON RESOURCE
# =============================================================

class LessonResourceForm(forms.ModelForm):
    class Meta:
        model = LessonResource
        fields = [
            "title",
            "file",
            "resource_type",
            "description",
            "order",
            "published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter resource title",
            }),
            "file": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
            "resource_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe this resource...",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


# =============================================================
# INDEPENDENT COURSE
# =============================================================

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "category",
            "education_level",
            "subject",
            "thumbnail",
            "price",
            "published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter course title",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 7,
                "placeholder": "Describe the course...",
            }),
            "category": forms.Select(attrs={
                "class": "form-select",
            }),
            "education_level": forms.Select(attrs={
                "class": "form-select",
            }),
            "subject": forms.Select(attrs={
                "class": "form-select",
            }),
            "thumbnail": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "education_level" in self.fields:
            self.fields["education_level"].queryset = (
                EducationLevel.objects.order_by("order", "name")
            )

        if "subject" in self.fields:
            self.fields["subject"].queryset = (
                Subject.objects.select_related(
                    "school_class",
                    "school_class__education_level",
                ).order_by(
                    "school_class__education_level__order",
                    "school_class__order",
                    "name",
                )
            )
            self.fields["subject"].label_from_instance = lambda obj: (
                f"{obj.school_class.education_level.name} - "
                f"{obj.school_class.name} - {obj.name}"
                if obj.school_class
                else obj.name
            )


# =============================================================
# EXAM
# =============================================================

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            "name",
            "slug",
            "description",
            "price",
            "published",
            "order",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter examination name",
            }),
            "slug": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. waec, jamb, neco",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Describe this examination...",
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank if free",
                "min": "0",
                "step": "0.01",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].required = False

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price


class ExamSubjectForm(forms.ModelForm):
    class Meta:
        model = ExamSubject
        fields = [
            "exam",
            "name",
            "code",
            "price",
            "published",
            "order",
        ]
        widgets = {
            "exam": forms.Select(attrs={
                "class": "form-select",
            }),
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter subject name",
            }),
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. ENG, MATH, PHY",
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank if free",
                "min": "0",
                "step": "0.01",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].required = False

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price


# =============================================================
# EXAM YEAR
# =============================================================

class ExamYearForm(forms.ModelForm):
    class Meta:
        model = ExamYear
        fields = [
            "exam",
            "year",
            "published",
            "order",
        ]
        widgets = {
            "exam": forms.Select(attrs={
                "class": "form-select",
            }),
            "year": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1900",
                "max": "2100",
                "placeholder": "e.g. 2025",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
        }


# 
# =========================================================
# EXAM RESOURCE — COMMON INFORMATION
# =========================================================

class ExamResourceForm(forms.ModelForm):
    """
    Handles common information shared by every exam resource.

    Resource-specific content is handled separately by the
    dedicated resource content forms.
    """

    class Meta:
        model = ExamResource
        fields = [
            "exam",
            "subject",
            "year",
            "resource_type",
            "title",
            "description",
            "price",
            "content",
            "file",
            "video_url",
            "published",
            "order",
        ]
        widgets = {
            "exam": forms.Select(attrs={
                "class": "form-select",
            }),
            "subject": forms.Select(attrs={
                "class": "form-select",
            }),
            "year": forms.Select(attrs={
                "class": "form-select",
            }),
            "resource_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter resource title",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe this exam resource...",
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank if free",
                "min": "0",
                "step": "0.01",
            }),
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Optional general resource content...",
            }),
            "file": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
            "video_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://...",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["exam"].queryset = (
            Exam.objects.order_by("order", "name")
        )

        self.fields["subject"].queryset = (
            ExamSubject.objects.select_related("exam").order_by(
                "exam__order",
                "exam__name",
                "order",
                "name",
            )
        )

        self.fields["year"].queryset = (
            ExamYear.objects.select_related("exam").order_by("-year")
        )

        self.fields["price"].required = False

    def clean(self):
        cleaned_data = super().clean()

        exam = cleaned_data.get("exam")
        subject = cleaned_data.get("subject")
        year = cleaned_data.get("year")

        if exam and subject and subject.exam_id != exam.id:
            self.add_error(
                "subject",
                "Select a subject belonging to the chosen examination.",
            )

        if exam and year and year.exam_id != exam.id:
            self.add_error(
                "year",
                "Select a year belonging to the chosen examination.",
            )

        return cleaned_data

    def clean_price(self):
        price = self.cleaned_data.get("price")

        if price is not None and price < 0:
            raise forms.ValidationError(
                "Price cannot be negative."
            )

        return price


# =============================================================
# EXAM RESOURCE — LESSON CONTENT
# =============================================================

class ExamLessonContentForm(forms.Form):
    """
    Content fields for an Exam Lesson resource.

    These fields are saved into ExamResource.structured_content
    by the corresponding resource views.

    The field name 'content' intentionally matches the
    student-facing lesson content structure.
    """

    objectives = forms.CharField(
        required=False,
        label="Learning Objectives",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 5,
            "placeholder": "What should students learn from this lesson?",
        }),
    )

    definitions = forms.CharField(
        required=False,
        label="Important Definitions",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 5,
            "placeholder": "Enter important terms and their meanings...",
        }),
    )

    content = forms.CharField(
        required=False,
        label="Lesson Content",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 12,
            "placeholder": "Write the complete lesson...",
        }),
    )

    examples = forms.CharField(
        required=False,
        label="Examples",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 7,
            "placeholder": "Provide worked examples...",
        }),
    )

    key_points = forms.CharField(
        required=False,
        label="Key Points",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 6,
            "placeholder": "List the important points students should remember...",
        }),
    )

    activity = forms.CharField(
        required=False,
        label="Student Activities",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 6,
            "placeholder": "Add exercises or activities...",
        }),
    )


# =============================================================
# EXAM RESOURCE — PRACTICAL CONTENT
#===========================================================

class ExamPracticalContentForm(forms.Form):
    """
    Content fields for an Exam Practical resource.
    """

    objectives = forms.CharField(
        required=False,
        label="Practical Objectives",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "What should students achieve?",
        }),
    )

    materials = forms.CharField(
        required=False,
        label="Materials and Equipment",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 5,
            "placeholder": "List the required materials and equipment...",
        }),
    )

    procedures = forms.CharField(
        required=False,
        label="Procedure",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 10,
            "placeholder": "Describe the practical procedure step by step...",
        }),
    )

    activities = forms.CharField(
        required=False,
        label="Practical Activities",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 6,
            "placeholder": "Enter practical tasks for students...",
        }),
    )

    expected_results = forms.CharField(
        required=False,
        label="Expected Results",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 6,
            "placeholder": "Describe the expected observations or results...",
        }),
    )

    safety_notes = forms.CharField(
        required=False,
        label="Safety Notes",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Include relevant safety precautions...",
        }),
    )


# =============================================================
# EXAM RESOURCE — REVISION CONTENT
# =============================================================

class ExamRevisionContentForm(forms.Form):
    """
    Content fields for a Revision Materials resource.
    """

    topic = forms.CharField(
        required=False,
        label="Revision Topic",
        max_length=255,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter the topic...",
        }),
    )

    summary = forms.CharField(
        required=False,
        label="Topic Summary",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 8,
            "placeholder": "Write a concise revision summary...",
        }),
    )

    key_points = forms.CharField(
        required=False,
        label="Important Points",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 6,
            "placeholder": "List essential facts, formulas and concepts...",
        }),
    )

    formulas = forms.CharField(
        required=False,
        label="Formulas and Rules",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 5,
            "placeholder": "Enter relevant formulas, rules or principles...",
        }),
    )

    revision_exercises = forms.CharField(
        required=False,
        label="Revision Exercises",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 8,
            "placeholder": "Add practice exercises...",
        }),
    )


# =============================================================
# EXAM RESOURCE — MOCK EXAM INSTRUCTIONS
# =============================================================

class ExamMockExamContentForm(forms.Form):
    """
    Instructions and settings for a Mock Exam resource.

    The actual questions are stored as ExamQuestion records.
    """

    instructions = forms.CharField(
        required=False,
        label="Examination Instructions",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 7,
            "placeholder": "Enter instructions candidates should read before starting...",
        }),
    )

    duration_minutes = forms.IntegerField(
        required=False,
        min_value=1,
        label="Duration (minutes)",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": "1",
            "placeholder": "e.g. 60",
        }),
    )

    total_marks = forms.IntegerField(
        required=False,
        min_value=1,
        label="Total Marks",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": "1",
            "placeholder": "Enter total marks...",
        }),
    )



# =========================================================
# EXAM QUESTION
# ==========================================================

class ExamQuestionForm(forms.ModelForm):
    class Meta:
        model = ExamQuestion
        fields = [
            "resource",
            "source_question",
            "question_number",
            "question_type",
            "question_text",
            "correct_answer",
            "solution",
            "explanation",
            "marks",
            "image",
            "published",
            "order",
        ]

        widgets = {
            "resource": forms.Select(attrs={
                "class": "form-select",
            }),
            "source_question": forms.Select(attrs={
                "class": "form-select",
            }),
            "question_number": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
            }),
            "question_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "question_text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Enter the question...",
            }),
            "correct_answer": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter the correct answer...",
            }),
            "solution": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Enter the detailed solution or workings...",
            }),
            "explanation": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Add an additional explanation if needed...",
            }),
            "marks": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["source_question"].required = False
        self.fields["source_question"].empty_label = (
            "Select a source question (optional)"
        )

        self.fields["source_question"].queryset = (
            ExamQuestion.objects.filter(
                resource__resource_type="past_questions",
            ).select_related(
                "resource",
                "resource__exam",
                "resource__subject",
                "resource__year",
            ).order_by(
                "resource__exam__name",
                "resource__subject__name",
                "resource__year__year",
                "question_number",
            )
        )

        self.fields["source_question"].label_from_instance = (
            self.source_question_label
        )

    @staticmethod
    def source_question_label(question):
        resource = question.resource

        year_label = (
            resource.year.year
            if resource.year_id
            else "Year not specified"
        )

        subject_label = (
            resource.subject.name
            if resource.subject_id
            else "Subject not specified"
        )

        return (
            f"{resource.exam.name} - "
            f"{subject_label} - "
            f"{year_label} - "
            f"{resource.title} - "
            f"Question {question.question_number}"
        )

    def clean(self):
        cleaned_data = super().clean()

        resource = cleaned_data.get("resource")
        source_question = cleaned_data.get("source_question")

        if source_question and resource:
            if resource.resource_type != "solutions":
                self.add_error(
                    "source_question",
                    "An existing Past Question can only be linked "
                    "to a Solutions resource.",
                )
            else:
                source_resource = source_question.resource

                if (
                    source_resource.resource_type != "past_questions"
                    or source_resource.exam_id != resource.exam_id
                    or source_resource.subject_id != resource.subject_id
                    or source_resource.year_id != resource.year_id
                ):
                    self.add_error(
                        "source_question",
                        "The selected question must belong to a "
                        "Past Questions resource for the same "
                        "examination, subject and year.",
                    )

        return cleaned_data


# =============================================================
# EXAM CHOICE
# =============================================================

class ExamChoiceForm(forms.ModelForm):
    class Meta:
        model = ExamChoice
        fields = [
            "text",
            "is_correct",
            "order",
        ]

        widgets = {
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter this answer choice...",
            }),
            "is_correct": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["text"].required = False
        self.fields["is_correct"].required = False
        self.fields["order"].required = False

# ===========================================================
# ADULT STORIES & NOVELS
# ===========================================================

class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = [
            "title",
            "slug",
            "description",
            "cover",
            "genre",
            "audience",
            "content_rating",
            "author_name",
            "status",
            "is_featured",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter story title",
            }),
            "slug": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. the-hidden-truth",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Write a compelling story description...",
            }),
            "cover": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "genre": forms.Select(attrs={
                "class": "form-select",
            }),
            "audience": forms.Select(attrs={
                "class": "form-select",
            }),
            "content_rating": forms.Select(attrs={
                "class": "form-select",
            }),
            "author_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Author name",
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
            "is_featured": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


class StoryChapterForm(forms.ModelForm):
    class Meta:
        model = StoryChapter
        fields = [
            "story",
            "chapter_number",
            "title",
            "content",
            "is_published",
        ]
        widgets = {
            "story": forms.Select(attrs={
                "class": "form-select",
            }),
            "chapter_number": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter chapter title",
            }),
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 16,
                "placeholder": "Write the complete chapter content...",
            }),
            "is_published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["story"].queryset = (
            Story.objects.order_by("-created_at")
        )


# =============================================================
# PLAY & LEARN — GAMES
# =============================================================

class PlayGameForm(forms.ModelForm):
    class Meta:
        model = PlayGame
        fields = [
            "name",
            "slug",
            "url_name",
            "description",
            "category",
            "min_age",
            "max_age",
            "difficulty",
            "thumbnail",
            "is_published",
            "order",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter game name",
            }),
            "slug": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. memory-match",
            }),
            "url_name": forms.Select(attrs={
                "class": "form-select",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Describe this game...",
            }),
            "category": forms.Select(attrs={
                "class": "form-select",
            }),
            "min_age": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "max_age": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "difficulty": forms.Select(attrs={
                "class": "form-select",
            }),
            "thumbnail": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "is_published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        min_age = cleaned_data.get("min_age")
        max_age = cleaned_data.get("max_age")

        if (
            min_age is not None
            and max_age is not None
            and min_age > max_age
        ):
            self.add_error(
                "max_age",
                "Maximum age cannot be lower than minimum age.",
            )

        return cleaned_data

class CurriculumMaterialForm(forms.ModelForm):
    class Meta:
        model = CurriculumMaterial
        fields = [
            "title",
            "file",
            "description",
            "published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Week 1 Study Material",
            }),
            "file": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": ".pdf,application/pdf",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Briefly describe the contents of this PDF.",
            }),
            "published": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")

        if uploaded_file:
            if not uploaded_file.name.lower().endswith(".pdf"):
                raise forms.ValidationError(
                    "Only PDF files are allowed."
                )

        return uploaded_file
    