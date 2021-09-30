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
from shared.permissions.locker_permissions.sync_pwd_permission import SyncPwdPermission
from v1_0.users.serializers import UserPwdSerializer, UserSessionSerializer
from v1_0.apps import PasswordManagerViewSet


class SyncPwdViewSet(PasswordManagerViewSet):
    permission_classes = (SyncPwdPermission, )
    http_method_names = ["head", "options", "get"]
    session_repository = CORE_CONFIG["repositories"]["ISessionRepository"]()

    @action(methods=["get"], detail=False)
    def sync(self, request, *args, **kwargs):
        user = self.request.user

        valid_token = self.session_repository.fetch_access_token(user=user)
        if not valid_token:
            raise AuthenticationFailed

        return Response(status=200, data={"success": True})
