from rest_framework.exceptions import PermissionDenied

from locker_server.core.entities.team.team import Team
from locker_server.core.exceptions.team_member_exception import TeamMemberDoesNotExistException
from locker_server.shared.constants.members import *
from locker_server.shared.permissions.app import AppBasePermission
from locker_server.containers.containers import team_member_service, cipher_service


class APIPermission(AppBasePermission):
    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)

    @staticmethod
    def get_team_member(user, obj):
        """
        Get member of the team
        :param user:
        :param obj: (obj) Team object
        :return:
        """
        member = None
        if isinstance(obj, Team):
            try:
                member = team_member_service.get_team_member(user_id=user.user_id, team_id=obj.team_id)
            except TeamMemberDoesNotExistException:
                raise PermissionDenied
        if member is None:
            raise PermissionDenied
        return member

    def can_retrieve_cipher(self, request, cipher):
        user = request.user
        if cipher.user and cipher.user.user_id == user.user_id:
            return True

        # Check member is confirmed
        member = self.get_team_member(user=user, obj=cipher.team)
        if member.status != PM_MEMBER_STATUS_CONFIRMED:
            return False

        # Check is owner or admin
        role_id = member.role.name
        if role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]:
            return True
        if role_id in [MEMBER_ROLE_MEMBER, MEMBER_ROLE_MANAGER] and cipher.team.personal_share is True:
            return True

        # Check member collection: Member belongs to one of collections of cipher and member has read permission
        if self._member_belongs_cipher_collections(member=member, cipher=cipher):
            return True

        # Check member group: Member belongs to one of groups of cipher collections (DEPRECATED)
        # if self._member_belongs_cipher_groups(member=member, cipher=cipher):
        #     return True

        # Check member policy (DEPRECATED)
        # if self._cipher_team_policy(request, cipher) is True:
        #     return True

        return False

    def can_edit_cipher(self, request, cipher):
        user = request.user
        if cipher.user and cipher.user.user_id == user.user_id:
            return True

        # Check member is confirmed
        member = self.get_team_member(user=user, obj=cipher.team)
        if member.status != PM_MEMBER_STATUS_CONFIRMED:
            return False
        # Check is owner or admin
        role_id = member.role.name
        if role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]:
            return True
        if self._member_group_can_edit(member=member) is True:
            return True

        # Check member collection: Member belongs to one of collections of cipher and member has write permission
        if self._member_belongs_cipher_collections(member=member, cipher=cipher) and role_id != MEMBER_ROLE_MEMBER:
            return True

        # Check member group: Member belongs to one of groups of cipher collections (DEPRECATED)
        # if self._member_belongs_cipher_groups(member, cipher):
        #     return True

        # Check member policy (DEPRECATED)
        # if self._cipher_team_policy(request, cipher) is True:
        #     return True

        return False

    @staticmethod
    def _member_belongs_cipher_collections(member, cipher):
        # Check member collection: Member belongs to one of collections of cipher and member has write permission
        return cipher_service.check_member_belongs_cipher_collections(cipher=cipher, member=member)

    @staticmethod
    def _member_belongs_cipher_groups(member, cipher):
        return False
        # from cystack_models.models.teams.collections_groups import CollectionGroup
        #
        # cipher_collection_ids = list(cipher.collections_ciphers.values_list('collection_id', flat=True))
        # member_group_ids = list(member.groups_members.values_list('group_id', flat=True))
        # cipher_group_ids = list(CollectionGroup.objects.filter(
        #     collection_id=cipher_collection_ids
        # ).values_list('group_id', flat=True))
        # return any(group_id in cipher_group_ids for group_id in member_group_ids)

    @staticmethod
    def _member_group_can_edit(member):
        group_member_roles = team_member_service.list_group_member_roles(team_member=member)
        return any(role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN] for role_id in group_member_roles)

    @staticmethod
    def _cipher_team_policy(request, cipher):
        return False
        # # Check member policy
        # team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
        # check_policy = team_repository.check_team_policy(request=request, team=cipher.team)
        # return check_policy
