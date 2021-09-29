from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.decorators import action

from core.settings import CORE_CONFIG
from core.utils.data_helpers import camel_snake_data
from core.utils.core_helpers import secure_random_string
from shared.constants.members import PM_MEMBER_STATUS_INVITED, PM_MEMBER_STATUS_CONFIRMED, MEMBER_ROLE_OWNER
# from shared.constants.sync_event import SYNC_EVENT_MEMBER_ACCEPTED
from shared.constants.transactions import PLAN_TYPE_PM_FAMILY_DISCOUNT
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.user_pwd_permission import UserPwdPermission
from cystack_models.models.users.users import User
from v1_0.users.serializers import UserPwdSerializer
from v1_0.apps import PasswordManagerViewSet


class UserPwdViewSet(PasswordManagerViewSet):
    permission_classes = (UserPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]
    user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()

    def get_serializer_class(self):
        if self.action == "register":
            self.serializer_class = UserPwdSerializer
        return super(UserPwdViewSet, self).get_serializer_class()

    @action(methods=["post"], detail=False)
    def register(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        kdf = validated_data.get("kdf", 0)
        kdf_iterations = validated_data.get("kdf_iterations", 100000)
        key = validated_data.get("key")
        keys = validated_data.get("keys", {})
        master_password_hash = validated_data.get("master_password_hash")
        master_password_hint = validated_data.get("master_password_hint", "")
        score = validated_data.get("score")
        # Register new user information
        user.kdf = kdf
        user.kdf_iterations = kdf_iterations
        user.key = key
        user.public_key = keys.get("public_key")
        user.private_key = keys.get("encrypted_private_key")
        user.master_password = master_password_hash
        user.master_password_hint = master_password_hint
        user.master_password_score = score
        user.api_key = secure_random_string(length=30)
        # Verified and activated this user
        user.activated = True
        user.save()

        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def prelogin(self, request, *args, **kwargs):
        user = self.request.user
        kdf_info = self.user_repository.get_kdf_information(user=user)
        kdf_info = camel_snake_data(kdf_info, snake_to_camel=True)
        return Response(status=200, data=kdf_info)

    @action(methods=["get", "put"], detail=False)
    def me(self, request, *args, **kwargs):
        user = self.request.user
        if request.method == "GET":
            default_team = self.user_repository.get_default_team(user=user)
            return Response(status=200, data={
                "timeout": user.timeout,
                "timeout_action": user.timeout_action,
                "is_pwd_manager": user.activated,
                "default_team_id": None
            })
        elif request.method == "PUT":
            timeout = request.data.get("timeout", user.bw_timeout)
            timeout_action = request.data.get("timeout_action", user.bw_timeout_action)
            scores = request.data.get("scores", {})
            if isinstance(timeout, int):
                user.bw_timeout = timeout
            if timeout_action in ["lock", "logOut"]:
                user.bw_timeout_action = timeout_action

            user.save()
            return Response(status=200, data={"success": True})