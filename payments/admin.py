from django.contrib import admin
from django.utils import timezone

from payments.models import (
    PromoToken,
    Purchase,
    PurchaseStatus,
    WebhookEvent,
)
from payments.services import grant_access


# ==============================================================
# PURCHASE
# ==============================================================

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "content_type",
        "content_id",
        "status",
        "amount",
        "currency",
        "source",
        "access_expires_at",
        "created_at",
    )

    list_filter = (
        "status",
        "content_type",
        "source",
        "gateway",
        "currency",
    )

    search_fields = (
        "student__email",
        "gateway_reference",
        "public_id",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "paid_at",
        "refunded_at",
    )

    actions = [
        "mark_as_paid",
        "mark_as_refunded",
    ]

    @admin.action(description="Mark selected as paid (90 days)")
    def mark_as_paid(self, request, queryset):
        for purchase in queryset:
            if purchase.status != PurchaseStatus.PAID:
                purchase.mark_paid(90)
                grant_access(purchase)
                self.message_user(
                    request,
                    f"Marked {purchase.id} as paid and granted access.",
                )

    @admin.action(description="Refund and revoke access immediately")
    def mark_as_refunded(self, request, queryset):
        for purchase in queryset:
            purchase.mark_refunded(revoke_access=True)
            self.message_user(
                request,
                f"Refunded {purchase.id} and revoked access.",
            )


# ==============================================================
# PROMO TOKEN
# ==============================================================

@admin.register(PromoToken)
class PromoTokenAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "student",
        "is_used",
        "used_at",
        "expires_at",
        "created_at",
    )

    list_filter = ("is_used",)
    search_fields = ("code", "student__email")

    readonly_fields = ("used_at", "created_at")

    actions = ["mark_unused"]

    @admin.action(description="Reset selected tokens to unused")
    def mark_unused(self, request, queryset):
        queryset.update(is_used=False, used_at=None)
        self.message_user(request, "Tokens reset.")


# ==============================================================
# WEBHOOK EVENT
# ==============================================================

@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):

    list_display = (
        "gateway",
        "event_id",
        "event_type",
        "reference",
        "signature_valid",
        "processed",
        "created_at",
    )

    list_filter = ("gateway", "processed", "signature_valid")
    search_fields = ("event_id", "reference")

    readonly_fields = (
        "gateway",
        "event_id",
        "event_type",
        "reference",
        "payload",
        "signature_valid",
        "created_at",
    )