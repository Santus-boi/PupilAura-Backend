
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from community.models import CommunityGroup, GroupMembership

from .views import admin_required


# ============================================================
# COMMUNITY OVERVIEW
# ============================================================

@admin_required
def community(request):
    groups = (
        CommunityGroup.objects
        .select_related(
            "created_by",
            "reviewed_by",
            "school_class",
            "exam",
            "exam_subject",
            "tech_course",
        )
        .annotate(
            member_count=Count(
                "memberships",
                filter=Q(
                    memberships__status=GroupMembership.Status.ACTIVE
                ),
                distinct=True,
            ),
            pending_member_count=Count(
                "memberships",
                filter=Q(
                    memberships__status=GroupMembership.Status.PENDING
                ),
                distinct=True,
            ),
        )
        .order_by("-created_at")
    )

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    type_filter = request.GET.get("type", "").strip()

    valid_statuses = [
        choice[0] for choice in CommunityGroup.ReviewStatus.choices
    ]

    valid_types = [
        choice[0] for choice in CommunityGroup.GroupType.choices
    ]

    if search_query:
        groups = groups.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(created_by__email__icontains=search_query)
        )

    if status_filter in valid_statuses:
        groups = groups.filter(review_status=status_filter)

    if type_filter in valid_types:
        groups = groups.filter(group_type=type_filter)

    context = {
        "groups": groups,

        # Group statistics
        "total_groups": CommunityGroup.objects.count(),
        "pending_groups": CommunityGroup.objects.filter(
            review_status=CommunityGroup.ReviewStatus.PENDING
        ).count(),
        "approved_groups": CommunityGroup.objects.filter(
            review_status=CommunityGroup.ReviewStatus.APPROVED
        ).count(),
        "rejected_groups": CommunityGroup.objects.filter(
            review_status=CommunityGroup.ReviewStatus.REJECTED
        ).count(),
        "suspended_groups": CommunityGroup.objects.filter(
            review_status=CommunityGroup.ReviewStatus.SUSPENDED
        ).count(),

        # Membership statistics
        "active_memberships": GroupMembership.objects.filter(
            status=GroupMembership.Status.ACTIVE
        ).count(),
        "pending_memberships": GroupMembership.objects.filter(
            status=GroupMembership.Status.PENDING
        ).count(),
        "total_caretakers": GroupMembership.objects.filter(
            role=GroupMembership.Role.CARETAKER,
            status=GroupMembership.Status.ACTIVE,
        ).count(),

        # Filters
        "search_query": search_query,
        "status_filter": status_filter,
        "type_filter": type_filter,
        "review_statuses": CommunityGroup.ReviewStatus.choices,
        "group_types": CommunityGroup.GroupType.choices,

        "nav_active": "community",
    }

    return render(
        request,
        "admin_dashboard/community.html",
        context,
    )


# ============================================================
# COMMUNITY GROUP DETAIL
# ============================================================

@admin_required
def community_group_detail(request, group_id):
    group = get_object_or_404(
        CommunityGroup.objects.select_related(
            "created_by",
            "reviewed_by",
            "school_class",
            "exam",
            "exam_subject",
            "tech_course",
        ),
        pk=group_id,
    )

    memberships = (
        GroupMembership.objects
        .filter(group=group)
        .select_related("user", "reviewed_by")
        .order_by("-joined_at")
    )

    pending_memberships = memberships.filter(
        status=GroupMembership.Status.PENDING,
        role=GroupMembership.Role.MEMBER,
    )

    active_memberships = memberships.filter(
        status=GroupMembership.Status.ACTIVE,
    )

    caretakers = active_memberships.filter(
        role=GroupMembership.Role.CARETAKER,
    )

    context = {
        "group": group,
        "memberships": memberships,
        "pending_memberships": pending_memberships,
        "active_memberships": active_memberships,
        "caretakers": caretakers,

        "total_members": active_memberships.count(),
        "pending_count": pending_memberships.count(),
        "caretaker_count": caretakers.count(),

        "rejected_count": memberships.filter(
            status=GroupMembership.Status.REJECTED
        ).count(),

        "banned_count": memberships.filter(
            status=GroupMembership.Status.BANNED
        ).count(),

        "review_statuses": CommunityGroup.ReviewStatus.choices,
        "nav_active": "community",
    }

    return render(
        request,
        "admin_dashboard/community_group_detail.html",
        context,
    )


