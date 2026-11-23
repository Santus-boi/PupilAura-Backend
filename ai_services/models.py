import uuid

from django.conf import settings
from django.db import models


class AICallLog(models.Model):
    FEATURE_LESSON = "lesson"
    FEATURE_QUIZ = "quiz"
    FEATURE_FLASHCARDS = "flashcards"
    FEATURE_SUMMARY = "summary"
    FEATURE_EXAM_QUESTIONS = "exam_questions"
    FEATURE_EXAM_RESOURCES = "exam_resource"

    FEATURE_CHOICES = [
        (FEATURE_LESSON, "Lesson Generator"),
        (FEATURE_QUIZ, "Quiz Generator"),
        (FEATURE_FLASHCARDS, "Flashcards"),
        (FEATURE_SUMMARY, "Summary"),
        (FEATURE_EXAM_QUESTIONS, "Exam Questions"),
        (FEATURE_EXAM_RESOURCES, "Exam Resource Generator"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="ai_calls",
    )
    feature = models.CharField(max_length=32, choices=FEATURE_CHOICES, db_index=True)
    provider = models.CharField(max_length=32)
    model = models.CharField(max_length=64)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    cost_estimate = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_feature_display()} · {self.created_at:%Y-%m-%d %H:%M}"