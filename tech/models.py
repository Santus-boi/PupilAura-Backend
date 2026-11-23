from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# ==============================================================
# TECH CATEGORY
# ==============================================================

class TechCategory(models.Model):
    """
    A category for Tech/Digital Skills courses.

    Examples:
        Web Development
        Programming
        Cybersecurity
        Data Analysis
        Graphic Design
        Digital Marketing
    """

    name = models.CharField(
        max_length=100,
        unique=True,
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
        ordering = [
            "order",
            "name",
        ]

    def __str__(self):
        return self.name


# ==============================================================
# TECH COURSE
# ==============================================================

class TechCourse(models.Model):
    """
    A completely independent Tech/Digital Skills course.

    This course does NOT belong to:
        SchoolClass
        Subject
        Term
        Week
        EducationLevel

    Anyone can learn a TechCourse.
    """

    category = models.ForeignKey(
        TechCategory,
        on_delete=models.PROTECT,
        related_name="courses",
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    thumbnail = models.ImageField(
        upload_to="tech_course_thumbnails/",
        blank=True,
        null=True,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
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
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return self.title


# ==============================================================
# TECH MODULE
# ==============================================================

class TechModule(models.Model):
    """
    A section/module inside a TechCourse.

    Example:

        Python Programming
            ├── Module 1 - Python Fundamentals
            ├── Module 2 - Conditions and Loops
            ├── Module 3 - Lists and Dictionaries
            └── Module 4 - Object-Oriented Programming
    """

    course = models.ForeignKey(
        TechCourse,
        on_delete=models.CASCADE,
        related_name="modules",
    )

    title = models.CharField(
        max_length=200,
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
        ordering = [
            "order",
            "id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "course",
                    "order",
                ],
                name="unique_tech_module_order_per_course",
            )
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# ==============================================================
# TECH LESSON
# ==============================================================

class TechLesson(models.Model):
    """
    A lesson inside a TechCourse module.

    Tech lessons are independent from the School Curriculum.
    """

    module = models.ForeignKey(
        TechModule,
        on_delete=models.CASCADE,
        related_name="lessons",
    )

    title = models.CharField(
        max_length=200,
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

    # Main lesson content
    content = models.TextField(
        blank=True,
    )

    # Practical exercise
    practical = models.TextField(
        blank=True,
    )

    # Project instructions
    project = models.TextField(
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
        ordering = [
            "order",
            "id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "module",
                    "order",
                ],
                name="unique_tech_lesson_order_per_module",
            )
        ]

    def clean(self):
        if not self.module_id:
            raise ValidationError(
                "A tech lesson must belong to a module."
            )

    @property
    def course(self):
        if not self.module_id:
            return None

        return self.module.course

    def __str__(self):
        return (
            f"{self.module.course.title} - "
            f"{self.title}"
        )


# ==============================================================
# TECH LESSON VIDEO
# ==============================================================

class TechLessonVideo(models.Model):
    """
    Videos belonging to a TechLesson.
    """

    lesson = models.ForeignKey(
        TechLesson,
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
        ordering = [
            "order",
            "id",
        ]

    def __str__(self):
        return (
            f"{self.lesson.title} - "
            f"{self.title}"
        )


# ==============================================================
# TECH LESSON IMAGE
# ==============================================================

class TechLessonImage(models.Model):
    """
    Images and diagrams belonging to a TechLesson.
    """

    lesson = models.ForeignKey(
        TechLesson,
        on_delete=models.CASCADE,
        related_name="images",
    )

    title = models.CharField(
        max_length=200,
    )

    image = models.ImageField(
        upload_to="tech_lesson_images/",
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
        ordering = [
            "order",
            "id",
        ]

    def __str__(self):
        return (
            f"{self.lesson.title} - "
            f"{self.title}"
        )


# ==============================================================
# TECH LESSON RESOURCE
# ==============================================================

class TechLessonResource(models.Model):
    """
    Downloadable resources belonging to a TechLesson.

    Examples:
        PDF
        Notes
        Worksheet
        Slides
        Project files
        Source code
    """

    lesson = models.ForeignKey(
        TechLesson,
        on_delete=models.CASCADE,
        related_name="resources",
    )

    title = models.CharField(
        max_length=200,
    )

    file = models.FileField(
        upload_to="tech_lesson_resources/",
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
        ordering = [
            "order",
            "id",
        ]

    def __str__(self):
        return (
            f"{self.lesson.title} - "
            f"{self.title}"
        )


# ==============================================================
# TECH ENROLLMENT
# ==============================================================

class TechEnrollment(models.Model):
    """
    Enrolls a student/user into a TechCourse.

    This is completely independent from the school
    Enrollment model.
    """

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tech_enrollments",
    )

    course = models.ForeignKey(
        TechCourse,
        on_delete=models.CASCADE,
        related_name="enrollments",
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
                    "course",
                ],
                name="unique_tech_student_course_enrollment",
            )
        ]

        ordering = [
            "-enrolled_at",
        ]

    def __str__(self):
        return (
            f"{self.student.email} - "
            f"{self.course.title}"
        )


# ==============================================================
# TECH LESSON PROGRESS
# ==============================================================

class TechLessonProgress(models.Model):
    """
    Stores a user's progress through TechCourse lessons.
    """

    enrollment = models.ForeignKey(
        TechEnrollment,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )

    lesson = models.ForeignKey(
        TechLesson,
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
                name="unique_tech_lesson_progress",
            )
        ]

        ordering = [
            "-completed_at",
        ]

    def clean(self):
        if not self.lesson_id or not self.enrollment_id:
            return

        lesson_course_id = (
            self.lesson.module.course_id
            if self.lesson.module_id
            else None
        )

        if (
            lesson_course_id
            and lesson_course_id
            != self.enrollment.course_id
        ):
            raise ValidationError(
                {
                    "lesson": (
                        "This lesson does not belong "
                        "to the enrolled Tech course."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.enrollment.student.email} - "
            f"{self.lesson.title}"
        )


# ============================================================
# TECH QUIZ SYSTEM
# ============================================================

class TechQuiz(models.Model):
    lesson = models.OneToOneField(
        TechLesson,
        on_delete=models.CASCADE,
        related_name="quiz",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    pass_mark = models.PositiveIntegerField(default=50)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class TechQuestion(models.Model):
    quiz = models.ForeignKey(
        TechQuiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question = models.TextField()
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "order"],
                name="unique_tech_question_order_per_quiz",
            )
        ]

    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"


class TechChoice(models.Model):
    question = models.ForeignKey(
        TechQuestion,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text


class TechQuizAttempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tech_quiz_attempts",
    )
    quiz = models.ForeignKey(
        TechQuiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    score = models.PositiveIntegerField(default=0)
    total_points = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        return (
            f"{self.student.email} - "
            f"{self.quiz.title} - "
            f"{self.percentage}%"
        )