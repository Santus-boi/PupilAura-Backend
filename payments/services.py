"""
Business logic for the payments app.

All views and templates go through these functions.
"""

import hashlib
import hmac
import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from payments.models import (
    ContentType,
    Currency,
    Gateway,
    PromoToken,
    Purchase,
    PurchaseSource,
    PurchaseStatus,
)

logger = logging.getLogger(__name__)


# ==============================================================
# CONFIG
# ==============================================================

DEFAULT_DURATION_DAYS = getattr(
    settings,
    "PAYMENT_DEFAULT_DURATION_DAYS",
    90,
)


# ==============================================================
# CONTENT LOOKUP
# ==============================================================

def _model_for(content_type):
    """
    Lazily import so this module doesn't force circular imports.
    """
    if content_type == ContentType.SUBJECT:
        from learning.models import Subject
        return Subject

    if content_type == ContentType.SCHOOL_CLASS:
        from learning.models import SchoolClass
        return SchoolClass

    if content_type == ContentType.EXAM:
        from exam_prep.models import Exam
        return Exam

    if content_type == ContentType.EXAM_RESOURCE:
        from exam_prep.models import ExamResource
        return ExamResource

    if content_type == ContentType.TECH_COURSE:
        from tech.models import TechCourse
        return TechCourse

    if content_type == ContentType.TECH_MODULE:
        from tech.models import TechModule
        return TechModule

    raise ValueError(f"Unknown content type: {content_type}")


def get_price(content_type, content_id):
    """
    Returns (amount, currency_hint, is_free).
    """
    Model = _model_for(content_type)

    try:
        item = Model.objects.get(pk=content_id)
    except Model.DoesNotExist:
        raise ValueError(f"{content_type} #{content_id} does not exist.")

    amount = getattr(item, "price", None) or Decimal("0.00")
    is_free = amount <= Decimal("0.00")

    return amount, Currency.NGN, is_free


# ==============================================================
# ACCESS CHECK
# ==============================================================

class AccessResult:
    """
    Returned by has_access(). Simple struct so templates can use it.
    """

    def __init__(self, has_access, purchase=None, days_remaining=None):
        self.has_access = has_access
        self.purchase = purchase
        self.days_remaining = days_remaining

    def __bool__(self):
        return self.has_access


def has_access(student, content_type, content_id):
    """
    Is this student currently allowed to open this item?

    Free items (price = 0) always pass.
    Paid items require an active purchase.
    """
    # Free items always accessible
    try:
        amount, _currency, is_free = get_price(content_type, content_id)
    except ValueError:
        return AccessResult(False)

    if is_free:
        return AccessResult(True)

    # Look for active paid purchase
    purchase = (
        Purchase.objects
        .filter(
            student=student,
            content_type=content_type,
            content_id=content_id,
            status=PurchaseStatus.PAID,
        )
        .order_by("-access_expires_at")
        .first()
    )

    if not purchase:
        return AccessResult(False)

    if not purchase.is_active:
        return AccessResult(False)

    return AccessResult(
        has_access=True,
        purchase=purchase,
        days_remaining=purchase.days_remaining,
    )


# ==============================================================
# CREATE CHECKOUT
# ==============================================================

def create_checkout(student, content_type, content_id, currency, gateway):
    """
    Creates a pending Purchase and returns the hosted checkout URL.

    The gateway is expected to redirect the user back to
    /payments/success/?reference=... on completion.
    """
    amount, _hint, is_free = get_price(content_type, content_id)

    if is_free:
        raise ValueError("This item is free — no checkout required.")

    # Reject if already active
    existing = has_access(student, content_type, content_id)
    if existing.has_access:
        raise ValueError("You already have access to this item.")

    purchase = Purchase.objects.create(
        student=student,
        content_type=content_type,
        content_id=content_id,
        source=PurchaseSource.PAYMENT,
        amount=amount,
        currency=currency,
        gateway=gateway,
        status=PurchaseStatus.PENDING,
    )

    try:
        if gateway == Gateway.PAYSTACK:
            return _paystack_init(purchase)
        if gateway == Gateway.STRIPE:
            return _stripe_init(purchase)
        raise ValueError(f"Unsupported gateway: {gateway}")

    except Exception as exc:
        logger.exception("Checkout creation failed for purchase %s", purchase.id)
        purchase.mark_failed(str(exc))
        raise


