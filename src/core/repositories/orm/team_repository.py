from django.core.exceptions import ObjectDoesNotExist

from core.repositories import ITeamRepository
from shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED

from shared.constants.members import *
from shared.utils.network import get_ip_by_request, detect_device
from cystack_models.models.teams.teams import Team
from cystack_models.models.policy.policy import Policy
from cystack_models.models.enterprises.policy.policy import EnterprisePolicy


class TeamRepository(ITeamRepository):
    def is_locked(self, team: Team) -> bool:
        return team.locked

    def is_pwd_team(self, team: Team) -> bool:
        return False if team.key is None else True

    def get_default_collection(self, team: Team):
        return team.collections.get(is_default=True)

    def get_list_collection_ids(self, team: Team):
        return list(team.collections.values_list('id', flat=True))

    def get_by_id(self, team_id: str) -> Team:
        return Team.objects.get(id=team_id)

    def get_vault_team_by_id(self, team_id) -> Team:
        return Team.objects.get(id=team_id, key__isnull=False)

    def get_multiple_team_by_ids(self, team_ids: list):
        return Team.objects.filter(id__in=team_ids)

    def get_multiple_team_by_user(self, user, status=None, personal_share=None):
        if not status:
            teams = Team.objects.filter(team_members__user=user, key__isnull=False)
        else:
            teams = Team.objects.filter(
                team_members__user=user, key__isnull=False,
                team_members__status=status
            )
        if personal_share is not None:
            teams = teams.filter(personal_share=personal_share)
        return teams

    def get_role_notify(self, team: Team, user) -> dict:
        try:
            member = team.team_members.get(user=user)
            return {
                "role": member.role.name,
                "is_default": member.is_default
            }
        except ObjectDoesNotExist:
            return {"role": None, "is_default": None}

    def get_primary_member(self, team: Team):
        return team.team_members.get(is_primary=True)

    def get_member_obj(self, team: Team, user):
        try:
            return team.team_members.get(user=user)
        except ObjectDoesNotExist:
            return None

    def retrieve_or_create_policy(self, team: Team):
        try:
            return team.policy
        except AttributeError:
            return Policy.create(team=team)

    def get_multiple_policy_by_user(self, user):
        # managed_teams = user.team_members.filter(status=PM_MEMBER_STATUS_CONFIRMED).filter(
        #     # team__team_members__role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN], team__team_members__user=user
        # ).values_list('team_id', flat=True)
        # policies = Policy.objects.filter(team_id__in=managed_teams)
        enterprises = user.enterprise_members.filter(
            status=E_MEMBER_STATUS_CONFIRMED
        ).values_list('enterprise_id', flat=True)
        policies = EnterprisePolicy.objects.filter(enterprise_id__in=enterprises)

        return policies

    def check_team_policy(self, request, team: Team) -> bool:
        policy = self.retrieve_or_create_policy(team=team)

        # Check block ip
        ip_allow = policy.get_list_ip_allow()
        ip_block = policy.get_list_ip_block()
        client_ip = self.__get_client_ip(request)
        if ip_allow and client_ip not in ip_allow:
            return False
        if ip_block and client_ip in ip_block:
            return False

        # Check block mobile
        if policy.block_mobile is True:
            device_info = detect_device(self.__get_user_agent(request))
            if device_info.get("device", {}).get("is_mobile"):
                return False

        return True

    @staticmethod
    def __get_client_ip(request):
        # Get ip from header
        ip = request.META.get("HTTP_LOCKER_CLIENT_IP") or get_ip_by_request(request=request)
        return ip

    @staticmethod
    def __get_user_agent(request):
        user_agent = request.META.get("HTTP_LOCKER_CLIENT_AGENT") or request.META.get("HTTP_USER_AGENT")
        return user_agent
