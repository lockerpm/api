from core.settings import CORE_CONFIG
from cystack_models.models import Cipher
from shared.constants.members import *
from shared.permissions.app import AppBasePermission


class LockerPermission(AppBasePermission):
    def has_permission(self, request, view):
        return super(LockerPermission, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        role_permissions = role.get_permissions()
        role_pattern = self.get_role_pattern(view)
        return member.status == PM_MEMBER_STATUS_CONFIRMED and role_pattern in role_permissions

    def can_retrieve_cipher(self, request, cipher: Cipher):
        user = request.user
        if cipher.user == user:
            return True

        # Check member is confirmed
        member = self.get_team_member(user=user, obj=cipher.team)
        if member.status != PM_MEMBER_STATUS_CONFIRMED:
            return False

        # Check is owner or admin
        role_id = member.role_id
        if role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]:
            return True

        # Check member collection: Member belongs to one of collections of cipher and member has read permission
        if self._member_belongs_cipher_collections(member=member, cipher=cipher):
            return True

        # Check member group: Member belongs to one of groups of cipher collections
        if self._member_belongs_cipher_groups(member=member, cipher=cipher):
            return True

        # Check member policy
        if self._cipher_team_policy(request, cipher) is True:
            return True

        return False

    def can_edit_cipher(self, request, cipher: Cipher):
        user = request.user
        if cipher.user == user:
            return True

        # Check member is confirmed
        member = self.get_team_member(user=user, obj=cipher.team)
        if member.status != PM_MEMBER_STATUS_CONFIRMED:
            return False
        # Check is owner or admin
        role_id = member.role_id
        if role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]:
            return True
        if role_id in [MEMBER_ROLE_MEMBER]:
            return False

        # Check member collection: Member belongs to one of collections of cipher and member has write permission
        if self._member_belongs_cipher_collections(member=member, cipher=cipher) and role_id != MEMBER_ROLE_MEMBER:
            return True

        # Check member group: Member belongs to one of groups of cipher collections
        if self._member_belongs_cipher_groups(member, cipher):
            return True

        # Check member policy
        if self._cipher_team_policy(request, cipher) is True:
            return True

        return False

    @staticmethod
    def _member_belongs_cipher_collections(member, cipher):
        # Check member collection: Member belongs to one of collections of cipher and member has write permission
        cipher_collection_ids = list(cipher.collections_ciphers.values_list('collection_id', flat=True))
        member_collection_ids = list(member.collections_members.values_list('collection_id', flat=True))
        return any(collection_id in cipher_collection_ids for collection_id in member_collection_ids)

    @staticmethod
    def _member_belongs_cipher_groups(member, cipher):
        from cystack_models.models.teams.collections_groups import CollectionGroup

        cipher_collection_ids = list(cipher.collections_ciphers.values_list('collection_id', flat=True))
        member_group_ids = list(member.groups_members.values_list('group_id', flat=True))
        cipher_group_ids = list(CollectionGroup.objects.filter(
            collection_id=cipher_collection_ids
        ).values_list('group_id', flat=True))
        return any(group_id in cipher_group_ids for group_id in member_group_ids)

    @staticmethod
    def _cipher_team_policy(request, cipher):
        # Check member policy
        team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
        check_policy = team_repository.check_team_policy(request=request, team=cipher.team)
        return check_policy