# ==============================================================
# PAYSTACK
# ==============================================================

PAYSTACK_INIT_URL = "https://api.paystack.co/transaction/initialize"
PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/{}"


def _paystack_init(purchase):
    """
    Initializes a Paystack transaction.

    Amount is in the smallest currency unit.
    NGN is in kobo (×100).
    """
    reference = _build_reference(purchase)
    purchase.gateway_reference = reference
    purchase.save(update_fields=["gateway_reference"])

    callback_url = (
        settings.SITE_URL
        + reverse("payments:success")
        + f"?gateway=paystack&reference={reference}"
    )

    payload = {
        "email": purchase.student.email,
        "amount": int(purchase.amount * 100),  # kobo
        "currency": purchase.currency,
        "reference": reference,
        "callback_url": callback_url,
    }

    response = requests.post(
        PAYSTACK_INIT_URL,
        json=payload,
        headers={
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        },
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("status"):
        raise ValueError(
            f"Paystack init failed: {data.get('message', 'unknown error')}"
        )

    return data["data"]["authorization_url"]


def verify_paystack(reference):
    """
    Server-to-server verification. Returns the Purchase
    if the payment was successful.
    """
    response = requests.get(
        PAYSTACK_VERIFY_URL.format(reference),
        headers={
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        },
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("status"):
        raise ValueError(
            f"Paystack verify failed: {data.get('message', 'unknown error')}"
        )

    result = data["data"]

    if result.get("status") != "success":
        raise ValueError(
            f"Payment not successful. Status: {result.get('status')}"
        )

    purchase = Purchase.objects.filter(gateway_reference=reference).first()
    if not purchase:
        raise ValueError(f"No purchase found for reference {reference}")

    if purchase.status == PurchaseStatus.PAID:
        # Already processed (idempotent)
        return purchase

    purchase.mark_paid(DEFAULT_DURATION_DAYS)
    grant_access(purchase)

    return purchase


# ==============================================================
# STRIPE
# ==============================================================

STRIPE_CHECKOUT_URL = "https://api.stripe.com/v1/checkout/sessions"


def _stripe_init(purchase):
    """
    Creates a Stripe Checkout session and returns its URL.
    """
    reference = _build_reference(purchase)
    purchase.gateway_reference = reference
    purchase.save(update_fields=["gateway_reference"])

    success_url = (
        settings.SITE_URL
        + reverse("payments:success")
        + "?gateway=stripe&reference="
        + reference
        + "&session_id={CHECKOUT_SESSION_ID}"
    )

    cancel_url = (
        settings.SITE_URL
        + reverse("payments:cancel")
        + f"?reference={reference}"
    )

    # Stripe expects amount in smallest unit (cents for USD, pence for GBP)
    unit_amount = int(purchase.amount * 100)

    payload = {
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "customer_email": purchase.student.email,
        "client_reference_id": reference,
        "line_items[0][price_data][currency]": purchase.currency.lower(),
        "line_items[0][price_data][unit_amount]": unit_amount,
        "line_items[0][price_data][product_data][name]": (
            f"PupilAura — {purchase.get_content_type_display()}"
        ),
        "line_items[0][quantity]": 1,
    }

    response = requests.post(
        STRIPE_CHECKOUT_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}",
        },
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    if "url" not in data:
        raise ValueError(f"Stripe init failed: {data}")

    return data["url"]


def verify_stripe(session_id):
    """
    Called from the success page after Stripe redirects back.
    Confirms the session is paid and marks the purchase.
    """
    response = requests.get(
        f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
        headers={
            "Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}",
        },
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()

    if data.get("payment_status") != "paid":
        raise ValueError(
            f"Payment not complete. Status: {data.get('payment_status')}"
        )

    reference = data.get("client_reference_id", "")
    purchase = Purchase.objects.filter(gateway_reference=reference).first()
    if not purchase:
        raise ValueError(f"No purchase found for reference {reference}")

    if purchase.status == PurchaseStatus.PAID:
        return purchase

    purchase.mark_paid(DEFAULT_DURATION_DAYS)
    grant_access(purchase)

    return purchase


# ==============================================================
# TOKEN REDEMPTION
# ==============================================================

def redeem_token(student, code, content_type, content_id):
    """
    Redeem a promo token for the given content.

    Rules:
        - token must belong to this student
        - token must not be used
        - token must not be expired
        - if token has max_item_price, the item price must be <= it

    Returns the resulting Purchase.
    """
    code = (code or "").strip().upper()

    if not code:
        raise ValueError("Enter a valid promo code.")

    try:
        token = PromoToken.objects.get(
            code=code,
            student=student,
        )
    except PromoToken.DoesNotExist:
        raise ValueError("This promo code is not valid for your account.")

    if not token.is_valid:
        raise ValueError("This promo code has already been used or expired.")

    amount, _currency, _is_free = get_price(content_type, content_id)

    if token.max_item_price is not None and amount > token.max_item_price:
        raise ValueError(
            "This item is not eligible for this promo code."
        )

    existing = has_access(student, content_type, content_id)
    if existing.has_access:
        raise ValueError("You already have access to this item.")

    with transaction.atomic():
        purchase = token.redeem(content_type, content_id, amount=amount)
        purchase.mark_paid(DEFAULT_DURATION_DAYS)
        grant_access(purchase)

    return purchase


# ==============================================================
# GRANT ACCESS
# ==============================================================

def grant_access(purchase):
    """
    Called after payment is confirmed (or token redeemed).

    Creates an Enrollment (school) or TechEnrollment (tech)
    so the student sees the item in their dashboard.

    Safe to call twice — enrollment models use unique constraints.
    """
    if purchase.content_type == ContentType.SUBJECT:
        _grant_subject(purchase)

    elif purchase.content_type == ContentType.TECH_COURSE:
        _grant_tech_course(purchase)

    elif purchase.content_type == ContentType.SCHOOL_CLASS:
        # Unlocks all subjects in that class — no enrollment row.
        pass

    elif purchase.content_type in (
        ContentType.EXAM,
        ContentType.EXAM_RESOURCE,
        ContentType.TECH_MODULE,
    ):
        # These unlock within their own pages —
        # no separate enrollment model needed.
        pass


def _grant_subject(purchase):
    from accounts.models import StudentProfile
    from enrollments.models import Enrollment
    from learning.models import Subject

    try:
        subject = Subject.objects.get(pk=purchase.content_id)
    except Subject.DoesNotExist:
        logger.warning("Subject %s not found for purchase %s",
                       purchase.content_id, purchase.id)
        return

    try:
        profile = StudentProfile.objects.get(user=purchase.student)
    except StudentProfile.DoesNotExist:
        logger.warning(
            "No StudentProfile for %s — cannot enroll",
            purchase.student.email,
        )
        return

    Enrollment.objects.get_or_create(
        student=profile,
        subject=subject,
    )


def _grant_tech_course(purchase):
    from tech.models import TechCourse, TechEnrollment

    try:
        course = TechCourse.objects.get(pk=purchase.content_id)
    except TechCourse.DoesNotExist:
        logger.warning("TechCourse %s not found for purchase %s",
                       purchase.content_id, purchase.id)
        return

    TechEnrollment.objects.get_or_create(
        student=purchase.student,
        course=course,
    )


# ==============================================================
# WEBHOOK SIGNATURE VERIFICATION
# ==============================================================

def verify_paystack_signature(raw_body, signature_header):
    """
    Paystack uses HMAC-SHA512 of the raw body with your secret key.
    """
    if not signature_header:
        return False

    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)


def verify_stripe_signature(raw_body, signature_header):
    """
    Stripe uses a t=timestamp,v1=signature format.
    We use the stripe library to verify.
    """
    try:
        import stripe
    except ImportError:
        logger.error("stripe library not installed")
        return False

    try:
        stripe.Webhook.construct_event(
            payload=raw_body,
            sig_header=signature_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
        return True
    except Exception:
        return False


# ==============================================================
# HELPERS
# ==============================================================

def _build_reference(purchase):
    """
    Unique, human-readable gateway reference.
    """
    return f"PA-{purchase.public_id.hex[:16]}"