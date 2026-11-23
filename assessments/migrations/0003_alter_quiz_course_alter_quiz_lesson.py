from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            "assessments",
            "0002_quizattempt_answer",
        ),
        (
            "learning",
            "0009_lessonimage_lessonresource_lessonvideo",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="quiz",
            name="course",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="quizzes",
                to="learning.course",
            ),
        ),
        migrations.AlterField(
            model_name="quiz",
            name="lesson",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="quizzes",
                to="learning.lesson",
            ),
        ),
    ]