"""
Payment views — checkout, callbacks, webhooks, token redemption.
"""
import uuid
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from payments.models import (
    ContentType,
    Currency,
    Gateway,
    Purchase,
    PurchaseStatus,
    WebhookEvent,
)
from payments.services import (
    create_checkout,
    get_price,
    has_access,
    redeem_token,
    verify_paystack,
    verify_paystack_signature,
    verify_stripe,
    verify_stripe_signature,
)

logger = logging.getLogger(__name__)


CONTENT_TYPE_LABELS = {
    ContentType.SUBJECT: "Subject",
    ContentType.SCHOOL_CLASS: "School Class",
    ContentType.EXAM: "Examination",
    ContentType.EXAM_RESOURCE: "Exam Resource",
    ContentType.TECH_COURSE: "Tech Course",
    ContentType.TECH_MODULE: "Tech Module",
}


# ==============================================================
# CHECKOUT
# ==============================================================

@login_required
def checkout(request, content_type, content_id):
    """
    Shows the checkout page.

    GET  — render the checkout form.
    POST — create gateway session and redirect to hosted page.
    """
    try:
        amount, currency, is_free = get_price(content_type, content_id)
    except ValueError:
        messages.error(request, "This item could not be found.")
        return redirect("student_dashboard")

    if is_free:
        messages.info(request, "This item is free — no purchase needed.")
        return redirect("student_dashboard")

    if request.method == "POST":
        selected_currency = request.POST.get("currency", Currency.NGN)
        selected_gateway = request.POST.get("gateway", Gateway.PAYSTACK)

        # Simple guard: Paystack only accepts NGN
        if selected_gateway == Gateway.PAYSTACK:
            selected_currency = Currency.NGN

        # Stripe doesn't support NGN
        if selected_gateway == Gateway.STRIPE and selected_currency == Currency.NGN:
            selected_currency = Currency.USD

        try:
            redirect_url = create_checkout(
                request.user,
                content_type,
                content_id,
                selected_currency,
                selected_gateway,
            )
            return redirect(redirect_url)
        except Exception as exc:
            logger.exception("Checkout error")
            messages.error(request, f"Payment could not be started: {exc}")
            return redirect(request.path)

    context = {
        "content_type": content_type,
        "content_id": content_id,
        "content_label": CONTENT_TYPE_LABELS.get(content_type, "Content"),
        "amount": amount,
        "currency": currency,
        "nav_active": "courses",
    }
    return render(request, "payments/checkout.html", context)


# ==============================================================
# TOKEN REDEMPTION
# ==============================================================

@login_required
def redeem(request):
    """
    POST-only. Redeems a promo code.
    """
    if request.method != "POST":
        return redirect("payments:checkout_choose")

    code = request.POST.get("code", "").strip()
    content_type = request.POST.get("content_type", "")
    content_id = request.POST.get("content_id", "")
    next_url = request.POST.get("next", "") or "student_dashboard"

    if not (code and content_type and content_id):
        messages.error(request, "Please enter a valid promo code.")
        return redirect(next_url)

    try:
        content_id = int(content_id)
    except (TypeError, ValueError):
        messages.error(request, "Invalid content reference.")
        return redirect(next_url)

    try:
        purchase = redeem_token(
            request.user,
            code,
            content_type,
            content_id,
        )
        messages.success(
            request,
            f"Promo code applied! You have 90 days of access.",
        )
        return redirect(next_url)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect(next_url)
    except Exception:
        logger.exception("Promo redemption error")
        messages.error(request, "Something went wrong. Please try again.")
        return redirect(next_url)


# ==============================================================
# SUCCESS / CANCEL
# ==============================================================

@login_required
def success(request):
    """
    Gateway redirects here after checkout.

    We verify server-side and, on success, show a confirmation page.
    """
    gateway = request.GET.get("gateway", "").lower()
    reference = request.GET.get("reference", "")
    session_id = request.GET.get("session_id", "")

    purchase = None

    try:
        if gateway == "paystack" and reference:
            purchase = verify_paystack(reference)

        elif gateway == "stripe" and session_id:
            purchase = verify_stripe(session_id)

    except Exception as exc:
        logger.exception("Payment verification failed")
        messages.error(request, f"Payment could not be verified: {exc}")
        return redirect("payments:cancel")

    if not purchase:
        messages.info(request, "No payment details found.")
        return redirect("student_dashboard")

    context = {
        "purchase": purchase,
    }
    return render(request, "payments/success.html", context)


