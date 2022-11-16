from django.db import connection

from core.settings import CORE_CONFIG
from shared.background.i_background import ILockerBackground


class EnterpriseGroupBackground(ILockerBackground):
    sharing_repository = CORE_CONFIG["repositories"]["ISharingRepository"]

    def add_group_member_to_share(self, enterprise_group, new_member_ids):
        try:
            enterprise_group_member_user_ids = enterprise_group.groups_members.filter(
                member_id__in=new_member_ids
            ).values_list('member__user_id', flat=True)
            sharing_groups = enterprise_group.sharing_groups.all().select_related('team').prefetch_related('groups_members')
            members = [{"user_id": user_id, "key": None} for user_id in enterprise_group_member_user_ids]

            for sharing_group in sharing_groups:
                team = sharing_group.team
                collection = team.collections.first()
                groups = [{
                    "id": sharing_group.id,
                    "role": sharing_group.role_id,
                    "members": members
                }]
                existed_member_users, non_existed_member_users = self.sharing_repository.add_group_members(
                    team=team, shared_collection=collection, groups=groups
                )
                # TODO: Notification here

        except Exception as e:
            self.log_error(func_name="add_group_member_to_share")
        finally:
            if self.background:
                connection.close()
