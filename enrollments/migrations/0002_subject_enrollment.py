from django.db import migrations, models
import django.db.models.deletion


def copy_course_to_subject(apps, schema_editor):
    Enrollment = apps.get_model("enrollments", "Enrollment")
    Subject = apps.get_model("learning", "Subject")
    LessonProgress = apps.get_model(
        "enrollments",
        "LessonProgress",
    )

    for enrollment in Enrollment.objects.all():
        subject_id = None

        # First try to determine the correct subject from
        # the student's existing lesson progress.
        progress = (
            LessonProgress.objects
            .filter(enrollment_id=enrollment.pk)
            .select_related(
                "lesson__week__term__subject"
            )
            .first()
        )

        if progress and progress.lesson_id:
            lesson = progress.lesson

            if lesson.week_id:
                week = lesson.week

                if week.term_id:
                    term = week.term

                    if term.subject_id:
                        subject_id = term.subject_id

        # Fallback for the current test data.
        if not subject_id:
            subject = (
                Subject.objects
                .filter(name__iexact="Computer Studies")
                .first()
            )

            if subject:
                subject_id = subject.pk

        if subject_id:
            enrollment.subject_id = subject_id
            enrollment.save(
                update_fields=["subject"]
            )


class Migration(migrations.Migration):

    dependencies = [
        (
            "enrollments",
            "0001_initial",
        ),
        (
            "learning",
            "0010_remove_lesson_course_remove_lesson_resource_file_and_more",
        ),
    ]

    operations = [

        # ---------------------------------------------------------
        # 1. Add the new Subject field temporarily as nullable.
        # ---------------------------------------------------------
        migrations.AddField(
            model_name="enrollment",
            name="subject",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="enrollments",
                to="learning.subject",
            ),
        ),

        # ---------------------------------------------------------
        # 2. Convert existing enrollment data.
        # ---------------------------------------------------------
        migrations.RunPython(
            copy_course_to_subject,
            migrations.RunPython.noop,
        ),

        # ---------------------------------------------------------
        # 3. Remove the old Course relationship.
        # ---------------------------------------------------------
        migrations.RemoveField(
            model_name="enrollment",
            name="course",
        ),

        # ---------------------------------------------------------
        # 4. Subject is now required.
        # ---------------------------------------------------------
        migrations.AlterField(
            model_name="enrollment",
            name="subject",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="enrollments",
                to="learning.subject",
            ),
        ),

        # ---------------------------------------------------------
        # 5. Add the new student + subject uniqueness rule.
        #
        # We intentionally do NOT remove the old constraint here
        # because it does not exist in the actual database.
        # ---------------------------------------------------------
        migrations.AddConstraint(
            model_name="enrollment",
            constraint=models.UniqueConstraint(
                fields=[
                    "student",
                    "subject",
                ],
                name="unique_student_subject_enrollment",
            ),
        ),

        # ---------------------------------------------------------
        # 6. Update model ordering.
        # ---------------------------------------------------------
        migrations.AlterModelOptions(
            name="enrollment",
            options={
                "ordering": [
                    "-enrolled_at",
                ],
            },
        ),

        migrations.AlterModelOptions(
            name="lessonprogress",
            options={
                "ordering": [
                    "-completed_at",
                ],
            },
        ),
    ]
