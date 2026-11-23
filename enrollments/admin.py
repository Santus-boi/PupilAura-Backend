from django.contrib import admin

from .models import Enrollment, LessonProgress


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "subject",
        "get_school_class",
        "get_education_level",
        "enrolled_at",
        "completed",
    )

    list_filter = (
        "completed",
        "subject__school_class",
        "subject__school_class__education_level",
    )

    search_fields = (
        "student__user__email",
        "subject__name",
        "subject__school_class__name",
        "subject__school_class__education_level__name",
    )

    ordering = (
        "-enrolled_at",
    )

    @admin.display(
        description="School Class"
    )
    def get_school_class(self, obj):
        if obj.subject and obj.subject.school_class:
            return obj.subject.school_class.name

        return "-"

    @admin.display(
        description="Education Level"
    )
    def get_education_level(self, obj):
        if (
            obj.subject
            and obj.subject.school_class
            and obj.subject.school_class.education_level
        ):
            return obj.subject.school_class.education_level.name

        return "-"


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = (
        "enrollment",
        "lesson",
        "get_subject",
        "get_school_class",
        "completed",
        "completed_at",
    )

    list_filter = (
        "completed",
        "lesson__week__term__term_type",
        "lesson__week__term__subject",
        "lesson__week__term__subject__school_class",
    )

    search_fields = (
        "enrollment__student__user__email",
        "lesson__title",
        "lesson__week__title",
        "lesson__week__term__name",
        "lesson__week__term__subject__name",
    )

    ordering = (
        "-completed_at",
    )

    @admin.display(
        description="Subject"
    )
    def get_subject(self, obj):
        if (
            obj.lesson
            and obj.lesson.week
            and obj.lesson.week.term
            and obj.lesson.week.term.subject
        ):
            return obj.lesson.week.term.subject.name

        return "-"

    @admin.display(
        description="School Class"
    )
    def get_school_class(self, obj):
        if (
            obj.lesson
            and obj.lesson.week
            and obj.lesson.week.term
            and obj.lesson.week.term.subject
            and obj.lesson.week.term.subject.school_class
        ):
            return (
                obj.lesson.week.term.subject.school_class.name
            )

        return "-"