from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from accounts.models import StudentProfile
from learning.models import Course

from .models import Enrollment


@login_required
def enroll(request, course_id):
    if request.user.role != "student":
        return redirect("/")

    student_profile = get_object_or_404(
        StudentProfile,
        user=request.user,
    )

    course = get_object_or_404(
        Course,
        id=course_id,
        published=True,
    )

    Enrollment.objects.get_or_create(
        student=student_profile,
        course=course,
    )

    return redirect("/student/dashboard/")