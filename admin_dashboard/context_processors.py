from assessments.models import Answer

def admin_globals(request):
    if not request.user.is_authenticated:
        return {}

    is_admin = (
        getattr(request.user, "role", None) == "ADMIN"
        or request.user.is_staff
        or request.user.is_superuser
    )

    if not is_admin:
        return {}

    return {
        "pending_reviews": (
            Answer.objects
            .filter(reviewed=False)
            .exclude(question__question_type="objective")
            .count()
        ),
    }