from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import (
    Quiz,
    Question,
    Choice,
    QuizAttempt,
    Answer,
)


# ============================================================
# INLINES
# ============================================================

class ChoiceInline(admin.TabularInline):
    """
    Answer choices, edited on the same page as the question.

    4 blank rows appear by default — enough for a standard MCQ.
    """
    model = Choice
    extra = 4
    fields = (
        "order",
        "text",
        "is_correct",
    )
    ordering = ("order", "id")
    show_change_link = True


class QuestionInline(admin.TabularInline):
    """
    Questions, listed on the quiz page for quick overview.

    Use the Question admin to edit full text / choices;
    this inline is for reordering and a fast glance.
    """
    model = Question
    extra = 0
    fields = (
        "order",
        "text",
        "question_type",
        "points",
    )
    ordering = ("order", "id")
    show_change_link = True


# ============================================================
# QUIZ ADMIN
# ============================================================

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "assessment_parent",
        "assessment_type",
        "subject",
        "school_class",
        "pass_mark",
        "published",
        "created_at",
    )

    list_filter = (
        "published",
        "lesson__week__term__subject",
        "week__term__subject",
        "term__subject",
    )

    search_fields = (
        "title",
        "description",
        "lesson__title",
        "week__title",
        "term__name",
        "lesson__week__term__subject__name",
        "week__term__subject__name",
        "term__subject__name",
    )

    ordering = (
        "-created_at",
    )

    inlines = [
        QuestionInline,
    ]

    @admin.display(
        description="Parent"
    )
    def assessment_parent(self, obj):

        if obj.lesson_id:
            return obj.lesson.title

        if obj.week_id:
            return obj.week.title

        if obj.term_id:
            return obj.term.name

        return "-"

    @admin.display(
        description="Type"
    )
    def assessment_type(self, obj):

        return obj.assessment_type_display

    @admin.display(
        description="Subject"
    )
    def subject(self, obj):

        if obj.lesson_id:
            return obj.lesson.subject

        if obj.week_id:
            return obj.week.term.subject

        if obj.term_id:
            return obj.term.subject

        return None

    @admin.display(
        description="School Class"
    )
    def school_class(self, obj):

        subject = self.subject(obj)

        if subject:
            return subject.school_class

        return None


# ============================================================
# QUESTION ADMIN
# ============================================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        "text",
        "quiz",
        "question_type",
        "points",
        "order",
    )

    list_filter = (
        "question_type",
        "quiz",
    )

    search_fields = (
        "text",
        "quiz__title",
    )

    ordering = (
        "quiz",
        "order",
    )

    inlines = [
        ChoiceInline,
    ]


# ============================================================
# CHOICE ADMIN
# ============================================================

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):

    list_display = (
        "text",
        "question",
        "is_correct",
        "order",
    )

    list_filter = (
        "is_correct",
        "question__quiz",
    )

    search_fields = (
        "text",
        "question__text",
    )

    ordering = (
        "question",
        "order",
    )


# ============================================================
# ANSWER FORM
# ============================================================

