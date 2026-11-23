from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from learning.models import Lesson, Week, Term


class Quiz(models.Model):

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )

    week = models.ForeignKey(
        Week,
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    pass_mark = models.PositiveIntegerField(
        default=50
    )

    published = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        Q(lesson__isnull=False)
                        & Q(week__isnull=True)
                        & Q(term__isnull=True)
                    )
                    |
                    (
                        Q(lesson__isnull=True)
                        & Q(week__isnull=False)
                        & Q(term__isnull=True)
                    )
                    |
                    (
                        Q(lesson__isnull=True)
                        & Q(week__isnull=True)
                        & Q(term__isnull=False)
                    )
                ),
                name="quiz_has_exactly_one_parent",
            )
        ]

    def clean(self):

        parents = [
            self.lesson_id,
            self.week_id,
            self.term_id,
        ]

        if sum(
            parent is not None
            for parent in parents
        ) != 1:

            raise ValidationError(
                "An assessment must belong to exactly one "
                "lesson, week, or term."
            )

        if self.week_id:

            self._validate_week_parent()

        if self.term_id:

            self._validate_term_parent()

    def _validate_week_parent(self):

        if not self.week.term_id:

            raise ValidationError(
                "The selected week must belong to a term."
            )

    def _validate_term_parent(self):

        if not self.term.subject_id:

            raise ValidationError(
                "The selected term must belong to a subject."
            )

    @property
    def assessment_type(self):

        if self.lesson_id:

            return "lesson"

        if self.week_id:

            return "week"

        if self.term_id:

            return "term"

        return None

    @property
    def assessment_type_display(self):

        labels = {
            "lesson": "Lesson Assessment",
            "week": "Week Assessment",
            "term": "Term Assessment",
        }

        return labels.get(
            self.assessment_type,
            "Assessment",
        )

    @property
    def parent(self):

        if self.lesson_id:

            return self.lesson

        if self.week_id:

            return self.week

        if self.term_id:

            return self.term

        return None

    def __str__(self):

        return self.title


class Question(models.Model):

    class QuestionType(models.TextChoices):

        OBJECTIVE = (
            "objective",
            "Objective",
        )

        THEORY = (
            "theory",
            "Theory",
        )

        PRACTICAL = (
            "practical",
            "Practical",
        )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    text = models.TextField()

    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.OBJECTIVE,
    )

    points = models.PositiveIntegerField(
        default=1
    )

    order = models.PositiveIntegerField(
        default=0
    )

    class Meta:

        ordering = [
            "order"
        ]

    def clean(self):

        if (
            self.question_type
            == self.QuestionType.OBJECTIVE
            and self.pk
        ):

            if not self.choices.exists():

                raise ValidationError(
                    "An objective question must have at least one choice."
                )

    @property
    def is_objective(self):

        return (
            self.question_type
            == self.QuestionType.OBJECTIVE
        )

    @property
    def is_theory(self):

        return (
            self.question_type
            == self.QuestionType.THEORY
        )

    @property
    def is_practical(self):

        return (
            self.question_type
            == self.QuestionType.PRACTICAL
        )

    @property
    def requires_manual_review(self):

        return (
            self.question_type
            in [
                self.QuestionType.THEORY,
                self.QuestionType.PRACTICAL,
            ]
        )

    def __str__(self):

        return self.text[:80]


class Choice(models.Model):

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )

    text = models.CharField(
        max_length=500
    )

    is_correct = models.BooleanField(
        default=False
    )

    order = models.PositiveIntegerField(
        default=0
    )

    class Meta:

        ordering = [
            "order"
        ]

    def __str__(self):

        return self.text


