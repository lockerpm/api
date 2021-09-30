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
