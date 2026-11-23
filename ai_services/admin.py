from django.contrib import admin

from .models import AICallLog


@admin.register(AICallLog)
class AICallLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "feature",
        "user",
        "provider",
        "model",
        "success",
        "cost_estimate",
        "duration_ms",
    )
    list_filter = ("feature", "provider", "success", "created_at")
    search_fields = ("user__email", "model", "error_message")
    readonly_fields = (
        "id",
        "user",
        "feature",
        "provider",
        "model",
        "prompt_tokens",
        "completion_tokens",
        "cost_estimate",
        "success",
        "error_message",
        "duration_ms",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser