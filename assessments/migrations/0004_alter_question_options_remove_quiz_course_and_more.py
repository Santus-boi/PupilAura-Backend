from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            "assessments",
            "0003_alter_quiz_course_alter_quiz_lesson",
        ),
        (
            "learning",
            "0010_remove_lesson_course_remove_lesson_resource_file_and_more",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="question",
            options={
                "ordering": ["order"],
            },
        ),

        migrations.RemoveField(
            model_name="quiz",
            name="course",
        ),

        migrations.AlterField(
            model_name="quiz",
            name="lesson",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="quizzes",
                to="learning.lesson",
            ),
        ),
    ]