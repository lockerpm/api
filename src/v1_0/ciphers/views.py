from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, AuthenticationFailed
from rest_framework.decorators import action

from core.settings import CORE_CONFIG
from core.utils.data_helpers import camel_snake_data
from core.utils.core_helpers import secure_random_string
from shared.constants.members import PM_MEMBER_STATUS_INVITED, PM_MEMBER_STATUS_CONFIRMED, MEMBER_ROLE_OWNER
# from shared.constants.sync_event import SYNC_EVENT_MEMBER_ACCEPTED
from shared.constants.transactions import PLAN_TYPE_PM_FAMILY_DISCOUNT
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.cipher_pwd_permission import CipherPwdPermission
from v1_0.ciphers.serializers import VaultItemSerializer, MutipleItemIdsSerializer
from v1_0.users.serializers import UserPwdSerializer, UserSessionSerializer
from v1_0.apps import PasswordManagerViewSet


class CipherPwdViewSet(PasswordManagerViewSet):
    permission_classes = (CipherPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    @property
    def get_serializer_class(self):
        if self.action in ["vaults", "update", "share"]:
            self.serializer_class = VaultItemSerializer
        elif self.action in ["multiple_delete", "multiple_restore", "multiple_permanent_delete"]:
            self.serializer_class = MutipleItemIdsSerializer
        
        return super(CipherPwdViewSet, self).get_serializer_class()

    @action(methods=["post"], detail=False)
    def vaults(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cipher_detail = serializer.save()

        # We create new cipher object from cipher detail data.
        # Then, we update revision date of user (personal or members of the organization)
        # If cipher belongs to the organization, we also update collections of the cipher.
        new_cipher = self.cipher_repository.save_new_cipher(cipher_data=cipher_detail)
        return Response(status=200, data={"id": new_cipher.id})

    def retrieve(self, request, *args, **kwargs):
        # ----- [DEPRECATED] ----- #
        raise NotFound

    @action(methods=["put"], detail=False)
    def multiple_delete(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cipher_ids = validated_data.get("ids")

        # Check permission of user here
        ciphers = self.cipher_repository.get_multiple_by_ids(cipher_ids=cipher_ids)
        teams = self.team_repository.get_multiple_team_by_ids(ciphers.values_list('team_id', flat=True))
        for team in teams:
            self.check_object_permissions(request=request, obj=team)
        self.cipher_repository.delete_multiple_cipher(cipher_ids=cipher_ids, user_deleted=request.user)
        return Response(status=200, data={"success": True})
