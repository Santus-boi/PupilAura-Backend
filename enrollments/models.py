from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import StudentProfile
from learning.models import Subject, Lesson


class Enrollment(models.Model):
    """
    Enrolls a student into a subject.

    PupilAura curriculum hierarchy:

    EducationLevel
        ↓
    SchoolClass
        ↓
    Subject
        ↓
    Term
        ↓
    Week
        ↓
    Lesson

    A student enrolls in a Subject rather than
    the old Course model.
    """

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="enrollments",
        null=True,
        blank=True,
    )

    enrolled_at = models.DateTimeField(
        auto_now_add=True,
    )

    completed = models.BooleanField(
        default=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "subject",
                ],
                name="unique_student_subject_enrollment",
            )
        ]

        ordering = [
            "-enrolled_at",
        ]

    def __str__(self):
        return (
            f"{self.student.user.email} - "
            f"{self.subject.name}"
        )


class LessonProgress(models.Model):
    """
    Stores a student's progress through lessons.

    A lesson belongs to a Week, which belongs to a Term,
    which belongs to a Subject.

    Therefore LessonProgress can determine the student's
    subject automatically through the lesson.
    """

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="student_progress",
    )

    completed = models.BooleanField(
        default=False,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "enrollment",
                    "lesson",
                ],
                name="unique_lesson_progress",
            )
        ]

        ordering = [
            "-completed_at",
        ]

    def clean(self):
        """
        Make sure the lesson belongs to the same subject
        as the student's enrollment.
        """

        if not self.lesson_id or not self.enrollment_id:
            return

        lesson_subject_id = (
            self.lesson.week.term.subject_id
            if self.lesson.week
            and self.lesson.week.term
            else None
        )

        if (
            lesson_subject_id
            and lesson_subject_id != self.enrollment.subject_id
        ):
            raise ValidationError(
                {
                    "lesson": (
                        "This lesson does not belong to "
                        "the subject for this enrollment."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.enrollment.student.user.email} - "
            f"{self.lesson.title}"
        )