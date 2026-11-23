from django.urls import path

from payments import views

app_name = "payments"

urlpatterns = [
    path(
        "checkout/<str:content_type>/<int:content_id>/",
        views.checkout,
        name="checkout",
    ),
    path(
        "redeem/",
        views.redeem,
        name="redeem",
    ),
    path(
        "success/",
        views.success,
        name="success",
    ),
    path(
        "cancel/",
        views.cancel,
        name="cancel",
    ),
    path(
        "webhook/paystack/",
        views.paystack_webhook,
        name="paystack_webhook",
    ),
    path(
        "webhook/stripe/",
        views.stripe_webhook,
        name="stripe_webhook",
    ),
    path(
    "manual-transfer/<str:content_type>/<int:content_id>/",
    views.manual_transfer,
    name="manual_transfer",
    ),
]