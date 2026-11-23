from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    def __str__(self):
        return self.name


class EducationLevel(models.Model):
    class LevelType(models.TextChoices):
        NURSERY = "nursery", "Nursery"
        PRIMARY = "primary", "Primary"
        JUNIOR_SECONDARY = "jss", "Junior Secondary"
        SENIOR_SECONDARY = "ss", "Senior Secondary"

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    level_type = models.CharField(
        max_length=20,
        choices=LevelType.choices,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class SchoolClass(models.Model):
    name = models.CharField(
        max_length=100,
    )

    education_level = models.ForeignKey(
        EducationLevel,
        on_delete=models.CASCADE,
        related_name="classes",
    )

    order = models.PositiveIntegerField(
        default=0,
    )
    price = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0,)

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "name",
                    "education_level",
                ],
                name="unique_class_per_education_level",
            )
        ]

    def __str__(self):
        return f"{self.education_level.name} - {self.name}"


class Subject(models.Model):
    """
    A subject belongs to a specific SchoolClass.

    Example:

    JSS 1
      ├── Mathematics
      ├── English
      ├── Biology
      └── Computer Studies
    """

    name = models.CharField(
        max_length=100,
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="subjects",
        null=True,
        blank=True,
    )
    price = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "name",
                    "school_class",
                ],
                name="unique_subject_per_class",
            )
        ]

    def __str__(self):
        if self.school_class:
            return f"{self.school_class.name} - {self.name}"

        return self.name


class Term(models.Model):
    """
    A term belongs to a Subject.

    Structure:

    SchoolClass
        ↓
    Subject
        ↓
    Term
    """

    class TermType(models.TextChoices):
        FIRST = "first", "First Term"
        SECOND = "second", "Second Term"
        THIRD = "third", "Third Term"

    name = models.CharField(
        max_length=100,
    )

    term_type = models.CharField(
        max_length=20,
        choices=TermType.choices,
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="terms",
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "term_type",
                    "subject",
                ],
                name="unique_term_per_subject",
            )
        ]

    def __str__(self):
        if self.subject.school_class:
            return (
                f"{self.subject.school_class.name} - "
                f"{self.subject.name} - "
                f"{self.name}"
            )

        return f"{self.subject.name} - {self.name}"


class Week(models.Model):
    """
    A week belongs to a Term.

    Structure:

    SchoolClass
        ↓
    Subject
        ↓
    Term
        ↓
    Week
        ↓
    Lessons
    """

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="weeks",
    )

    number = models.PositiveIntegerField()

    title = models.CharField(
        max_length=200,
        blank=True,
    )

    # General introduction/overview for the week.
    overview = models.TextField(
        blank=True,
    )

    # Activities that belong to the whole week.
    activities = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["number"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "term",
                    "number",
                ],
                name="unique_week_per_term",
            )
        ]

    def __str__(self):
        if self.title:
            return f"Week {self.number} - {self.title}"

        return f"Week {self.number}"


from django.core.validators import FileExtensionValidator


class CurriculumMaterial(models.Model):
    """
    One consolidated downloadable PDF for either a Week or a Term.
    A parent can have only one consolidated material.
    """

    week = models.OneToOneField(
        Week,
        on_delete=models.CASCADE,
        related_name="curriculum_material",
        null=True,
        blank=True,
    )

    term = models.OneToOneField(
        Term,
        on_delete=models.CASCADE,
        related_name="curriculum_material",
        null=True,
        blank=True,
    )

    title = models.CharField(
        max_length=200,
    )

    file = models.FileField(
        upload_to="curriculum_materials/",
        validators=[FileExtensionValidator(["pdf"])],
    )

    description = models.TextField(
        blank=True,
    )

    published = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        week__isnull=False,
                        term__isnull=True,
                    )
                    | models.Q(
                        week__isnull=True,
                        term__isnull=False,
                    )
                ),
                name="material_must_belong_to_week_or_term",
            ),
        ]

    def clean(self):
        super().clean()

        if bool(self.week_id) == bool(self.term_id):
            raise ValidationError(
                "A curriculum material must belong to exactly one Week or Term."
            )

    def __str__(self):
        if self.week_id:
            return f"{self.title} - Week {self.week.number}"

        return f"{self.title} - {self.term.name}"


