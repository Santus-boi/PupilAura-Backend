"""
PupilAura payments app.

Models:

    Purchase        — one row per unlocked item (paid OR via token)
    PromoToken      — single-use promotional unlock code
    WebhookEvent    — raw gateway webhook events, for audit + idempotency
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


# ==============================================================
# ENUMS
# ==============================================================

class ContentType(models.TextChoices):
    SUBJECT = "subject", "Subject"
    SCHOOL_CLASS = "school_class", "School Class"
    EXAM = "exam", "Examination"
    EXAM_RESOURCE = "exam_resource", "Exam Resource"
    TECH_COURSE = "tech_course", "Tech Course"
    TECH_MODULE = "tech_module", "Tech Module"


class PurchaseStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"
    EXPIRED = "expired", "Expired"


class PurchaseSource(models.TextChoices):
    PAYMENT = "payment", "Payment"
    PROMO_TOKEN = "promo_token", "Promo Token"
    ADMIN_GRANT = "admin_grant", "Admin Grant"


class Gateway(models.TextChoices):
    PAYSTACK = "paystack", "Paystack"
    STRIPE = "stripe", "Stripe"
    MANUAL = "manual", "Manual Bank Transfer"


class Currency(models.TextChoices):
    NGN = "NGN", "Nigerian Naira"
    USD = "USD", "US Dollar"
    GBP = "GBP", "British Pound"
    EUR = "EUR", "Euro"


# ==============================================================
# PURCHASE
# ==============================================================

class Purchase(models.Model):
    """
    A single unlock grant for one specific piece of content.

    Created by:

        - Successful Paystack / Stripe payment
        - Successful PromoToken redemption
        - Admin manual grant (for support / giveaways)

    Access is time-limited: `access_expires_at` determines
    whether the student can still open the content.

    Never deleted. Set `status=refunded` and
    `access_expires_at=timezone.now()` to revoke.
    """

    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchases",
    )

    content_type = models.CharField(
        max_length=30,
        choices=ContentType.choices,
    )

    content_id = models.PositiveIntegerField(
        db_index=True,
    )

    source = models.CharField(
        max_length=20,
        choices=PurchaseSource.choices,
        default=PurchaseSource.PAYMENT,
    )

    status = models.CharField(
        max_length=20,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.PENDING,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.NGN,
    )

    gateway = models.CharField(
        max_length=20,
        choices=Gateway.choices,
        blank=True,
    )

    gateway_reference = models.CharField(
        max_length=200,
        blank=True,
        db_index=True,
    )

    promo_token = models.ForeignKey(
        "payments.PromoToken",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchases",
    )

    access_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["student", "content_type", "content_id"],
                name="purchase_access_idx",
            ),
            models.Index(
                fields=["status", "access_expires_at"],
                name="purchase_status_expiry_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.student.email} - "
            f"{self.get_content_type_display()} #{self.content_id} - "
            f"{self.get_status_display()}"
        )

    # ----------------------------------------------------------
    # STATE HELPERS
    # ----------------------------------------------------------

    @property
    def is_paid(self):
        return self.status == PurchaseStatus.PAID

    @property
    def is_active(self):
        """
        Paid and not expired.
        """
        if self.status != PurchaseStatus.PAID:
            return False

        if self.access_expires_at is None:
            return True

        return self.access_expires_at > timezone.now()

    @property
    def days_remaining(self):
        """
        Rounded-up days until expiry. None if lifetime or not active.
        """
        if not self.access_expires_at:
            return None

        delta = self.access_expires_at - timezone.now()

        if delta.total_seconds() <= 0:
            return 0

        return max(1, int(delta.total_seconds() // 86400) + (
            1 if delta.total_seconds() % 86400 else 0
        ))

    # ----------------------------------------------------------
    # STATE TRANSITIONS
    # ----------------------------------------------------------

    def mark_paid(self, duration_days):
        """
        Called from webhook handlers and admin actions after
        payment verification has succeeded.
        """
        self.status = PurchaseStatus.PAID
        self.paid_at = timezone.now()
        self.access_expires_at = (
            timezone.now() + timezone.timedelta(days=duration_days)
        )
        self.save(
            update_fields=[
                "status",
                "paid_at",
                "access_expires_at",
                "gateway_reference",
            ]
        )

    def mark_refunded(self, revoke_access=True):
        """
        Called when refund is confirmed via gateway dashboard.
        Revokes access immediately by setting expiry to now.
        """
        self.status = PurchaseStatus.REFUNDED
        self.refunded_at = timezone.now()

        if revoke_access:
            self.access_expires_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "refunded_at",
                "access_expires_at",
            ]
        )

    def mark_failed(self, reason=""):
        self.status = PurchaseStatus.FAILED
        if reason:
            self.notes = f"{self.notes}\n{reason}".strip()
        self.save(update_fields=["status", "notes"])


# ==============================================================
# PROMO TOKEN
# ==============================================================

class PromoToken(models.Model):
    """
    A single-use promotional code.

    Each token:

        - belongs to a specific student (so it can't be shared)
        - can only be redeemed ONCE (by that student)
        - unlocks ANY ONE item of the student's choosing (scope B)
        - grants 90 days of access (same as a paid purchase)

    Created by an admin. The `code` is auto-generated and
    formatted to be readable (e.g. `PUPIL-8K3M-2F9X`).
    """

    code = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="promo_tokens",
    )

    is_used = models.BooleanField(
        default=False,
        db_index=True,
    )

    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Optional cap: if set, only allows redeem for items
    # whose price is <= this. Empty means no cap.
    max_item_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Leave blank for no expiry.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    note = models.CharField(
        max_length=200,
        blank=True,
        help_text="Internal note — not shown to the student.",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.student.email}"

    @property
    def is_valid(self):
        if self.is_used:
            return False

        if self.expires_at and self.expires_at <= timezone.now():
            return False

        return True

    def redeem(self, content_type, content_id, amount=0):
        """
        Mark the token as used and return the created Purchase.

        The caller is responsible for wrapping in a transaction
        and calling grant_access() afterwards.
        """
        if not self.is_valid:
            raise ValueError("Token is not valid.")

        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=["is_used", "used_at"])

        purchase = Purchase.objects.create(
            student=self.student,
            content_type=content_type,
            content_id=content_id,
            source=PurchaseSource.PROMO_TOKEN,
            amount=amount,
            currency=Currency.NGN,
            promo_token=self,
        )

        return purchase


# ==============================================================
# WEBHOOK EVENT
# ==============================================================

class WebhookEvent(models.Model):
    """
    Raw gateway webhook payloads. Used for:

        - Idempotency (don't re-process the same event twice)
        - Audit trail
        - Debugging failed payments
    """

    class Gateway(models.TextChoices):
        PAYSTACK = "paystack", "Paystack"
        STRIPE = "stripe", "Stripe"

    gateway = models.CharField(
        max_length=20,
        choices=Gateway.choices,
    )

    event_id = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Gateway's unique event ID.",
    )

    event_type = models.CharField(
        max_length=100,
        blank=True,
    )

    reference = models.CharField(
        max_length=200,
        blank=True,
        db_index=True,
    )

    payload = models.JSONField(
        default=dict,
        blank=True,
    )

    signature_valid = models.BooleanField(
        default=False,
    )

    processed = models.BooleanField(
        default=False,
    )

    error = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["gateway", "event_id"],
                name="unique_webhook_per_gateway",
            )
        ]

    def __str__(self):
        return f"{self.gateway} - {self.event_id}"

