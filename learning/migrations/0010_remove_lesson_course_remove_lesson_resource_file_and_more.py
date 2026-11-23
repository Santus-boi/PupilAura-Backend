from django.db import migrations, models
import django.db.models.deletion


def prepare_existing_data(apps, schema_editor):
    Subject = apps.get_model("learning", "Subject")
    SchoolClass = apps.get_model("learning", "SchoolClass")

    # Existing subjects that already belong to a school class are kept.
    # Subjects without a class are intentionally left alone for now.
    #
    # We do NOT assign a random SchoolClass because that could corrupt
    # existing curriculum data.


class Migration(migrations.Migration):

    dependencies = [
        (
            "learning",
            "0009_lessonimage_lessonresource_lessonvideo",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="lesson",
            name="course",
        ),
        migrations.RemoveField(
            model_name="lesson",
            name="resource_file",
        ),
        migrations.RemoveField(
            model_name="lesson",
            name="video_url",
        ),
        migrations.RemoveField(
            model_name="subject",
            name="education_level",
        ),

        migrations.AlterField(
            model_name="course",
            name="description",
            field=models.TextField(blank=True),
        ),

        migrations.RunPython(
            prepare_existing_data,
            migrations.RunPython.noop,
        ),

        migrations.AlterField(
            model_name="lesson",
            name="week",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="lessons",
                to="learning.week",
                null=True,
                blank=True,
            ),
        ),

        migrations.AlterField(
            model_name="subject",
            name="school_class",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="subjects",
                to="learning.schoolclass",
                null=True,
                blank=True,
            ),
        ),

        migrations.AlterField(
            model_name="term",
            name="subject",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="terms",
                to="learning.subject",
            ),
        ),
    ]