class QuizAttempt(models.Model):

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    score = models.PositiveIntegerField(
        default=0
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    passed = models.BooleanField(
        default=False
    )

    def __str__(self):

        return (
            f"{self.student.email} - "
            f"{self.quiz.title}"
        )

    @property
    def manual_answers(self):

        return self.answers.filter(
            question__question_type__in=[
                Question.QuestionType.THEORY,
                Question.QuestionType.PRACTICAL,
            ]
        )

    @property
    def objective_answers(self):

        return self.answers.filter(
            question__question_type=(
                Question.QuestionType.OBJECTIVE
            )
        )

    @property
    def has_manual_questions(self):

        return self.manual_answers.exists()

    @property
    def has_pending_review(self):

        return self.manual_answers.filter(
            reviewed=False
        ).exists()

    @property
    def all_manual_answers_reviewed(self):

        manual_answers = self.manual_answers

        if not manual_answers.exists():

            return True

        return not manual_answers.filter(
            reviewed=False
        ).exists()

    @property
    def review_status(self):

        if not self.has_manual_questions:

            return "not_required"

        if self.has_pending_review:

            return "pending"

        return "reviewed"

    @property
    def review_status_display(self):

        labels = {
            "not_required": "Automatically Graded",
            "pending": "Review Pending",
            "reviewed": "Reviewed",
        }

        return labels.get(
            self.review_status,
            "Review Pending",
        )

    @property
    def automatic_score(self):

        return sum(
            answer.points_earned
            for answer in self.objective_answers
        )

    @property
    def manual_score(self):

        return sum(
            answer.points_earned
            for answer in self.manual_answers
        )

    @property
    def total_points_possible(self):

        return sum(
            answer.question.points
            for answer in self.answers.select_related(
                "question"
            )
        )

    def finish(
        self,
        score,
        percentage,
    ):

        self.score = score

        self.percentage = percentage

        self.passed = (
            percentage >= self.quiz.pass_mark
        )

        self.completed_at = timezone.now()

        self.save()

    def recalculate_result(self):

        """
        Recalculate the complete assessment after
        manual grading or any answer modification.

        Objective questions are graded automatically.

        Theory and practical questions remain pending
        until an administrator reviews them.

        The attempt can only be marked as passed after
        all manually reviewed answers have been completed.
        """

        answers = (
            self.answers
            .select_related(
                "question"
            )
        )

        total_points = 0

        earned_points = 0

        has_pending_review = False

        for answer in answers:

            question = answer.question

            total_points += (
                question.points
            )

            earned_points += (
                answer.points_earned
            )

            if (
                question.question_type
                in [
                    Question.QuestionType.THEORY,
                    Question.QuestionType.PRACTICAL,
                ]
                and not answer.reviewed
            ):

                has_pending_review = True

        if total_points > 0:

            percentage = (
                earned_points
                / total_points
            ) * 100

        else:

            percentage = 0

        self.score = earned_points

        self.percentage = percentage

        self.passed = (
            not has_pending_review
            and percentage >= self.quiz.pass_mark
        )

        self.save(
            update_fields=[
                "score",
                "percentage",
                "passed",
            ]
        )

        return {
            "score": earned_points,
            "total_points": total_points,
            "percentage": percentage,
            "passed": self.passed,
            "has_pending_review": has_pending_review,
            "review_status": self.review_status,
        }


class Answer(models.Model):

    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="student_answers",
    )

    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="selected_answers",
        null=True,
        blank=True,
    )

    text_answer = models.TextField(
        blank=True
    )

    is_correct = models.BooleanField(
        default=False
    )

    points_earned = models.PositiveIntegerField(
        default=0
    )

    reviewed = models.BooleanField(
        default=False
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_quiz_answers",
        null=True,
        blank=True,
    )

    feedback = models.TextField(
        blank=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "attempt",
                    "question",
                ],
                name="unique_answer_per_attempt_question",
            )
        ]

    def clean(self):

        if (
            self.question.question_type
            == Question.QuestionType.OBJECTIVE
        ):

            if not self.selected_choice_id:

                raise ValidationError(
                    "An objective question requires a selected choice."
                )

            if (
                self.selected_choice
                and self.selected_choice.question_id
                != self.question_id
            ):

                raise ValidationError(
                    "The selected choice does not belong "
                    "to this question."
                )

        else:

            if self.selected_choice_id:

                raise ValidationError(
                    "Theory and practical questions cannot "
                    "use a selected choice."
                )

        if self.points_earned > self.question.points:

            raise ValidationError(
                "Points earned cannot be greater than "
                "the question's total points."
            )

        if (
            self.reviewed
            and self.question.question_type
            in [
                Question.QuestionType.THEORY,
                Question.QuestionType.PRACTICAL,
            ]
            and self.reviewed_at is None
        ):

            self.reviewed_at = timezone.now()

    def save(
        self,
        *args,
        **kwargs,
    ):

        is_manual_question = (
            self.question_id
            and self.question.question_type
            in [
                Question.QuestionType.THEORY,
                Question.QuestionType.PRACTICAL,
            ]
        )

        if is_manual_question:

            if self.reviewed:

                if self.reviewed_at is None:

                    self.reviewed_at = (
                        timezone.now()
                    )

            else:

                self.reviewed_at = None
                self.reviewed_by = None

        else:

            self.reviewed = True

            if self.reviewed_at is None:

                self.reviewed_at = (
                    timezone.now()
                )

        super().save(
            *args,
            **kwargs
        )

    def mark_reviewed(
        self,
        reviewer,
        points_earned,
        feedback="",
        is_correct=False,
    ):

        """
        Mark a theory/practical answer as reviewed
        by an administrator.
        """

        if self.question.question_type not in [
            Question.QuestionType.THEORY,
            Question.QuestionType.PRACTICAL,
        ]:

            raise ValidationError(
                "Only theory and practical answers "
                "require manual review."
            )

        if points_earned < 0:

            raise ValidationError(
                "Points earned cannot be negative."
            )

        if points_earned > self.question.points:

            raise ValidationError(
                "Points earned cannot be greater than "
                "the question's total points."
            )

        self.points_earned = (
            points_earned
        )

        self.is_correct = (
            is_correct
        )

        self.feedback = (
            feedback.strip()
            if feedback
            else ""
        )

        self.reviewed = True

        self.reviewed_at = (
            timezone.now()
        )

        self.reviewed_by = (
            reviewer
        )

        self.save()

        self.attempt.recalculate_result()

    def __str__(self):

        return (
            f"{self.attempt.student.email} - "
            f"{self.question.text[:50]}"
        )