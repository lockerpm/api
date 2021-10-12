from django.core.exceptions import ObjectDoesNotExist

from core.repositories import ITeamRepository

from cystack_models.models.teams.teams import Team


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

    def get_multiple_team_by_user(self, user):
        return Team.objects.filter(
            team_members__user=user, key__isnull=False
        )

    def get_role_notify(self, team: Team, user) -> dict:
        try:
            member = team.team_members.get(user=user)
            return {
                "role": member.role.name,
                "is_default": member.is_default
            }
        except ObjectDoesNotExist:
            return {"role": None, "is_default": None}

    def get_pm_plan(self, team: Team):
        pass
