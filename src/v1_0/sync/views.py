from rest_framework.response import Response
from rest_framework.decorators import action

from core.utils.data_helpers import camel_snake_data
from shared.permissions.locker_permissions.sync_pwd_permission import SyncPwdPermission
from v1_0.sync.serializers import SyncProfileSerializer, SyncCipherSerializer, SyncFolderSerializer, \
    SyncCollectionSerializer, SyncPolicySerializer
from v1_0.apps import PasswordManagerViewSet


class SyncPwdViewSet(PasswordManagerViewSet):
    permission_classes = (SyncPwdPermission, )
    http_method_names = ["head", "options", "get"]

    @action(methods=["get"], detail=False)
    def sync(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)

        policies = self.team_repository.get_multiple_policy_by_user(user=user).select_related('team')
        # Check team policies
        block_team_ids = []
        for policy in policies:
            check_policy = self.team_repository.check_team_policy(request=request, team=policy.team)
            if check_policy is False:
                block_team_ids.append(policy.team_id)

        ciphers = self.cipher_repository.get_multiple_by_user(
            user=user, exclude_team_ids=block_team_ids
        ).prefetch_related('collections_ciphers')
        folders = self.folder_repository.get_multiple_by_user(user=user)
        collections = self.collection_repository.get_multiple_user_collections(
            user=user, exclude_team_ids=block_team_ids
        ).select_related('team')

        sync_data = {
            "object": "sync",
            "profile": SyncProfileSerializer(user, many=False).data,
            "ciphers": SyncCipherSerializer(ciphers, many=True, context={"user": user}).data,
            "collections": SyncCollectionSerializer(collections, many=True, context={"user": user}).data,
            "folders": SyncFolderSerializer(folders, many=True).data,
            "domains": None,
            "policies": SyncPolicySerializer(policies, many=True).data,
            "sends": []
        }
        sync_data = camel_snake_data(sync_data, snake_to_camel=True)
        return Response(status=200, data=sync_data)
