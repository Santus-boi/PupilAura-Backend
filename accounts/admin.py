from django.contrib import admin
from .models import User, StudentProfile, TeacherProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "role",
        "is_staff",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "email",
        "phone_number",
    )

    ordering = ("-date_joined",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "education_level",
        "school",
        "class_name",
    )

    search_fields = (
        "user__email",
        "school",
        "class_name",
    )

    list_filter = (
        "education_level",
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "display_name",
        "specialization",
        "experience",
    )

    search_fields = (
        "user__email",
        "display_name",
        "specialization",
    )

    list_filter = (
        "specialization",
    )