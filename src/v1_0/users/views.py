import json
from datetime import datetime, timedelta
from typing import Dict, Union, Any

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, FloatField, ExpressionWrapper, Count, CharField, IntegerField
from django.db.models.expressions import RawSQL, Case, When
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.decorators import action

from core.utils.data_helpers import camel_snake_data
from core.utils.core_helpers import secure_random_string
from cystack_models.models import Event
from cystack_models.models.notifications.notification_settings import NotificationSetting
from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.enterprises.members.enterprise_members import EnterpriseMember
from shared.background import LockerBackgroundFactory, BG_EVENT, BG_NOTIFY
from shared.constants.account import ONBOARDING_CATEGORY_TO_DASHBOARD, ONBOARDING_CATEGORY_ENTERPRISE
from shared.constants.ciphers import CIPHER_TYPE_MASTER_PASSWORD
from shared.constants.enterprise_members import *
from shared.constants.members import PM_MEMBER_STATUS_INVITED, MEMBER_ROLE_OWNER, PM_MEMBER_STATUS_CONFIRMED
from shared.constants.event import *
from shared.constants.policy import POLICY_TYPE_BLOCK_FAILED_LOGIN, POLICY_TYPE_PASSWORDLESS, POLICY_TYPE_2FA
from shared.constants.transactions import *
from shared.constants.user_notification import NOTIFY_SHARING, NOTIFY_CHANGE_MASTER_PASSWORD
from shared.error_responses.error import gen_error, refer_error
from shared.permissions.locker_permissions.user_pwd_permission import UserPwdPermission
from shared.services.pm_sync import SYNC_EVENT_MEMBER_ACCEPTED, PwdSync, SYNC_EVENT_VAULT, SYNC_EVENT_MEMBER_UPDATE, \
    SYNC_EVENT_CIPHER_UPDATE
from shared.utils.app import now, start_end_month_current
from shared.utils.network import detect_device
from v1_0.ciphers.serializers import UpdateVaultItemSerializer, VaultItemSerializer
from v1_0.users.serializers import UserPwdSerializer, UserSessionSerializer, UserPwdInvitationSerializer, \
    UserMasterPasswordHashSerializer, UserChangePasswordSerializer, DeviceFcmSerializer, UserDeviceSerializer, \
    ListUserSerializer, UpdateOnboardingProcessSerializer
from v1_0.apps import PasswordManagerViewSet


