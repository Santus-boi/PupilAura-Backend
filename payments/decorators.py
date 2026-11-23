"""
View decorators for content gating.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from payments.models import ContentType
from payments.services import has_access


def requires_purchase(content_type, id_kwarg):
    """
    Decorator that checks the logged-in student has access
    to the content identified by `id_kwarg` in the view's kwargs.

    Usage:

        @requires_purchase(ContentType.SUBJECT, "subject_id")
        def subject_detail(request, subject_id):
            ...

    If the student has no access, redirects to checkout.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            content_id = kwargs.get(id_kwarg) or args[0]

            access = has_access(request.user, content_type, content_id)
            if access.has_access:
                return view_func(request, *args, **kwargs)

            return redirect(
                "payments:checkout",
                content_type=content_type,
                content_id=content_id,
            )
        return _wrapped
    return decorator