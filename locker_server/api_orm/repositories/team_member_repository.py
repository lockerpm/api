from typing import Union, Dict, Optional, List

from django.db.models import When, Q, Value, Case, IntegerField

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_user_model, get_team_member_model, get_group_member_model, \
    get_collection_member_model, get_team_model
from locker_server.api_orm.utils.revision_date import bump_account_revision_date
from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.team.team import Team
from locker_server.core.entities.user.user import User
from locker_server.core.repositories.team_member_repository import TeamMemberRepository
from locker_server.shared.constants.members import *
from locker_server.shared.constants.transactions import PLAN_TYPE_PM_FAMILY


UserORM = get_user_model()
TeamORM = get_team_model()
TeamMemberORM = get_team_member_model()
GroupMemberORM = get_group_member_model()
CollectionMemberORM = get_collection_member_model()
# PMPlanORM = get_plan_model()
# PMUserPlanORM = get_user_plan_model()
# EnterpriseMemberRoleORM = get_enterprise_member_role_model()
# EnterpriseMemberORM = get_enterprise_member_model()
# EnterpriseORM = get_enterprise_model()
ModelParser = get_model_parser()


class TeamMemberORMRepository(TeamMemberRepository):
    @staticmethod
    def _get_user_orm(user_id: int) -> Optional[UserORM]:
        try:
            return UserORM.objects.get(user_id=user_id)
        except UserORM.DoesNotExist:
            return None

    @staticmethod
    def _get_team_member_orm(team_member_id: int) -> Optional[TeamMemberORM]:
        try:
            team_member_orm = TeamMemberORM.objects.get(id=team_member_id)
            return team_member_orm
        except TeamMemberORM.DoesNotExist:
            return None

    # ------------------------ List TeamMember resource ------------------- #
    def list_members_by_user_id(self, user_id: int, **filter_params) -> List[TeamMember]:
        personal_share = filter_params.get("personal_share", True)
        members_orm = TeamMemberORM.objects.filter(
            user_id=user_id, team__personal_share=personal_share,
        ).select_related('team').select_related('user').order_by('access_time')

        status_params = filter_params.get("statuses")
        team_key_null = filter_params.get("team_key_null")
        if status_params:
            members_orm = members_orm.filter(status__in=status_params)
        if isinstance(team_key_null, bool):
            members_orm = members_orm.filter(team__key__isnull=team_key_null)
        members = []
        for member_orm in members_orm:
            members.append(ModelParser.team_parser().parse_team_member(team_member_orm=member_orm))
        return members

    def list_member_user_ids(self, team_ids: List[str], status: str = None, personal_share: bool = None) -> List[int]:
        members_orm = TeamMemberORM.objects.filter(team_id__in=team_ids)
        if status is not None:
            members_orm = members_orm.filter(status=status)
        if personal_share is not None:
            members_orm = members_orm.filter(team__personal_share=personal_share)
        return list(members_orm.values_list('user_id', flat=True))

    def list_member_by_teams(self, teams: List[Team], exclude_owner: bool = True,
                             is_added_by_group: bool = None) -> List[TeamMember]:
        order_whens = [
            When(Q(role__name=MEMBER_ROLE_OWNER, user__isnull=False), then=Value(2)),
            When(Q(role__name=MEMBER_ROLE_ADMIN, user__isnull=False), then=Value(3)),
            When(Q(role__name=MEMBER_ROLE_MEMBER, user__isnull=False), then=Value(4))
        ]
        team_ids = [team.team_id for team in teams]
        members_orm = TeamMemberORM.objects.filter(team_id__in=team_ids).annotate(
            order_field=Case(*order_whens, output_field=IntegerField(), default=Value(4))
        ).order_by("order_field").select_related('team').select_related('user').select_related('role')
        if exclude_owner:
            members_orm = members_orm.exclude(role_id=MEMBER_ROLE_OWNER)
        if is_added_by_group is not None:
            members_orm = members_orm.filter(is_added_by_group=is_added_by_group)
        return [
            ModelParser.team_parser().parse_team_member(team_member_orm=member_orm) for member_orm in members_orm
        ]

    def list_member_user_ids_by_teams(self, teams: List[Team], status: str = None,
                                      personal_share: bool = None) -> List[int]:
        team_ids = [team.team_id for team in teams]
        return self.list_member_user_ids(team_ids=team_ids, status=status, personal_share=personal_share)

    def list_group_member_roles(self, team_member: TeamMember) -> List[str]:
        return list(GroupMemberORM.objects.filter(
            member_id=team_member.team_member_id
        ).values_list('group__role_id', flat=True))

    def list_member_collection_ids(self, team_member_id: int) -> List[str]:
        return list(
            CollectionMemberORM.objects.filter(member_id=team_member_id).values_list('collection_id', flat=True)
        )

    def list_team_ids_owner_family_plan(self, user_id: int) -> List[str]:
        team_ids = TeamMemberORM.objects.filter(user_id=user_id, status=PM_MEMBER_STATUS_CONFIRMED).filter(
            user__pm_user_plan__pm_plan__alias=PLAN_TYPE_PM_FAMILY,
            role_id=MEMBER_ROLE_OWNER,
            is_default=True, is_primary=True
        ).values_list('team_id', flat=True)
        return team_ids

    # ------------------------ Get TeamMember resource --------------------- #
    def get_team_member_by_id(self, team_member_id: int) -> Optional[TeamMember]:
        team_member_orm = self._get_team_member_orm(team_member_id=team_member_id)
        if not team_member_orm:
            return None
        return ModelParser.team_parser().parse_team_member(team_member_orm=team_member_orm)

    def get_user_team_member(self, user_id: int, team_id: str) -> Optional[TeamMember]:
        try:
            team_member_orm = TeamMemberORM.objects.get(user_id=user_id, team_id=team_id)
            return ModelParser.team_parser().parse_team_member(team_member_orm=team_member_orm)
        except TeamMemberORM.DoesNotExist:
            return None

    def get_primary_member(self, team_id: str) -> Optional[TeamMember]:
        try:
            team_member_orm = TeamMemberORM.objects.get(team_id=team_id, is_primary=True)
            return ModelParser.team_parser().parse_team_member(team_member_orm=team_member_orm)
        except TeamMemberORM.DoesNotExist:
            return None

    def get_role_notify_dict(self, team_id: str, user_id: int) -> Dict:
        try:
            team_member_orm = TeamMemberORM.objects.get(user_id=user_id, team_id=team_id)
            return {
                "role": team_member_orm.role_id,
                "is_default": team_member_orm.is_default
            }
        except TeamMemberORM.DoesNotExist:
            return {"role": None, "is_default": None}

    # ------------------------ Create TeamMember resource --------------------- #

    # ------------------------ Update TeamMember resource --------------------- #
    def sharing_invitations_confirm(self, user: User, email: str = None) -> Optional[User]:
        user_orm = self._get_user_orm(user_id=user.user_id)
        if not user_orm:
            return
        if not email:
            email = user_orm.get_from_cystack_id().get("email")
        if not email:
            return user
        sharing_invitations = TeamMemberORM.objects.filter(
            email=email, team__key__isnull=False, status=PM_MEMBER_STATUS_INVITED, team__personal_share=True
        )
        sharing_invitations.update(email=None, token_invitation=None, user=user_orm)
        return user

    def reject_invitation(self, team_member_id: int):
        team_member_orm = self._get_team_member_orm(team_member_id=team_member_id)
        if not team_member_orm:
            return False
        team_member_orm.delete()
        return True

    def confirm_invitation(self, team_member_id: int, key: str) -> Optional[TeamMember]:
        team_member_orm = self._get_team_member_orm(team_member_id=team_member_id)
        if not team_member_orm:
            return None
        team_member_orm.email = None
        team_member_orm.key = key
        team_member_orm.status = PM_MEMBER_STATUS_CONFIRMED
        team_member_orm.save()
        bump_account_revision_date(user=team_member_orm.user)
        return ModelParser.team_parser().parse_team_member(team_member_orm=team_member_orm)

    def accept_invitation(self, team_member_id: int) -> Optional[TeamMember]:
        team_member_orm = self._get_team_member_orm(team_member_id=team_member_id)
        if not team_member_orm:
            return None
        if team_member_orm.key:
            team_member_orm.status = PM_MEMBER_STATUS_CONFIRMED
        else:
            team_member_orm.status = PM_MEMBER_STATUS_ACCEPTED
        team_member_orm.save()
        bump_account_revision_date(user=team_member_orm.user)
        return ModelParser.team_parser().parse_team_member(team_member_orm=team_member_orm)

    # ------------------------ Delete TeamMember resource --------------------- #
    def leave_all_teams(self, user_id: int, status: str = PM_MEMBER_STATUS_CONFIRMED, personal_share: bool = False,
                        exclude_roles: List = None):
        teams_orm = TeamORM.objects.filter(
            team_members__user_id=user_id, key__isnull=False,
            team_members__status=status
        ).order_by('-creation_date')
        if personal_share is not None:
            teams_orm = teams_orm.filter(personal_share=personal_share)
        for team_orm in teams_orm:
            member_orm = team_orm.team_members.get(user_id=user_id)
            if exclude_roles and member_orm.role_id in exclude_roles:
                continue
            member_orm.delete()
