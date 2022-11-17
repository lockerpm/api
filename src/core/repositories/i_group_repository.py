# from abc import ABC, abstractmethod
#
# from cystack_models.models.teams.teams import Team
# from cystack_models.models.teams.groups import Group
#
#
# class IGroupRepository(ABC):
#     @abstractmethod
#     def get_multiple_by_team_id(self, team_id):
#         pass
#
#     @abstractmethod
#     def get_team_group_by_id(self, group_id: str, team_id: str) -> Group:
#         pass
#
#     @abstractmethod
#     def save_new_group(self, team: Team, name: str, access_all: bool, collections: list) -> Group:
#         pass
#
#     @abstractmethod
#     def save_update_group(self, group: Group, name: str, access_all: bool, collections: list) -> Group:
#         pass
#
#     @abstractmethod
#     def save_update_user_group(self, group: Group, member_ids: list) -> Group:
#         pass
