
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Exam(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
    )

    published = models.BooleanField(
        default=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ExamSubject(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="subjects",
    )

    name = models.CharField(
        max_length=150,
    )

    code = models.CharField(
        max_length=50,
        blank=True,
    )

    published = models.BooleanField(
        default=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        ordering = ["order", "name"]

        constraints = [
            models.UniqueConstraint(
                fields=["exam", "name"],
                name="unique_exam_subject",
            )
        ]

    def __str__(self):
        return f"{self.exam.name} - {self.name}"


class ExamYear(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="years",
    )

    year = models.PositiveIntegerField()

    published = models.BooleanField(
        default=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["-year"]

        constraints = [
            models.UniqueConstraint(
                fields=["exam", "year"],
                name="unique_exam_year",
            )
        ]

    def __str__(self):
        return f"{self.exam.name} - {self.year}"


class ExamResource(models.Model):

    RESOURCE_TYPES = [
        ("past_questions", "Past Questions"),
        ("solutions", "Solutions / Answers"),
        ("lesson", "Exam Lesson"),
        ("practical", "Practical"),
        ("mock_exam", "Mock Exam"),
        ("revision", "Revision Materials"),
    ]

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="resources",
    )

    subject = models.ForeignKey(
        ExamSubject,
        on_delete=models.CASCADE,
        related_name="resources",
    )

    year = models.ForeignKey(
        ExamYear,
        on_delete=models.CASCADE,
        related_name="resources",
    )

    resource_type = models.CharField(
        max_length=30,
        choices=RESOURCE_TYPES,
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
    )

    # General resource content.
    content = models.TextField(
        blank=True,
    )

    # Structured content for lessons, practicals,
    # revision materials and other resource-specific data.
    structured_content = models.JSONField(
        default=dict,
        blank=True,
    )

    file = models.FileField(
        upload_to="exam_resources/",
        blank=True,
        null=True,
    )

    video_url = models.URLField(
        blank=True,
    )

    published = models.BooleanField(
        default=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["order", "title"]

    def clean(self):
        errors = {}

        if self.subject_id and self.exam_id:
            if self.subject.exam_id != self.exam_id:
                errors["subject"] = (
                    "The selected subject does not belong "
                    "to the selected examination."
                )

        if self.year_id and self.exam_id:
            if self.year.exam_id != self.exam_id:
                errors["year"] = (
                    "The selected year does not belong "
                    "to the selected examination."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.exam.name} - "
            f"{self.subject.name} - "
            f"{self.year.year} - "
            f"{self.title}"
        )


class ExamQuestion(models.Model):

    QUESTION_TYPES = [
        ("mcq", "Multiple Choice"),
        ("theory", "Theory"),
        ("practical", "Practical"),
    ]

    resource = models.ForeignKey(
        ExamResource,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    # Optional link to an original past question.
    # This allows a Solutions resource to reuse
    # an existing question without requiring it.
    source_question = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solution_copies",
    )

    question_number = models.PositiveIntegerField()

    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default="mcq",
    )

    question_text = models.TextField()

    # Retained for compatibility with existing records
    # and existing code that uses explanations.
    explanation = models.TextField(
        blank=True,
    )

    # The actual correct answer.
    correct_answer = models.TextField(
        blank=True,
    )

    # Detailed solution, calculations or workings.
    solution = models.TextField(
        blank=True,
    )

    marks = models.PositiveIntegerField(
        default=1,
    )

    image = models.ImageField(
        upload_to="exam_questions/",
        blank=True,
        null=True,
    )

    published = models.BooleanField(
        default=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["order", "question_number"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "resource",
                    "question_number",
                ],
                name="unique_resource_question_number",
            )
        ]

    def clean(self):
        errors = {}

        if self.source_question_id:
            if self.source_question_id == self.pk:
                errors["source_question"] = (
                    "A question cannot reference itself."
                )
            elif self.resource_id:
                if self.resource.resource_type != "solutions":
                    errors["source_question"] = (
                        "Source questions can only be linked "
                        "from a Solutions resource."
                    )
                elif (
                    self.source_question.resource.resource_type
                    != "past_questions"
                ):
                    errors["source_question"] = (
                        "The selected source must belong "
                        "to a Past Questions resource."
                    )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.resource.title} "
            f"- Question {self.question_number}"
        )


class ExamChoice(models.Model):

    question = models.ForeignKey(
        ExamQuestion,
        on_delete=models.CASCADE,
        related_name="choices",
    )

    text = models.TextField()

    is_correct = models.BooleanField(
        default=False,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "question",
                    "order",
                ],
                name="unique_question_choice_order",
            )
        ]

    def __str__(self):
        return self.text[:80]


class ExamAttempt(models.Model):

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_attempts",
    )

    resource = models.ForeignKey(
        ExamResource,
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    score = models.PositiveIntegerField(
        default=0,
    )

    total_marks = models.PositiveIntegerField(
        default=0,
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    passed = models.BooleanField(
        default=False,
    )

    completed = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.resource.title} - "
            f"{self.percentage}%"
        )


class ExamAnswer(models.Model):

    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    question = models.ForeignKey(
        ExamQuestion,
        on_delete=models.CASCADE,
        related_name="exam_answers",
    )

    selected_choice = models.ForeignKey(
        ExamChoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="selected_exam_answers",
    )

    is_correct = models.BooleanField(
        default=False,
    )

    marks_awarded = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "attempt",
                    "question",
                ],
                name="unique_attempt_question",
            )
        ]

    def __str__(self):
        return (
            f"{self.attempt} - "
            f"Question {self.question.question_number}"
        )
