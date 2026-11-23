from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# ==============================================================
# USER MANAGER
# ==============================================================

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError(
                "Users must have an email address"
            )

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email,
        password=None,
        **extra_fields
    ):

        extra_fields.setdefault(
            "is_staff",
            True
        )

        extra_fields.setdefault(
            "is_superuser",
            True
        )

        extra_fields.setdefault(
            "is_active",
            True
        )

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "Superuser must have is_staff=True."
            )

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                "Superuser must have is_superuser=True."
            )

        return self.create_user(
            email=email,
            password=password,
            **extra_fields
        )


# ==============================================================
# USER
# ==============================================================

class User(AbstractUser):

    username = None

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = UserManager()

    class Role(models.TextChoices):

        STUDENT = (
            "student",
            "Student"
        )

        ADMIN = (
            "admin",
            "Admin"
        )

    email = models.EmailField(
        unique=True
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.email


# ==============================================================
# STUDENT PROFILE
# ==============================================================

class StudentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    # ----------------------------------------------------------
    # EXISTING PROFILE FIELDS
    # ----------------------------------------------------------

    education_level = models.CharField(
        max_length=100,
        blank=True,
    )

    school = models.CharField(
        max_length=200,
        blank=True,
    )

    class_name = models.CharField(
        max_length=100,
        blank=True,
    )

    # ----------------------------------------------------------
    # REAL CURRICULUM RELATIONSHIPS
    # ----------------------------------------------------------

    curriculum_level = models.ForeignKey(
        "learning.EducationLevel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profiles",
    )

    school_class = models.ForeignKey(
        "learning.SchoolClass",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profiles",
    )

    def __str__(self):
        return (
            f"Student Profile - "
            f"{self.user.email}"
        )


# ==============================================================
# TEACHER PROFILE
# ==============================================================

class TeacherProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
    )

    display_name = models.CharField(
        max_length=150,
        blank=True,
    )

    bio = models.TextField(
        blank=True,
    )

    qualifications = models.TextField(
        blank=True,
    )

    specialization = models.CharField(
        max_length=200,
        blank=True,
    )

    subjects = models.TextField(
        blank=True,
    )

    experience = models.PositiveIntegerField(
        default=0,
    )

    def __str__(self):
        return (
            self.display_name
            or f"Teacher Profile - {self.user.email}"
        )
