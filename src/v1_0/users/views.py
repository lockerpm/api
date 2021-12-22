from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, FloatField, ExpressionWrapper
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, Throttled
from rest_framework.decorators import action

from core.utils.data_helpers import camel_snake_data
from core.utils.core_helpers import secure_random_string
from shared.background import LockerBackgroundFactory, BG_EVENT
from shared.constants.members import PM_MEMBER_STATUS_INVITED, MEMBER_ROLE_OWNER, PM_MEMBER_STATUS_CONFIRMED
from shared.constants.event import *
from shared.constants.transactions import PLAN_TYPE_PM_FAMILY_DISCOUNT
from shared.error_responses.error import gen_error, refer_error
from shared.permissions.locker_permissions.user_pwd_permission import UserPwdPermission
from shared.services.pm_sync import SYNC_EVENT_MEMBER_ACCEPTED, PwdSync, SYNC_EVENT_VAULT
from shared.utils.app import now
from v1_0.users.serializers import UserPwdSerializer, UserSessionSerializer, UserPwdInvitationSerializer, \
    UserMasterPasswordHashSerializer, UserChangePasswordSerializer
from v1_0.apps import PasswordManagerViewSet


class UserPwdViewSet(PasswordManagerViewSet):
    permission_classes = (UserPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "register":
            self.serializer_class = UserPwdSerializer
        elif self.action == "session":
            self.serializer_class = UserSessionSerializer
        elif self.action == "invitations":
            self.serializer_class = UserPwdInvitationSerializer
        elif self.action in ["delete_me", "purge_me", "revoke_all_sessions"]:
            self.serializer_class = UserMasterPasswordHashSerializer
        elif self.action == "password":
            self.serializer_class = UserChangePasswordSerializer
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
        user.activated_date = now()
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

    @action(methods=["get"], detail=False)
    def revision_date(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        return Response(status=200, data={"revision_date": user.revision_date})

    @action(methods=["post"], detail=False)
    def session(self, request, *args, **kwargs):
        user = self.request.user
        if user.login_block_until and user.login_block_until > now():
            wait = user.login_block_until - now()
            error_detail = refer_error(gen_error("1008"))
            error_detail["wait"] = wait
            return Response(status=400, data=error_detail)

        user_teams = list(self.team_repository.get_multiple_team_by_user(
            user=user, status=PM_MEMBER_STATUS_CONFIRMED
        ).values_list('id', flat=True))
        ip = request.data.get("ip")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        client_id = validated_data.get("client_id")
        device_identifier = validated_data.get("device_identifier")
        device_name = validated_data.get("device_name")
        device_type = validated_data.get("device_type")
        password = validated_data.get("password")

        # Login failed
        if user.check_master_password(raw_password=password) is False:
            # Create event here
            LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_team_ids", **{
                "team_ids": user_teams, "user_id": user.user_id, "acting_user_id": user.user_id,
                "type": EVENT_USER_LOGIN_FAILED, "ip_address": ip
            })
            # Check policy
            login_policy_limit = self.team_repository.get_multiple_policy_by_user(user=user).filter(
                failed_login_attempts__isnull=False
            ).annotate(
                rate_limit=ExpressionWrapper(
                    F('failed_login_attempts') * 1.0 / F('failed_login_duration'), output_field=FloatField()
                )
            ).order_by('rate_limit').first()
            if login_policy_limit:
                failed_login_attempts = login_policy_limit.failed_login_attempts
                failed_login_duration = login_policy_limit.failed_login_duration
                failed_login_block_time = login_policy_limit.failed_login_block_time
                latest_request_login = user.last_request_login

                user.login_failed_attempts = user.login_failed_attempts + 1
                user.last_request_login = now()
                user.save()

                if user.login_failed_attempts >= failed_login_attempts and \
                        latest_request_login and now() - latest_request_login < failed_login_duration:
                    # Lock login of this member
                    user.login_block_until = now() + failed_login_block_time
                    user.save()
                    owner = self.team_repository.get_primary_member(team=login_policy_limit.team).user_id
                    raise ValidationError(detail={
                        "password": ["Password is not correct"],
                        "owner": owner,
                        "lock_time": "{} (UTC+00)".format(
                            datetime.utcfromtimestamp(now()).strftime('%H:%M:%S %d-%m-%Y')
                        ),
                        "unlock_time": "{} (UTC+00)".format(
                            datetime.utcfromtimestamp(user.login_block_until).strftime('%H:%M:%S %d-%m-%Y')
                        ),
                        "ip": ip
                    })

            raise ValidationError(detail={"password": ["Password is not correct"]})

        user.last_request_login = now()
        user.login_failed_attempts = 0
        user.login_block_until = None
        user.save()
        # First, check CyStack database to get existed access token
        refresh_token_obj = self.session_repository.filter_refresh_tokens(
            user=user, device_identifier=device_identifier
        ).first()
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
        # Create event login successfully
        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_team_ids", **{
            "team_ids": user_teams, "user_id": user.user_id, "acting_user_id": user.user_id,
            "type": EVENT_USER_LOGIN, "ip_address": ip
        })
        return Response(status=200, data=result)

    @action(methods=["post"], detail=False)
    def password(self, request, *args, **kwargs):
        user = self.request.user
        user_teams = list(self.team_repository.get_multiple_team_by_user(
            user=user, status=PM_MEMBER_STATUS_CONFIRMED
        ).values_list('id', flat=True))
        ip = request.data.get("ip")
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        new_master_password_hash = validated_data.get("new_master_password_hash")
        key = validated_data.get("key")
        self.user_repository.change_master_password_hash(
            user=user, new_master_password_hash=new_master_password_hash, key=key
        )
        self.user_repository.revoke_all_sessions(user=user)
        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_team_ids", **{
            "team_ids": user_teams, "user_id": user.user_id, "acting_user_id": user.user_id,
            "type": EVENT_USER_CHANGE_PASSWORD, "ip_address": ip
        })
        return Response(status=200, data={"success": True})

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
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.user_repository.revoke_all_sessions(user)
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def delete_me(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Check if user is the only owner of any teams (except default team)
        default_team = self.user_repository.get_default_team(user=user)
        default_team_id = default_team.id if default_team else None

        owner_teams = user.team_members.all().filter(
            role__name=MEMBER_ROLE_OWNER, is_primary=True, team__key__isnull=False
        ).exclude(team_id=default_team_id)
        if owner_teams.count() > 0:
            raise ValidationError({"non_field_errors": [gen_error("1007")]})

        # Clear data of default team
        if default_team:
            default_team.team_members.all().order_by('id').delete()
            default_team.groups.order_by('id').delete()
            default_team.collections.all().order_by('id').delete()
            default_team.ciphers.all().order_by('id').delete()
            default_team.delete()

        # Deactivated this account
        self.user_repository.delete_account(user)
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def purge_me(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.user_repository.purge_account(user=user)
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[user.user_id]).send()
        return Response(status=200, data={"success": True})

    @action(methods=["get"], detail=False)
    def invitations(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        member_invitations = self.user_repository.get_list_invitations(user=user)
        serializer = self.get_serializer(member_invitations, many=True)
        return Response(status=200, data=serializer.data)

    @action(methods=["put"], detail=False)
    def invitation_update(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        user = self.request.user
        status = request.data.get("status")
        if status not in ["accept", "reject"]:
            raise ValidationError(detail={"status": ["This status is not valid"]})
        try:
            member_invitation = user.team_members.get(
                id=kwargs.get("pk"), status=PM_MEMBER_STATUS_INVITED,
                team__key__isnull=False, user__activated=True
            )
        except ObjectDoesNotExist:
            raise NotFound

        if status == "accept":
            self.team_member_repository.accept_invitation(member=member_invitation)
            primary_owner = self.team_repository.get_primary_member(team=member_invitation.team)
            PwdSync(event=SYNC_EVENT_MEMBER_ACCEPTED, user_ids=[primary_owner.user_id, user.user_id]).send()
            result = {"status": status, "owner": primary_owner.user_id, "team_name": member_invitation.team.name}
        else:
            self.team_member_repository.reject_invitation(member=member_invitation)
            PwdSync(event=SYNC_EVENT_MEMBER_ACCEPTED, user_ids=[user.user_id]).send()
            result = {"status": status}
        return Response(status=200, data=result)

    @action(methods=["get"], detail=False)
    def family(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request)
        # Get all team that user is a confirmed members and owner's plan is Family discount
        team_ids = user.team_members.filter(status=PM_MEMBER_STATUS_CONFIRMED).filter(
            user__pm_user_plan__pm_plan__alias=PLAN_TYPE_PM_FAMILY_DISCOUNT,
            role_id=MEMBER_ROLE_OWNER,
            is_default=True, is_primary=True
        ).values_list('team_id', flat=True)
        return Response(status=200, data=list(team_ids))