@login_required
def cancel(request):
    reference = request.GET.get("reference", "")
    purchase = None

    if reference:
        purchase = Purchase.objects.filter(
            gateway_reference=reference,
            student=request.user,
        ).first()

        if purchase and purchase.status == PurchaseStatus.PENDING:
            purchase.mark_failed("Cancelled by user.")

    return render(request, "payments/cancel.html", {"purchase": purchase})


# ==============================================================
# WEBHOOKS
# ==============================================================

@csrf_exempt
def paystack_webhook(request):
    """
    Paystack server webhook. Verified via HMAC-SHA512.
    """
    if request.method != "POST":
        return JsonResponse({"status": "method-not-allowed"}, status=405)

    raw_body = request.body
    signature = request.headers.get("x-paystack-signature", "")

    valid = verify_paystack_signature(raw_body, signature)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        payload = {}

    event_id = str(payload.get("id", "")) or str(payload.get("data", {}).get("id", ""))
    event_type = payload.get("event", "")
    data = payload.get("data", {}) or {}
    reference = data.get("reference", "")

    event, _created = WebhookEvent.objects.get_or_create(
        gateway=WebhookEvent.Gateway.PAYSTACK,
        event_id=event_id or reference or "unknown",
        defaults={
            "event_type": event_type,
            "reference": reference,
            "payload": payload,
            "signature_valid": valid,
        },
    )

    if not valid:
        return JsonResponse({"status": "invalid signature"}, status=401)

    if event.processed:
        return JsonResponse({"status": "already processed"})

    try:
        if event_type == "charge.success":
            verify_paystack(reference)
            event.processed = True
            event.save(update_fields=["processed"])
    except Exception as exc:
        logger.exception("Paystack webhook failed")
        event.error = str(exc)
        event.save(update_fields=["error"])
        return JsonResponse({"status": "error"}, status=500)

    return JsonResponse({"status": "ok"})


@csrf_exempt
def stripe_webhook(request):
    """
    Stripe server webhook. Verified via Stripe signature.
    """
    if request.method != "POST":
        return JsonResponse({"status": "method-not-allowed"}, status=405)

    raw_body = request.body
    signature = request.headers.get("stripe-signature", "")

    valid = verify_stripe_signature(raw_body, signature)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        payload = {}

    event_id = payload.get("id", "")
    event_type = payload.get("type", "")

    event, _created = WebhookEvent.objects.get_or_create(
        gateway=WebhookEvent.Gateway.STRIPE,
        event_id=event_id or "unknown",
        defaults={
            "event_type": event_type,
            "payload": payload,
            "signature_valid": valid,
        },
    )

    if not valid:
        return JsonResponse({"status": "invalid signature"}, status=401)

    if event.processed:
        return JsonResponse({"status": "already processed"})

    try:
        if event_type == "checkout.session.completed":
            obj = payload.get("data", {}).get("object", {})
            session_id = obj.get("id", "")
            if session_id:
                verify_stripe(session_id)
                event.processed = True
                event.save(update_fields=["processed"])
    except Exception as exc:
        logger.exception("Stripe webhook failed")
        event.error = str(exc)
        event.save(update_fields=["error"])
        return JsonResponse({"status": "error"}, status=500)

    return JsonResponse({"status": "ok"})

import uuid

@login_required
def manual_transfer(request, content_type, content_id):
    """
    Records a manual bank-transfer intent for admin approval.
    """
    from payments.models import PurchaseSource

    if request.method != "POST":
        return redirect("payments:checkout", content_type=content_type, content_id=content_id)

    try:
        amount, _currency, is_free = get_price(content_type, content_id)
    except ValueError:
        messages.error(request, "This item could not be found.")
        return redirect("student_dashboard")

    if is_free:
        messages.info(request, "This item is free — no payment needed.")
        return redirect("student_dashboard")

    existing = has_access(request.user, content_type, content_id)
    if existing.has_access:
        messages.info(request, "You already have access to this item.")
        return redirect("student_dashboard")

    # Reuse existing pending manual purchase if there is one
    reference = f"MANUAL-{uuid.uuid4().hex[:12].upper()}"

    purchase, created = Purchase.objects.get_or_create(
        student=request.user,
        content_type=content_type,
        content_id=content_id,
        gateway=Gateway.MANUAL,
        status=PurchaseStatus.PENDING,
        defaults={
            "source": PurchaseSource.PAYMENT,
            "amount": amount,
            "currency": Currency.NGN,
            "gateway_reference": reference,
        },
    )

    return render(request, "payments/manual_pending.html", {
        "purchase": purchase,
        "reference": purchase.gateway_reference,
        "amount": amount,
        "content_label": CONTENT_TYPE_LABELS.get(content_type, "Content"),
        "content_id": content_id,
        "content_type": content_type,
    })