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
from v1_0.users.serializers import UserPwdSerializer, UserSessionSerializer, UserPwdInvitationSerializer
from v1_0.apps import PasswordManagerViewSet


class UserPwdViewSet(PasswordManagerViewSet):
    permission_classes = (UserPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]
    # user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
    # session_repository = CORE_CONFIG["repositories"]["ISessionRepository"]()

    def get_serializer_class(self):
        if self.action == "register":
            self.serializer_class = UserPwdSerializer
        elif self.action == "session":
            self.serializer_class = UserSessionSerializer
        elif self.action == "invitations":
            self.serializer_class = UserPwdInvitationSerializer
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
        user.set_master_password(raw_password=master_password_hash)
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
                "default_team_id": default_team.id if default_team else None,
            })
        elif request.method == "PUT":
            timeout = request.data.get("timeout", user.timeout)
            timeout_action = request.data.get("timeout_action", user.timeout_action)
            scores = request.data.get("scores", {})
            if isinstance(timeout, int):
                user.timeout = timeout
            if timeout_action in ["lock", "logOut"]:
                user.timeout_action = timeout_action
            if scores:
                user_score = self.user_repository.retrieve_or_create_user_score(user=user)
                user_score.cipher0 = scores.get("0", user_score.cipher0)
                user_score.cipher1 = scores.get("1", user_score.cipher1)
                user_score.cipher2 = scores.get("2", user_score.cipher2)
                user_score.cipher3 = scores.get("3", user_score.cipher3)
                user_score.cipher4 = scores.get("4", user_score.cipher4)
                user_score.save()
            user.save()
            return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def session(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        client_id = validated_data.get("client_id")
        device_identifier = validated_data.get("device_identifier")
        device_name = validated_data.get("device_name")
        device_type = validated_data.get("device_type")
        password = validated_data.get("password")
        if user.check_master_password(raw_password=password) is False:
            raise ValidationError(detail={"password": ["Password is not correct"]})
        # First, check CyStack database to get existed access token
        refresh_token_obj = self.session_repository.filter_refresh_tokens(device_identifier=device_identifier).first()
        # If database does not have refresh token object => Create new one
        if not refresh_token_obj:
            refresh_token_obj = user.user_refresh_tokens.model.retrieve_or_create(user, **{
                "client_id": client_id,
                "device_name": device_name,
                "device_type": device_type,
                "device_identifier": device_identifier,
                "scope": "api offline_access",
                "token_type": "Bearer",
                "refresh_token": secure_random_string(length=64, lower=False)
            })
        # Get access token from refresh token
        access_token = self.session_repository.fetch_valid_token(refresh_token=refresh_token_obj)
        result = {
            "refresh_token": refresh_token_obj.refresh_token,
            "access_token": access_token.access_token,
            "token_type": refresh_token_obj.token_type,
            "public_key": user.public_key,
            "private_key": user.private_key,
            "key": user.key,
            "kdf": user.kdf,
            "kdf_iterations": user.kdf_iterations
        }
        return Response(status=200, data=result)

    @action(methods=["post"], detail=False)
    def password(self, request, *args, **kwargs):
        pass

    @action(methods=["post"], detail=False)
    def password_hint(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        try:
            user = self.user_repository.get_by_id(user_id=user_id)
            if self.user_repository.is_activated(user) is False:
                raise ValidationError(detail={"email": ["There’s no account associated with this email"]})
        except ObjectDoesNotExist:
            raise ValidationError(detail={"email": ["There’s no account associated with this email"]})
        master_password_hint = user.master_password_hint
        return Response(status=200, data={"master_password_hint": master_password_hint})

    @action(methods=["post"], detail=False)
    def revoke_all_sessions(self, request, *args, **kwargs):
        pass

    @action(methods=["post"], detail=False)
    def delete_me(self, request, *args, **kwargs):
        pass

    @action(methods=["post"], detail=False)
    def purge_me(self, request, *args, **kwargs):
        pass

    @action(methods=["get"], detail=False)
    def profile(self, request, *args, **kwargs):
        pass

    @action(methods=["get"], detail=False)
    def public_key(self, request, *args, **kwargs):
        pass

    @action(methods=["get"], detail=False)
    def invitations(self, request, *args, **kwargs):
        user = self.request.user
        # self.check_pwd_session_auth(request=request)
        member_invitations = self.user_repository.get_list_invitations(user=user)
        serializer = self.get_serializer(member_invitations, many=True)
        return Response(status=200, data=serializer.data)

    @action(methods=["put"], detail=False)
    def invitation_update(self, request, *args, **kwargs):
        pass

    @action(methods=["get"], detail=False)
    def family(self, request, *args, **kwargs):
        pass