class UserPwdViewSet(PasswordManagerViewSet):
    permission_classes = (UserPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

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
        elif self.action == "fcm_id":
            self.serializer_class = DeviceFcmSerializer
        elif self.action == "devices":
            self.serializer_class = UserDeviceSerializer
        elif self.action in ["retrieve", "list", "list_users"]:
            self.serializer_class = ListUserSerializer
        elif self.action == "onboarding_process":
            self.serializer_class = UpdateOnboardingProcessSerializer
        return super(UserPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            user = self.user_repository.get_by_id(user_id=self.kwargs.get("pk"))
            return user
        except ObjectDoesNotExist:
            raise NotFound

    def get_queryset(self):
        users = self.user_repository.list_users(**{
            "register_from": self.check_int_param(self.request.query_params.get("register_from")),
            "register_to": self.check_int_param(self.request.query_params.get("register_to")),
            "plan": self.request.query_params.get("plan"),
            "user_ids": self.request.query_params.get("user_ids"),
            "utm_source": self.request.query_params.get("utm_source"),
            "q": self.request.query_params.get("q"),
            "activated": self.request.query_params.get("activated")
        })
        return users

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
        score = validated_data.get("score", 0)
        trial_plan_obj = validated_data.get("trial_plan_obj")
        is_trial_promotion = validated_data.get("is_trial_promotion", False)

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
        user.revision_date = now()
        user.delete_account_date = None
        user.save()

        # Upgrade trial plan
        if trial_plan_obj and trial_plan_obj.get_alias() != PLAN_TYPE_PM_FREE:
            current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)

            if trial_plan_obj.is_team_plan is False:
                if current_plan.is_personal_trial_applied() is False:
                    end_period = now() + TRIAL_PERSONAL_PLAN
                    trial_duration = TRIAL_PERSONAL_DURATION_TEXT
                    if is_trial_promotion is True and trial_plan_obj.get_alias() == PLAN_TYPE_PM_FAMILY:
                        end_period = now() + TRIAL_PROMOTION
                        trial_duration = TRIAL_PROMOTION_DURATION_TEXT
                    plan_metadata = {
                        "start_period": now(),
                        "end_period": end_period
                    }
                    self.user_repository.update_plan(
                        user=user, plan_type_alias=trial_plan_obj.get_alias(),
                        duration=DURATION_MONTHLY, scope=settings.SCOPE_PWD_MANAGER, **plan_metadata
                    )
                    current_plan.personal_trial_applied = True
                    current_plan.save()
                    # Send trial mail
                    LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                        func_name="trial_successfully", **{
                            "user_id": user.user_id,
                            "scope": settings.SCOPE_PWD_MANAGER,
                            "plan": trial_plan_obj.get_alias(),
                            "payment_method": None,
                            "duration": trial_duration,
                        }
                    )
            # Enterprise plan
            else:
                if user.enterprise_members.exists() is False and current_plan.get_plan_type_alias() == PLAN_TYPE_PM_FREE:
                    end_period = now() + TRIAL_TEAM_PLAN
                    number_members = TRIAL_TEAM_MEMBERS
                    plan_metadata = {
                        "start_period": now(),
                        "end_period": end_period,
                        "number_members": number_members,
                        "enterprise_name": validated_data.get("enterprise_name")
                    }
                    self.user_repository.update_plan(
                        user=user, plan_type_alias=trial_plan_obj.get_alias(),
                        duration=DURATION_MONTHLY, scope=settings.SCOPE_PWD_MANAGER, **plan_metadata
                    )
                    pm_current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
                    pm_current_plan.enterprise_trial_applied = True
                    pm_current_plan.save()
                    # Send trial enterprise mail here
                    LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                        func_name="trial_enterprise_successfully", **{
                            "user_id": user.user_id,
                            "scope": settings.SCOPE_PWD_MANAGER,
                        }
                    )

        # Upgrade plan if the user is a family member
        self.user_repository.upgrade_member_family_plan(user=user)

        # Update sharing confirmation
        self.user_repository.sharing_invitations_confirm(user=user)
        # Update enterprise invitations
        self.user_repository.enterprise_invitations_confirm(user=user)

        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def prelogin(self, request, *args, **kwargs):
        user = self.request.user
        kdf_info = self.user_repository.get_kdf_information(user=user)
        kdf_info = camel_snake_data(kdf_info, snake_to_camel=True)
        return Response(status=200, data=kdf_info)

    @action(methods=["get"], detail=False)
    def invitation_confirmation(self, request, *args, **kwargs):
        email = self.request.query_params.get("email", None)
        user_id = self.request.query_params.get("user_id", None)
        if (email is None) or (user_id is None):
            raise NotFound
        member_user = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
        # Update sharing confirmation
        self.user_repository.sharing_invitations_confirm(user=member_user, email=email)
        # Update enterprise invitations
        self.user_repository.enterprise_invitations_confirm(user=member_user, email=email)

        return Response(status=200, data={"success": True})

    @action(methods=["get", "put"], detail=False)
    def me(self, request, *args, **kwargs):
        user = self.request.user
        if request.method == "GET":
            utm_source = self.request.query_params.get("utm_source")
            block_by_source = False
            if utm_source in LIST_UTM_SOURCE_PROMOTIONS:
                if user.payments.filter(status=PAYMENT_STATUS_PAID).exists() is False:
                    block_by_source = True
            user_type = self.user_repository.get_user_type(user_id=user.user_id)
            pm_current_plan = self.user_repository.get_current_plan(user=user).get_plan_type_alias()
            return Response(status=200, data={
                "timeout": user.timeout,
                "timeout_action": user.timeout_action,
                "is_pwd_manager": user.activated,
                "block_by_source": block_by_source,
                "pwd_user_id": str(user.user_id),
                "pwd_user_type": user_type,
                "pwd_plan": pm_current_plan
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
    def login_method_me(self, request, *args, **kwargs):
        user = self.request.user
        login_method = user.login_method
        require_passwordless = user.require_passwordless
        return Response(status=200, data={
            "login_method": login_method,
            "require_passwordless": require_passwordless
        })

    @action(methods=["get"], detail=False)
    def passwordless_require(self, request, *args, **kwargs):
        user = self.request.user
        e_member = user.enterprise_members.filter(enterprise__locked=False).first()
        e_passwordless_policy = False
        if e_member:
            enterprise = e_member.enterprise
            policy = enterprise.policies.filter(policy_type=POLICY_TYPE_PASSWORDLESS, enabled=True).first()
            e_passwordless_policy = policy.policy_passwordless.only_allow_passwordless if policy else \
                e_passwordless_policy

        return Response(status=200, data={"require_passwordless": e_passwordless_policy})

    @action(methods=["get"], detail=False)
    def violation_me(self, request, *args, **kwargs):
        user = self.request.user
        start_ts, end_ts = start_end_month_current()
        failed_login = Event.objects.filter(
            type=EVENT_USER_BLOCK_LOGIN, user_id=user.user_id,
            creation_date__gte=start_ts, creation_date__lte=end_ts
        ).count()
        return Response(status=200, data={"failed_login": failed_login})

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

        # user_teams = list(self.team_repository.get_multiple_team_by_user(
        #     user=user, status=PM_MEMBER_STATUS_CONFIRMED, personal_share=False
        # ).values_list('id', flat=True))

        user_enterprises = Enterprise.objects.filter(
            enterprise_members__user=user, enterprise_members__status=E_MEMBER_STATUS_CONFIRMED
        )
        user_enterprise_ids = list(user_enterprises.values_list('id', flat=True))

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
            if user_enterprise_ids:
                # Create failed login event here
                LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                    "enterprise_ids": user_enterprise_ids, "user_id": user.user_id, "acting_user_id": user.user_id,
                    "type": EVENT_USER_LOGIN_FAILED, "ip_address": ip
                })
                policy = self.team_repository.get_multiple_policy_by_user(user=user).filter(
                    policy_type=POLICY_TYPE_BLOCK_FAILED_LOGIN, enabled=True
                ).annotate(
                    rate_limit=ExpressionWrapper(
                        F('policy_failed_login__failed_login_attempts') * 1.0 /
                        F('policy_failed_login__failed_login_duration'), output_field=FloatField()
                    )
                ).order_by('rate_limit').first()
                if policy:
                    failed_login_attempts = policy.policy_failed_login.failed_login_attempts
                    failed_login_duration = policy.policy_failed_login.failed_login_duration
                    failed_login_block_time = policy.policy_failed_login.failed_login_block_time
                    latest_request_login = user.last_request_login

                    user.login_failed_attempts = user.login_failed_attempts + 1
                    user.last_request_login = now()
                    user.save()

                    if user.login_failed_attempts >= failed_login_attempts and \
                            latest_request_login and now() - latest_request_login < failed_login_duration:
                        # Lock login of this member
                        user.login_block_until = now() + failed_login_block_time
                        user.save()
                        # Create block failed login event
                        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(
                            func_name="create_by_enterprise_ids", **{
                                "enterprise_ids": user_enterprise_ids, "user_id": user.user_id,
                                "type": EVENT_USER_BLOCK_LOGIN, "ip_address": ip
                            }
                        )
                        owner = policy.enterprise.enterprise_members.get(is_primary=True).user_id
                        raise ValidationError(detail={
                            "password": ["Password is not correct"],
                            "failed_login_owner_email": policy.policy_failed_login.failed_login_owner_email,
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

        if user_enterprises.filter(enterprise_members__user=user, enterprise_members__is_activated=False).exists():
            raise ValidationError({"non_field_errors": [gen_error("1009")]})
        if EnterpriseMember.objects.filter(
            user=user, status__in=[E_MEMBER_STATUS_REQUESTED, E_MEMBER_STATUS_INVITED], domain__isnull=False
        ).exists():
            raise ValidationError({"non_field_errors": [gen_error("1011")]})
        if user_enterprises.filter(enterprise_members__user=user, locked=True).exists():
            raise ValidationError({"non_field_errors": [gen_error("1010")]})

        # Check 2FA policy
        is_factor2 = request.data.get("is_factor2", False)
        if is_factor2 is False:
            for enterprise in user_enterprises:
                policy = enterprise.policies.filter(policy_type=POLICY_TYPE_2FA, enabled=True).first()
                if not policy:
                    continue
                try:
                    member_role = enterprise.enterprise_members.get(user=user).role_id
                except ObjectDoesNotExist:
                    continue
                only_admin = policy.policy_2fa.only_admin
                if only_admin is False or \
                        (only_admin and member_role in [E_MEMBER_ROLE_ADMIN, E_MEMBER_ROLE_PRIMARY_ADMIN]):
                    raise ValidationError({"non_field_errors": [gen_error("1012")]})

        # Unblock login
        user.last_request_login = now()
        user.login_failed_attempts = 0
        user.login_block_until = None
        user.save()

        # Get sso token id from authentication token
        decoded_token = self.decode_token(request.auth)
        sso_token_id = decoded_token.get("sso_token_id") if decoded_token else None

        # Get current user plan, the sync device limit
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        limit_sync_device = None if user_enterprise_ids else current_plan.get_plan_obj().get_sync_device()
        # The list stores sso token id which will not be synchronized
        not_sync_sso_token_ids = []

        # First, check the device exists
        device_existed = self.device_repository.get_device_by_identifier(
            user=user, device_identifier=device_identifier
        )
        device_info = detect_device(ua_string=self.get_client_agent())
        device_obj = user.user_devices.model.retrieve_or_create(user, **{
            "client_id": client_id,
            "device_name": device_name,
            "device_type": device_type,
            "device_identifier": device_identifier,
            "os": device_info.get("os"),
            "browser": device_info.get("browser"),
            "scope": "api offline_access",
            "token_type": "Bearer",
            "refresh_token": secure_random_string(length=64, lower=False)
        })
        # If the device does not exist => New device => Create new one
        if not device_existed:
            all_devices = self.device_repository.get_device_user(user=user)
            if limit_sync_device and all_devices.count() > limit_sync_device:
                old_devices = all_devices[:limit_sync_device]
                not_sync_sso_token_ids = list(
                    self.device_repository.get_devices_access_token(devices=old_devices).exclude(
                        sso_token_id__isnull=True
                    ).values_list('sso_token_id', flat=True)
                )
                self.device_repository.remove_devices_access_token(devices=old_devices)

        # Set last login
        self.device_repository.set_last_login(device=device_obj, last_login=now())

        # Retrieve or create new access token
        access_token = self.device_repository.fetch_device_access_token(
            device=device_obj, renewal=True, sso_token_id=sso_token_id
        )
        result = {
            "refresh_token": device_obj.refresh_token,
            "access_token": access_token.access_token,
            "token_type": device_obj.token_type,
            "public_key": user.public_key,
            "private_key": user.private_key,
            "key": user.key,
            "kdf": user.kdf,
            "kdf_iterations": user.kdf_iterations,
            "not_sync": not_sync_sso_token_ids,
            "has_no_master_pw_item": not user.created_ciphers.filter(type=CIPHER_TYPE_MASTER_PASSWORD).exists()
        }
        # Create event login successfully
        if user_enterprise_ids:
            LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                "enterprise_ids": user_enterprise_ids, "user_id": user.user_id, "acting_user_id": user.user_id,
                "type": EVENT_USER_LOGIN, "ip_address": ip
            })
        return Response(status=200, data=result)

    @action(methods=["post"], detail=False)
    def fcm_id(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        fcm_id = validated_data.get("fcm_id")
        device = validated_data.get("device")
        self.device_repository.update_fcm_id(device=device, fcm_id=fcm_id)
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def password(self, request, *args, **kwargs):
        user = self.request.user
        # user_teams = list(self.team_repository.get_multiple_team_by_user(
        #     user=user, status=PM_MEMBER_STATUS_CONFIRMED
        # ).values_list('id', flat=True))
        ip = request.data.get("ip")
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        new_master_password_hash = validated_data.get("new_master_password_hash")
        key = validated_data.get("key")
        score = validated_data.get("score", user.master_password_score)

        # Update the master password cipher
        master_password_cipher = request.data.get("master_password_cipher")
        master_pwd_item_obj = user.created_ciphers.filter(type=CIPHER_TYPE_MASTER_PASSWORD).first()

        if master_password_cipher:
            if not master_pwd_item_obj:
                # Create master password item
                self.serializer_class = VaultItemSerializer
                serializer = VaultItemSerializer(
                    data=master_password_cipher, **{"context": self.get_serializer_context()}
                )
                serializer.is_valid(raise_exception=True)
                team = serializer.validated_data.get("team")
                cipher_detail = serializer.save(**{"check_plan": False})
                cipher_detail.pop("team", None)
                cipher_detail = json.loads(json.dumps(cipher_detail))
                new_cipher = self.cipher_repository.save_new_cipher(cipher_data=cipher_detail)
                # Send sync message
                PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[request.user.user_id], team=team, add_all=True).send(
                    data={"id": str(new_cipher.id)}
                )
            else:
                # Check permission
                self.serializer_class = UpdateVaultItemSerializer
                serializer = UpdateVaultItemSerializer(
                    data=master_password_cipher, **{"context": self.get_serializer_context()}
                )
                # serializer = self.get_serializer(data=master_password_cipher)
                serializer.is_valid(raise_exception=True)
                team = serializer.validated_data.get("team")
                cipher_detail = serializer.save(**{"cipher": master_pwd_item_obj})
                cipher_detail.pop("team", None)
                cipher_detail = json.loads(json.dumps(cipher_detail))
                master_password_cipher_obj = self.cipher_repository.save_update_cipher(
                    cipher=master_pwd_item_obj, cipher_data=cipher_detail
                )
                PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[request.user.user_id], team=team, add_all=True).send(
                    data={"id": master_password_cipher_obj.id}
                )

        self.user_repository.change_master_password_hash(
            user=user, new_master_password_hash=new_master_password_hash, key=key, score=score
        )
        self.user_repository.revoke_all_sessions(user=user)
        mail_user_ids = NotificationSetting.get_user_mail(
            category_id=NOTIFY_CHANGE_MASTER_PASSWORD, user_ids=[user.user_id]
        )
        return Response(status=200, data={"notification": True if user.user_id in mail_user_ids else False})

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
        self._delete_locker_user(user=user)
        return Response(status=200, data={"success": True})

    def _delete_locker_user(self, user):
        # TODO: Need to delete Enterprise or not???
        # # Check if user is the owner of the enterprise
        # default_enterprise = self.user_repository.get_default_enterprise(user=user)
        # # Clear data of the default enterprise
        # if default_enterprise:
        #     default_enterprise.enterprise_members.all().order_by('id').delete()
        #     default_enterprise.groups.order_by('id').delete()
        #     default_enterprise.policies.order_by('id').delete()
        #     default_enterprise.domains.all().order_by('id').delete()
        #     default_enterprise.delete()

        # Check if user is the only owner of any teams (except default team)
        default_team = self.user_repository.get_default_team(user=user)
        default_team_id = default_team.id if default_team else None
        owner_teams = user.team_members.all().filter(
            role__name=MEMBER_ROLE_OWNER, is_primary=True, team__key__isnull=False,
        ).exclude(team_id=default_team_id)
        # Remove all user's share teams
        personal_share_teams = owner_teams.filter(team__personal_share=True)
        self.cipher_repository.delete_permanent_multiple_cipher_by_teams(
            team_ids=list(personal_share_teams.values_list('team_id', flat=True))
        )
        personal_share_teams.delete()
        # Share with me
        owners_share_with_me = self.sharing_repository.delete_share_with_me(user)
        PwdSync(event=SYNC_EVENT_MEMBER_UPDATE, user_ids=owners_share_with_me).send()

        # Deactivated this account and cancel the current plan immediately
        self.user_repository.delete_account(user)

    @action(methods=["post"], detail=False)
    def purge_me(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shared_ciphers_members = self.user_repository.purge_account(user=user)

        shared_member_user_ids = [cipher_member.get("shared_member") for cipher_member in shared_ciphers_members]
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[user.user_id] + shared_member_user_ids).send()

        # mail_user_ids = NotificationSetting.get_user_mail(category_id=NOTIFY_SHARING, user_ids=shared_member_user_ids)
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=shared_member_user_ids
        )
        notification = [c for c in shared_ciphers_members if c.get("shared_member") in notification_user_ids]
        return Response(status=200, data=notification)

    @action(methods=["get", "put"], detail=False)
    def onboarding_process(self, request, *args, **kwargs):
        user = self.request.user
        onboarding_process = user.get_onboarding_process()
        if request.method == "GET":
            return Response(status=200, data=onboarding_process)
        elif request.method == "PUT":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            vault_to_dashboard = validated_data.get(
                "vault_to_dashboard", onboarding_process.get(ONBOARDING_CATEGORY_TO_DASHBOARD)
            )
            enterprise_onboarding = validated_data.get(
                "enterprise_onboarding", onboarding_process.get(ONBOARDING_CATEGORY_TO_DASHBOARD)
            )
            onboarding_process.update({
                ONBOARDING_CATEGORY_TO_DASHBOARD: vault_to_dashboard,
                ONBOARDING_CATEGORY_ENTERPRISE: enterprise_onboarding
            })
            user.onboarding_process = onboarding_process
            user.save()
            return Response(status=200, data=user.get_onboarding_process())

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
            user__pm_user_plan__pm_plan__alias=PLAN_TYPE_PM_FAMILY,
            role_id=MEMBER_ROLE_OWNER,
            is_default=True, is_primary=True
        ).values_list('team_id', flat=True)
        return Response(status=200, data=list(team_ids))

    @action(methods=["get"], detail=False)
    def devices(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        devices = self.device_repository.get_device_user(user=user)
        serializer = self.get_serializer(devices, many=True)
        return Response(status=200, data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        statistic_param = self.request.query_params.get("statistic", "0")
        serializer = self.get_serializer(instance)
        data = serializer.data

        if statistic_param == "1":
            # policies = self.team_repository.get_multiple_policy_by_user(user=instance).select_related('enterprise')
            # Check team policies
            block_team_ids = []
            # for policy in policies:
            #     check_policy = self.team_repository.check_team_policy(request=request, team=policy.team)
            #     if check_policy is False:
            #         block_team_ids.append(policy.team_id)

            ciphers = self.cipher_repository.get_multiple_by_user(
                user=instance, exclude_team_ids=block_team_ids
            ).order_by('-revision_date').values('type').annotate(count=Count('type')).order_by('-count')
            ciphers_count = {item["type"]: item["count"] for item in list(ciphers)}
            data["items"] = ciphers_count

        data["current_plan"] = self.user_repository.get_current_plan(
            user=instance, scope=settings.SCOPE_PWD_MANAGER
        ).get_plan_type_alias()

        return Response(status=200, data=data)

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        instance = self.get_object()
        if user.user_id == instance.user_id:
            raise PermissionDenied
        self._delete_locker_user(user=instance)
        return Response(status=200, data={"success": True})

    @action(methods=["get"], detail=False)
    def list_user_ids(self, request, *args, **kwargs):
        users = self.get_queryset()
        user_ids = users.values_list('user_id', flat=True)
        return Response(status=200, data={"user_ids": list(user_ids)})

    @action(methods=["get"], detail=False)
    def list_users(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 20))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 20
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=["get"], detail=False)
    def dashboard(self, request, *args, **kwargs):
        current_time = now()
        register_from_param = self.check_int_param(self.request.query_params.get("register_from")) or current_time - 90 * 86400
        register_to_param = self.check_int_param(self.request.query_params.get("register_to")) or current_time
        duration_param = self.request.query_params.get("duration") or "monthly"
        device_type_param = self.request.query_params.get("device_type") or ""

        users = self.user_repository.list_users()
        if register_from_param:
            users = users.filter(creation_date__gte=register_from_param)
        if register_to_param:
            users = users.filter(creation_date__lt=register_to_param)
        device_users = users.annotate(
            web_device_count=Count(
                Case(When(user_devices__client_id='web', then=1), output_field=IntegerField())
            ),
            mobile_device_count=Count(
                Case(When(user_devices__client_id='mobile', then=1), output_field=IntegerField())
            ),
            ios_device_count=Count(
                Case(When(user_devices__device_type=1, then=1), output_field=IntegerField())
            ),
            android_device_count=Count(
                Case(When(user_devices__device_type=0, then=1), output_field=IntegerField())
            ),
            extension_device_count=Count(
                Case(When(user_devices__client_id='browser', then=1), output_field=IntegerField())
            ),
        )
        if device_type_param == "mobile":
            device_users = device_users.filter(mobile_device_count__gt=0)
        if device_type_param == "android":
            device_users = device_users.filter(android_device_count__gt=0)
        if device_type_param == "ios":
            device_users = device_users.filter(ios_device_count__gt=0)
        if device_type_param == "web":
            device_users = device_users.filter(web_device_count__gt=0)
        if device_type_param == "browser":
            device_users = device_users.filter(extension_device_count__gt=0)
        device_users = users.filter(user_id__in=device_users.values_list('user_id', flat=True))
        statistic_device = self._statistic_users_by_time(
            device_users, register_from_param, register_to_param, duration_param
        )

        dashboard_result = {
            "total_device": device_users.count(),
            "device": statistic_device
        }
        return Response(status=200, data=dashboard_result)

    @staticmethod
    def _generate_duration_init_data(start, end, duration="monthly"):
        durations_list = []
        for i in range((end - start).days + 1):
            date = start + timedelta(days=i)
            if duration == "daily":
                d = "{}-{:02}-{:02}".format(date.year, date.month, date.day)
            elif duration == "weekly":
                d = date.isocalendar()[:2]   # e.g. (2022, 24)
                d = "{}-{:02}".format(*d)
            else:
                d = "{}-{:02}".format(date.year, date.month)
            durations_list.append(d)
        duration_init = dict()
        for d in sorted(set(durations_list), reverse=True):
            duration_init[d] = None

        # # Get annotation query
        if duration == "daily":
            query = "CONCAT(YEAR(FROM_UNIXTIME(creation_date)), '-', " \
                    "LPAD(MONTH(FROM_UNIXTIME(creation_date)), 2, '0'), '-', " \
                    "LPAD(DAY(FROM_UNIXTIME(creation_date)), 2, '0') )"
        elif duration == "weekly":
            query = "CONCAT(YEAR(FROM_UNIXTIME(creation_date)), '-', LPAD(WEEK(FROM_UNIXTIME(creation_date)), 2, '0'))"
        else:
            query = "CONCAT(YEAR(FROM_UNIXTIME(creation_date)), '-', LPAD(MONTH(FROM_UNIXTIME(creation_date)), 2, '0'))"

        return {
            "duration_init": duration_init,
            "query": query
        }

    def _statistic_users_by_time(self, users, from_param, to_param, duration="weekly"):
        if to_param is None:
            to_param = now()
        if from_param is None:
            if users.first():
                from_param = users.first().creation_date
            else:
                from_param = now() - 365 * 86400

        duration_init_data = self._generate_duration_init_data(
            start=datetime.fromtimestamp(from_param),
            end=datetime.fromtimestamp(to_param),
            duration=duration
        )
        data = duration_init_data.get("duration_init") or {}
        query = duration_init_data.get("query")

        users_by_duration = users.filter(creation_date__gte=from_param, creation_date__lte=to_param).annotate(
            duration=RawSQL(query, [], output_field=CharField())
        ).order_by().values('duration').annotate(count=Count('duration'))
        for user_by_duration in users_by_duration:
            duration_string = user_by_duration.get("duration")
            duration_count = user_by_duration.get("count")
            if duration_string:
                data.update({duration_string: {"count": duration_count}})
                # data[duration_string] = {"count": duration_count}

        return data
