
from django.contrib import admin
from .models import CommunityGroup, GroupMembership


@admin.register(CommunityGroup)
class CommunityGroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "group_type",
        "created_by",
        "review_status",
        "created_at",
    )

    list_filter = (
        "group_type",
        "review_status",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "created_by__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "group",
        "role",
        "status",
        "reviewed_by",
        "joined_at",
    )

    list_filter = (
        "role",
        "status",
        "group__group_type",
        "joined_at",
    )

    search_fields = (
        "user__email",
        "group__name",
    )

    readonly_fields = (
        "joined_at",
        "updated_at",
        "reviewed_at",
    )

    list_select_related = (
        "user",
        "group",
        "reviewed_by",
    )

    actions = None