# ============================================================
# GROUP REVIEW ACTIONS
# ============================================================

@admin_required
@require_POST
def community_group_action(request, group_id, action):
    group = get_object_or_404(
        CommunityGroup,
        pk=group_id,
    )

    actions = {
        "approve": CommunityGroup.ReviewStatus.APPROVED,
        "reject": CommunityGroup.ReviewStatus.REJECTED,
        "suspend": CommunityGroup.ReviewStatus.SUSPENDED,
    }

    new_status = actions.get(action)

    if not new_status:
        messages.error(request, "Invalid group action.")

        return redirect(
            "admin_dashboard:community_group_detail",
            group_id=group.pk,
        )

    group.review_status = new_status
    group.reviewed_by = request.user
    group.reviewed_at = timezone.now()
    group.review_notes = request.POST.get(
        "review_notes",
        "",
    ).strip()

    group.save(
        update_fields=[
            "review_status",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"Group '{group.name}' status updated to "
        f"{group.get_review_status_display()}.",
    )

    return redirect(
        "admin_dashboard:community_group_detail",
        group_id=group.pk,
    )


# ============================================================
# MEMBERSHIP ACTIONS
# ============================================================

@admin_required
@require_POST
def community_membership_action(
    request,
    group_id,
    membership_id,
    action,):
    group = get_object_or_404(
        CommunityGroup,
        pk=group_id,
    )

    # Membership management is restricted to approved groups.
    if group.review_status != CommunityGroup.ReviewStatus.APPROVED:
        messages.error(
            request,
            "Memberships can only be managed in approved groups.",
        )

        return redirect(
            "admin_dashboard:community_group_detail",
            group_id=group.pk,
        )

    membership = get_object_or_404(
        GroupMembership.objects.select_related("user"),
        pk=membership_id,
        group=group,
    )

    actions = {
        "approve": (
            GroupMembership.Status.PENDING,
            GroupMembership.Status.ACTIVE,
        ),
        "reject": (
            GroupMembership.Status.PENDING,
            GroupMembership.Status.REJECTED,
        ),
        "ban": (
            GroupMembership.Status.ACTIVE,
            GroupMembership.Status.BANNED,
        ),
    }

    transition = actions.get(action)

    if not transition:
        messages.error(request, "Invalid membership action.")

    elif membership.status != transition[0]:
        messages.warning(
            request,
            "This membership can no longer receive that action.",
        )

    else:
        membership.status = transition[1]
        membership.reviewed_by = request.user
        membership.reviewed_at = timezone.now()

        membership.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "updated_at",
            ]
        )

        messages.success(
            request,
            f"Membership for {membership.user} updated successfully.",
        )

    return redirect(
        "admin_dashboard:community_group_detail",
        group_id=group.pk,
    )


# ============================================================
# CARETAKER MANAGEMENT
# ============================================================

@admin_required
@require_POST
def community_caretaker_action(
    request,
    group_id,
    membership_id,
    action,):
    group = get_object_or_404(
        CommunityGroup,
        pk=group_id,
    )

    # Caretakers can only be assigned in approved groups.
    if group.review_status != CommunityGroup.ReviewStatus.APPROVED:
        messages.error(
            request,
            "Caretakers can only be assigned in approved groups.",
        )

        return redirect(
            "admin_dashboard:community_group_detail",
            group_id=group.pk,
        )

    membership = get_object_or_404(
        GroupMembership.objects.select_related("user"),
        pk=membership_id,
        group=group,
        status=GroupMembership.Status.ACTIVE,
    )

    if action == "promote":
        if membership.role == GroupMembership.Role.CARETAKER:
            messages.warning(
                request,
                "This student is already a caretaker.",
            )
        else:
            membership.role = GroupMembership.Role.CARETAKER

            membership.save(
                update_fields=[
                    "role",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                f"{membership.user} is now a caretaker for {group.name}.",
            )

    elif action == "revoke":
        if membership.role != GroupMembership.Role.CARETAKER:
            messages.warning(
                request,
                "This student is not a caretaker.",
            )
        else:
            membership.role = GroupMembership.Role.MEMBER

            membership.save(
                update_fields=[
                    "role",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                f"Caretaker privileges removed from {membership.user}.",
            )

    else:
        messages.error(
            request,
            "Invalid caretaker action.",
        )

    return redirect(
        "admin_dashboard:community_group_detail",
        group_id=group.pk,
    )
