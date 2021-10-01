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
from v1_0.ciphers.serializers import VaultItemSerializer
from v1_0.users.serializers import UserPwdSerializer, UserSessionSerializer
from v1_0.apps import PasswordManagerViewSet


class CipherPwdViewSet(PasswordManagerViewSet):
    permission_classes = (CipherPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action in ["vaults", "update", "share"]:
            self.serializer_class = VaultItemSerializer
        
        return super(CipherPwdViewSet, self).get_serializer_class()

    @action(methods=["post"], detail=False)
    def vaults(self, request, *args, **kwargs):
        valid_token = self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cipher_detail = serializer.save()

        # We create new cipher object from cipher detail data.
        # Then, we update revision date of user (personal or members of the organization)
        # If cipher belongs to the organization, we also update collections of the cipher.
