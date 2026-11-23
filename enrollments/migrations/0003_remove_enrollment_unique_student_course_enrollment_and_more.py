from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("enrollments", "0002_subject_enrollment"),
        (
            "learning",
            "0011_alter_lesson_week_alter_subject_school_class_and_more",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterField(
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
            ],
            state_operations=[
                migrations.RemoveConstraint(
                    model_name="enrollment",
                    name="unique_student_course_enrollment",
                ),
                migrations.AlterField(
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
            ],
        ),
    ]