from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import redirect, render

from .models import User, StudentProfile


# ==============================================================
# REGISTER
# ==============================================================

def register(request):

    if request.method == "POST":

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        # ------------------------------------------------------
        # VALIDATE EMAIL
        # ------------------------------------------------------

        if not email:
            messages.error(
                request,
                "Email is required."
            )

            return render(
                request,
                "accounts/register.html"
            )

        # ------------------------------------------------------
        # VALIDATE PASSWORD
        # ------------------------------------------------------

        if not password:
            messages.error(
                request,
                "Password is required."
            )

            return render(
                request,
                "accounts/register.html"
            )

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return render(
                request,
                "accounts/register.html"
            )

        # ------------------------------------------------------
        # CHECK WHETHER EMAIL ALREADY EXISTS
        # ------------------------------------------------------

        if User.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                "An account with this email already exists."
            )

            return render(
                request,
                "accounts/register.html"
            )

        # ------------------------------------------------------
        # CREATE STUDENT ACCOUNT
        # ------------------------------------------------------

        user = User.objects.create_user(
            email=email,
            password=password,
            role=User.Role.STUDENT,
        )

        # ------------------------------------------------------
        # CREATE STUDENT PROFILE
        # ------------------------------------------------------

        StudentProfile.objects.create(
            user=user
        )

        # ------------------------------------------------------
        # LOG USER IN
        # ------------------------------------------------------

        login(
            request,
            user
        )

        messages.success(
            request,
            "Your account has been created successfully."
        )

        return redirect(
            "/student/dashboard/"
        )

    return render(
        request,
        "accounts/register.html"
    )


# ==============================================================
# LOGIN
# ==============================================================

def user_login(request):

    if request.method == "POST":

        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=email,      # ← FIXED: username= not email=
            password=password,
        )

        if user is not None:

            login(request, user)

            if user.role == User.Role.ADMIN:
                return redirect("/admin-dashboard/")

            return redirect("/student/dashboard/")

        messages.error(request, "Invalid email or password.")

    return render(request, "accounts/login.html")
#==============================================================
# LOGOUT
# ==============================================================

def user_logout(request):

    logout(request)

    return redirect(
        "/accounts/login/"
    )