class Course(models.Model):
    """
    Independent courses.

    Course is NOT part of the school curriculum hierarchy.

    The school curriculum is:

    SchoolClass
        ↓
    Subject
        ↓
    Term
        ↓
    Week
        ↓
    Lesson
    """

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="courses",
    )

    education_level = models.ForeignKey(
        EducationLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )

    thumbnail = models.ImageField(
        upload_to="course_thumbnails/",
        blank=True,
        null=True,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    published = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """
    A lesson belongs directly to a Week.

    School curriculum hierarchy:

    SchoolClass
        ↓
    Subject
        ↓
    Term
        ↓
    Week
        ↓
    Lesson

    A rich lesson can contain:

    - Learning objectives
    - Main lesson content
    - Examples
    - Key points
    - Class activity
    - Practical
    - Videos
    - Images/diagrams
    - Resources/PDF
    - Assessment
    """

    week = models.ForeignKey(
        Week,
        on_delete=models.CASCADE,
        related_name="lessons",
        null=True,
        blank=True,
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    # Learning objectives
    objectives = models.TextField(
        blank=True,
    )

    # Main lesson teaching content
    content = models.TextField(
        blank=True,
    )

    # Examples used to explain the lesson
    examples = models.TextField(
        blank=True,
    )

    # Important things students should remember
    key_points = models.TextField(
        blank=True,
    )

    # Activity students can perform during/after the lesson
    activity = models.TextField(
        blank=True,
    )

    # Practical tab
    practical = models.TextField(
        blank=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    published = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "week",
                    "order",
                ],
                name="unique_lesson_order_per_week",
            )
        ]

    def clean(self):
        if not self.week_id:
            raise ValidationError(
                "A lesson must belong to a week."
            )

    @property
    def subject(self):
        if not self.week_id:
            return None

        return self.week.term.subject

    @property
    def school_class(self):
        if not self.week_id:
            return None

        return self.week.term.subject.school_class

    @property
    def term(self):
        if not self.week_id:
            return None

        return self.week.term

    def __str__(self):
        if self.week_id:
            return (
                f"{self.week.term.subject.name} - "
                f"Week {self.week.number} - "
                f"{self.title}"
            )

        return self.title


class LessonVideo(models.Model):
    """
    Videos belonging to a lesson.

    One lesson can have multiple videos.
    """

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="videos",
    )

    title = models.CharField(
        max_length=200,
    )

    video_url = models.URLField()

    description = models.TextField(
        blank=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    published = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class LessonImage(models.Model):
    """
    Images and diagrams belonging to a lesson.
    """

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="images",
    )

    title = models.CharField(
        max_length=200,
    )

    image = models.ImageField(
        upload_to="lesson_images/",
    )

    caption = models.TextField(
        blank=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    published = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class LessonResource(models.Model):
    """
    Downloadable resources belonging to a lesson.

    Examples:

    PDF
    Worksheet
    Notes
    Exercise
    Slides
    Project files
    """

    class ResourceType(models.TextChoices):
        PDF = "pdf", "PDF"
        NOTES = "notes", "Notes"
        WORKSHEET = "worksheet", "Worksheet"
        EXERCISE = "exercise", "Exercise"
        SLIDES = "slides", "Slides"
        PROJECT = "project", "Project Files"
        OTHER = "other", "Other"

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="resources",
    )

    title = models.CharField(
        max_length=200,
    )

    file = models.FileField(
        upload_to="lesson_resources/",
    )

    resource_type = models.CharField(
        max_length=20,
        choices=ResourceType.choices,
        default=ResourceType.PDF,
    )

    description = models.TextField(
        blank=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    published = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"
