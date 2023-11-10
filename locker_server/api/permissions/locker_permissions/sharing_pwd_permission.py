from locker_server.api.permissions.app import APIPermission
from locker_server.shared.constants.members import *


class SharingPwdPermission(APIPermission):
    # scope = 'cipher'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        if view.action in ["public_key"]:
            return True
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        if view.action in ["leave"]:
            return role.name in [MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER]

        elif view.action in ["update_role", "update_group_role", "invitation_confirm", "stop_share", "add_member",
                             "stop_share_cipher_folder", "delete_share_folder",
                             "stop_share_folder", "remove_item_share_folder",
                             "add_item_share_folder"]:
            return role.name in [MEMBER_ROLE_OWNER]

        elif view.action in ["update_share_folder"]:
            return role.name in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
        elif view.action in ["invitation_group_confirm"]:
            return role.name in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER]

        return role.name in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
