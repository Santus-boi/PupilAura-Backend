"""
URL configuration for config project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from student import views


urlpatterns = [
    # HOME
    path("", views.home, name="home"),

    # DJANGO ADMIN
    path("admin/", admin.site.urls, name="django_admin"),

    # AUTHENTICATION
    path("accounts/", include("accounts.urls")),

    # STUDENT
    path("student/", include("student.urls")),

    # ADMIN DASHBOARD
    path("admin-dashboard/", include("admin_dashboard.urls")),

    # ENROLLMENTS
    path("enrollments/", include("enrollments.urls")),

    # LEARNING
    path("learning/", include("learning.urls")),

    # ASSESSMENTS
    path("assessments/", include("assessments.urls")),

    # TECH
    path("student/tech/", include("tech.urls")),

    # EXAM PREP
    path("exam-prep/", include("exam_prep.urls")),

    # PAYMENTS
    path("payments/", include("payments.urls")),

    # PLAY & LEARN
    path("play-learn/", include("play_learn.urls")),

    # COMMUNITY
    path("community/", include("community.urls")),
]


# MEDIA FILES
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )