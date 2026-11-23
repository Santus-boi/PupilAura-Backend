from django.contrib import admin

from .models import (
    Exam,
    ExamSubject,
    ExamYear,
    ExamResource,
    ExamQuestion,
    ExamChoice,
    ExamAttempt,
    ExamAnswer,
)


# ==============================================================
# INLINES
# ==============================================================

class ExamChoiceInline(admin.TabularInline):
    """
    Answer choices, editable directly inside an ExamQuestion.

    4 blank rows are shown by default — enough for a standard MCQ.
    """
    model = ExamChoice
    extra = 4
    fields = (
        "order",
        "text",
        "is_correct",
    )
    ordering = ("order", "id")
    show_change_link = True


class ExamQuestionInline(admin.TabularInline):
    """
    Questions, editable directly inside an ExamResource.

    Saved in one page load. Each row can be expanded
    to add its choices via the ExamQuestion admin page.
    """
    model = ExamQuestion
    extra = 0
    fields = (
        "order",
        "question_number",
        "question_type",
        "marks",
        "published",
    )
    ordering = ("order", "question_number")
    show_change_link = True


# ==============================================================
# EXAM
# ==============================================================

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "published",
        "order",
    )

    list_filter = (
        "published",
    )

    search_fields = (
        "name",
        "description",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    ordering = (
        "order",
        "name",
    )


# ==============================================================
# EXAM SUBJECT
# ==============================================================

@admin.register(ExamSubject)
class ExamSubjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "exam",
        "code",
        "published",
        "order",
    )

    list_filter = (
        "exam",
        "published",
    )

    search_fields = (
        "name",
        "code",
        "exam__name",
    )

    ordering = (
        "exam",
        "order",
        "name",
    )


# ==============================================================
# EXAM YEAR
# ==============================================================

@admin.register(ExamYear)
class ExamYearAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "exam",
        "published",
        "order",
    )

    list_filter = (
        "exam",
        "published",
    )

    search_fields = (
        "exam__name",
    )

    ordering = (
        "-year",
    )


# ==============================================================
# EXAM RESOURCE (with questions inline)
# ==============================================================

@admin.register(ExamResource)
class ExamResourceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "exam",
        "subject",
        "year",
        "resource_type",
        "published",
        "order",
    )

    list_filter = (
        "exam",
        "subject",
        "year",
        "resource_type",
        "published",
    )

    search_fields = (
        "title",
        "description",
        "content",
        "exam__name",
        "subject__name",
    )

    ordering = (
        "order",
        "title",
    )

    inlines = [
        ExamQuestionInline,
    ]


# ==============================================================
# EXAM QUESTION (with choices inline)
# ==============================================================

@admin.register(ExamQuestion)
class ExamQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "question_number",
        "resource",
        "question_type",
        "marks",
        "published",
        "order",
    )

    list_filter = (
        "question_type",
        "published",
    )

    search_fields = (
        "question_text",
        "resource__title",
    )

    ordering = (
        "resource",
        "order",
        "question_number",
    )

    inlines = [
        ExamChoiceInline,
    ]


# ==============================================================
# EXAM CHOICE
# ==============================================================

@admin.register(ExamChoice)
class ExamChoiceAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "text",
        "is_correct",
        "order",
    )

    list_filter = (
        "is_correct",
    )

    search_fields = (
        "text",
        "question__question_text",
    )

    ordering = (
        "question",
        "order",
    )


# ==============================================================
# EXAM ATTEMPT
# ==============================================================

@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "resource",
        "score",
        "total_marks",
        "percentage",
        "passed",
        "completed",
        "started_at",
    )

    list_filter = (
        "passed",
        "completed",
        "resource__exam",
    )

    search_fields = (
        "student__username",
        "student__email",
        "resource__title",
    )

    readonly_fields = (
        "started_at",
        "submitted_at",
    )

    ordering = (
        "-started_at",
    )


# ==============================================================
# EXAM ANSWER
# ==============================================================

@admin.register(ExamAnswer)
class ExamAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "attempt",
        "question",
        "selected_choice",
        "is_correct",
        "marks_awarded",
    )

    list_filter = (
        "is_correct",
    )

    search_fields = (
        "attempt__student__username",
        "question__question_text",
    )

    ordering = (
        "attempt",
        "question",
    )