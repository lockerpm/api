from django.db.models import Q

from shared.constants.members import PM_MEMBER_STATUS_CONFIRMED
from shared.utils.app import now
from cystack_models.models.users.users import User


def bump_account_revision_date(user: User = None, team=None, **team_filters):
    if team:
        # Finding all members
        team_members = team.team_members.filter(status=PM_MEMBER_STATUS_CONFIRMED)
        collection_ids = team_filters.get("collection_ids", [])
        role_name = team_filters.get("role_name", [])
        # Filter by collection ids
        if collection_ids:
            team_members = team_members.filter(
                Q(role_id__in=role_name) | Q(collections_members__collection_id__in=collection_ids)
            )

        # Get list user ids and update revision date of them
        member_user_ids = team_members.values_list('user_id', flat=True)
        User.objects.filter(user_id__in=member_user_ids).update(revision_date=now())

    elif user:
        user.revision_date = now()
        user.save()
