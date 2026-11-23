
from django import forms

from learning.models import (
    EducationLevel,
    SchoolClass,
    Subject,
    Term,
    Week,
    Lesson,
)


class EducationLevelForm(forms.ModelForm):
    class Meta:
        model = EducationLevel
        fields = [
            "name",
            "level_type",
            "order",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter education level name",
                }
            ),
            "level_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                }
            ),
        }


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = [
            "name",
            "education_level",
            "order",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter class name",
                }
            ),
            "education_level": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            "education_level"
        ].queryset = EducationLevel.objects.order_by(
            "order",
            "name",
        )


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = [
            "name",
            "school_class",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter subject name",
                }
            ),
            "school_class": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            "school_class"
        ].queryset = (
            SchoolClass.objects
            .select_related("education_level")
            .order_by(
                "education_level__order",
                "order",
                "name",
            )
        )

        self.fields[
            "school_class"
        ].label_from_instance = (
            lambda obj: (
                f"{obj.education_level.name} - "
                f"{obj.name}"
            )
        )


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = [
            "name",
            "term_type",
            "subject",
            "order",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter term name",
                }
            ),
            "term_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "subject": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            "subject"
        ].queryset = (
            Subject.objects
            .select_related(
                "school_class",
                "school_class__education_level",
            )
            .order_by(
                "school_class__education_level__order",
                "school_class__order",
                "name",
            )
        )

        self.fields[
            "subject"
        ].label_from_instance = (
            lambda obj: (
                f"{obj.school_class.education_level.name} - "
                f"{obj.school_class.name} - "
                f"{obj.name}"
            )
            if obj.school_class
            else obj.name
        )


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
            "term": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "number": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional week title",
                }
            ),
            "overview": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Enter the general overview "
                        "for this week..."
                    ),
                }
            ),
            "activities": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Enter activities for this week..."
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            "term"
        ].queryset = (
            Term.objects
            .select_related(
                "subject",
                "subject__school_class",
                "subject__school_class__education_level",
            )
            .order_by(
                "subject__school_class__education_level__order",
                "subject__school_class__order",
                "subject__name",
                "order",
            )
        )

        self.fields[
            "term"
        ].label_from_instance = (
            lambda obj: (
                f"{obj.subject.school_class.education_level.name} - "
                f"{obj.subject.school_class.name} - "
                f"{obj.subject.name} - "
                f"{obj.name}"
            )
        )


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
            "week": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter lesson title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
            "objectives": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "What should students be able "
                        "to do after this lesson?"
                    ),
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "placeholder": (
                        "Enter the main teaching content..."
                    ),
                }
            ),
            "examples": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                }
            ),
            "key_points": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                }
            ),
            "activity": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                }
            ),
            "practical": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                }
            ),
            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                }
            ),
            "published": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            "week"
        ].queryset = (
            Week.objects
            .select_related(
                "term",
                "term__subject",
                "term__subject__school_class",
                "term__subject__school_class__education_level",
            )
            .order_by(
                "term__subject__school_class__education_level__order",
                "term__subject__school_class__order",
                "term__subject__name",
                "term__order",
                "number",
            )
        )

        self.fields[
            "week"
        ].label_from_instance = (
            lambda obj: (
                f"{obj.term.subject.school_class.education_level.name} - "
                f"{obj.term.subject.school_class.name} - "
                f"{obj.term.subject.name} - "
                f"{obj.term.name} - "
                f"Week {obj.number}"
            )
        )