class AnswerAdminForm(forms.ModelForm):

    class Meta:

        model = Answer

        fields = (
            "attempt",
            "question",
            "selected_choice",
            "text_answer",
            "is_correct",
            "points_earned",
            "reviewed",
        )

        widgets = {
            "text_answer": forms.Textarea(
                attrs={
                    "rows": 8,
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        question = cleaned_data.get(
            "question"
        )

        selected_choice = cleaned_data.get(
            "selected_choice"
        )

        points_earned = cleaned_data.get(
            "points_earned"
        )

        reviewed = cleaned_data.get(
            "reviewed"
        )

        text_answer = (
            cleaned_data.get(
                "text_answer"
            )
            or ""
        ).strip()

        if question is None:

            return cleaned_data

        # =====================================================
        # OBJECTIVE
        # =====================================================

        if (
            question.question_type
            == Question.QuestionType.OBJECTIVE
        ):

            if selected_choice is None:

                raise ValidationError(
                    "An objective question requires "
                    "a selected choice."
                )

            if (
                selected_choice.question_id
                != question.id
            ):

                raise ValidationError(
                    "The selected choice does not "
                    "belong to this question."
                )

            if selected_choice.is_correct:

                cleaned_data["is_correct"] = True

                cleaned_data["points_earned"] = (
                    question.points
                )

            else:

                cleaned_data["is_correct"] = False

                cleaned_data["points_earned"] = 0

            cleaned_data["reviewed"] = True

        # =====================================================
        # THEORY / PRACTICAL
        # =====================================================

        else:

            cleaned_data["selected_choice"] = None

            if points_earned is None:

                points_earned = 0

            if points_earned < 0:

                raise ValidationError(
                    "Points earned cannot be negative."
                )

            if points_earned > question.points:

                raise ValidationError(
                    f"Points earned cannot exceed "
                    f"{question.points} points."
                )

            if reviewed and not text_answer:

                raise ValidationError(
                    "A written answer must contain an answer "
                    "before it can be marked as reviewed."
                )

            cleaned_data["text_answer"] = text_answer

        return cleaned_data


# ============================================================
# ANSWER ADMIN
# ============================================================

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):

    form = AnswerAdminForm

    list_display = (
        "student",
        "quiz",
        "question_number",
        "question_type",
        "points_earned",
        "maximum_points",
        "review_status",
        "is_correct",
    )

    list_filter = (
        "reviewed",
        "is_correct",
        "question__question_type",
        "question__quiz",
    )

    search_fields = (
        "attempt__student__email",
        "attempt__quiz__title",
        "question__text",
        "text_answer",
    )

    ordering = (
        "reviewed",
        "-attempt__started_at",
        "question__order",
    )

    readonly_fields = (
        "student",
        "quiz",
        "question_number",
        "question_type",
        "maximum_points",
    )

    fieldsets = (

        (
            "Assessment",
            {
                "fields": (
                    "attempt",
                    "student",
                    "quiz",
                    "question",
                    "question_number",
                    "question_type",
                    "maximum_points",
                )
            },
        ),

        (
            "Student Answer",
            {
                "fields": (
                    "selected_choice",
                    "text_answer",
                )
            },
        ),

        (
            "Manual Grading",
            {
                "fields": (
                    "points_earned",
                    "is_correct",
                    "reviewed",
                )
            },
        ),
    )

    @admin.display(
        description="Student"
    )
    def student(self, obj):

        return obj.attempt.student.email

    @admin.display(
        description="Quiz"
    )
    def quiz(self, obj):

        return obj.attempt.quiz.title

    @admin.display(
        description="Question"
    )
    def question_number(self, obj):

        return obj.question.order

    @admin.display(
        description="Question Type"
    )
    def question_type(self, obj):

        return obj.question.get_question_type_display()

    @admin.display(
        description="Maximum"
    )
    def maximum_points(self, obj):

        return obj.question.points

    @admin.display(
        description="Status"
    )
    def review_status(self, obj):

        if (
            obj.question.question_type
            == "objective"
        ):

            return "Automatically Graded"

        if obj.reviewed:

            return "Reviewed"

        return "Awaiting Review"

    # ========================================================
    # SAVE ANSWER + RECALCULATE ATTEMPT
    # ========================================================

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        # ----------------------------------------------------
        # Recalculate the complete assessment
        # ----------------------------------------------------

        attempt = obj.attempt

        result = attempt.recalculate_result()

        # ----------------------------------------------------
        # Lesson progress
        # ----------------------------------------------------

        quiz = attempt.quiz

        if (
            quiz.lesson_id
            and attempt.passed
        ):

            from enrollments.models import LessonProgress

            lesson = quiz.lesson

            enrollment = (
                attempt.student
                .student_profile
                .enrollments
                .filter(
                    subject=lesson.week.term.subject
                )
                .first()
            )

            if enrollment:

                from django.utils import timezone

                LessonProgress.objects.update_or_create(
                    enrollment=enrollment,
                    lesson=lesson,
                    defaults={
                        "completed": True,
                        "completed_at": timezone.now(),
                    },
                )


# ============================================================
# QUIZ ATTEMPT ADMIN
# ============================================================

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "quiz",
        "score",
        "total_points",
        "percentage",
        "passed",
        "review_status",
        "started_at",
        "completed_at",
    )

    list_filter = (
        "passed",
        "quiz",
        "answers__reviewed",
    )

    search_fields = (
        "student__email",
        "quiz__title",
    )

    ordering = (
        "-started_at",
    )

    readonly_fields = (
        "student",
        "quiz",
        "score",
        "total_points",
        "percentage",
        "passed",
        "review_status",
        "started_at",
        "completed_at",
    )

    fieldsets = (

        (
            "Attempt",
            {
                "fields": (
                    "student",
                    "quiz",
                    "started_at",
                    "completed_at",
                )
            },
        ),

        (
            "Result",
            {
                "fields": (
                    "score",
                    "total_points",
                    "percentage",
                    "passed",
                    "review_status",
                )
            },
        ),
    )

    @admin.display(
        description="Total Points"
    )
    def total_points(self, obj):

        return sum(
            answer.question.points
            for answer in obj.answers.select_related(
                "question"
            )
        )

    @admin.display(
        description="Review Status"
    )
    def review_status(self, obj):

        pending = obj.answers.filter(
            question__question_type__in=[
                "theory",
                "practical",
            ],
            reviewed=False,
        ).exists()

        if pending:

            return "Awaiting Review"

        return "Fully Reviewed"

    def has_add_permission(
        self,
        request,
    ):

        return False