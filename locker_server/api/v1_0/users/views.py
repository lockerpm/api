import json
from datetime import datetime

from django.conf import settings
# from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError, AuthenticationFailed
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.user_pwd_permission import UserPwdPermission
from locker_server.core.exceptions.cipher_exception import FolderDoesNotExistException, CipherMaximumReachedException
from locker_server.core.exceptions.collection_exception import CollectionDoesNotExistException, \
    CollectionCannotRemoveException, CollectionCannotAddException
from locker_server.core.exceptions.device_exception import DeviceDoesNotExistException
from locker_server.core.exceptions.team_exception import TeamDoesNotExistException, TeamLockedException
from locker_server.core.exceptions.team_member_exception import TeamMemberDoesNotExistException, \
    OnlyAllowOwnerUpdateException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException, \
    UserAuthBlockingEnterprisePolicyException, UserAuthFailedException, UserAuthBlockedEnterprisePolicyException, \
    UserIsLockedByEnterpriseException, UserEnterprisePlanExpiredException, UserBelongEnterpriseException, \
    User2FARequireException, UserAuthFailedPasswordlessRequiredException, UserCreationDeniedException, \
    UserResetPasswordTokenInvalidException
from locker_server.settings import locker_server_settings
from locker_server.shared.constants.account import *
from locker_server.shared.constants.transactions import PLAN_TYPE_PM_ENTERPRISE
from locker_server.shared.error_responses.error import refer_error, gen_error
from locker_server.api.v1_0.ciphers.serializers import VaultItemSerializer, UpdateVaultItemSerializer
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY
from locker_server.shared.external_services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_UPDATE
from locker_server.shared.external_services.user_notification.list_jobs import PWD_MASTER_PASSWORD_CHANGED, \
    PWD_NO_MASTER_PASSWORD_HINT, PWD_HINT_FOR_MASTER_PASSWORD, PWD_ACCOUNT_DELETED, PWD_DELETE_SHARE_ITEM, \
    PWD_CONFIRM_INVITATION
from locker_server.shared.utils.app import now, get_ip_location
from locker_server.shared.utils.network import get_ip_by_request, detect_device
from .serializers import UserMeSerializer, UserUpdateMeSerializer, UserRegisterSerializer, UserSessionSerializer, \
    DeviceFcmSerializer, UserChangePasswordSerializer, UserNewPasswordSerializer, UserCheckPasswordSerializer, \
    UserMasterPasswordHashSerializer, UpdateOnboardingProcessSerializer, UserPwdInvitationSerializer, \
    UserDeviceSerializer, PreloginSerializer, UserResetPasswordSerializer


class UserPwdViewSet(APIBaseViewSet):
    permission_classes = (UserPwdPermission,)
    http_method_names = ["options", "head", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9a-z-]+'

    def get_throttles(self):
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == "me":
            if self.request.method == "GET":
                self.serializer_class = UserMeSerializer
            else:
                self.serializer_class = UserUpdateMeSerializer
        elif self.action == "register":
            self.serializer_class = UserRegisterSerializer
        elif self.action == "session":
            self.serializer_class = UserSessionSerializer
        elif self.action == "fcm_id":
            self.serializer_class = DeviceFcmSerializer
        elif self.action == "password":
            self.serializer_class = UserChangePasswordSerializer
        elif self.action == "new_password":
            self.serializer_class = UserNewPasswordSerializer
        elif self.action == "check_password":
            self.serializer_class = UserCheckPasswordSerializer
        elif self.action in ["delete_me", "purge_me", "revoke_all_sessions"]:
            self.serializer_class = UserMasterPasswordHashSerializer
        elif self.action == "onboarding_process":
            self.serializer_class = UpdateOnboardingProcessSerializer
        elif self.action == "invitations":
            self.serializer_class = UserPwdInvitationSerializer
        elif self.action == "devices":
            self.serializer_class = UserDeviceSerializer
        elif self.action == "prelogin":
            self.serializer_class = PreloginSerializer
        elif self.action == "reset_password":
            self.serializer_class = UserResetPasswordSerializer
        return super().get_serializer_class()

    @action(methods=["post"], detail=False)
    def register(self, request, *args, **kwargs):
        # user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        key = validated_data.get("key")
        keys = validated_data.get("keys", {})
        master_password_hash = validated_data.get("master_password_hash")
        try:
            self.user_service.register_user(
                user_id=validated_data.get("email"),
                master_password_hash=master_password_hash,
                key=key,
                keys=keys,
                default_plan=locker_server_settings.DEFAULT_PLAN,
                default_plan_time=locker_server_settings.DEFAULT_PLAN_TIME,
                **{
                    "full_name": validated_data.get("full_name") or validated_data.get("email"),
                    "kdf": validated_data.get("kdf", 0),
                    "kdf_iterations": validated_data.get("kdf_iterations", 100000),
                    "master_password_hint": validated_data.get("master_password_hint", ""),
                    "score": validated_data.get("score", 0),
                    "trial_plan": validated_data.get("trial_plan"),
                    "is_trial_promotion": validated_data.get("is_trial_promotion"),
                    "enterprise_name": validated_data.get("enterprise_name")
                }
            )
        except UserCreationDeniedException:
            raise ValidationError(detail={"email": ["Please contact to your administrator to create new account"]})
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["get"], detail=False)
    def invitation_confirmation(self, request, *args, **kwargs):
        email = self.request.query_params.get("email", None)
        user_id = self.request.query_params.get("user_id", None)
        if (email is None) or (user_id is None):
            raise NotFound
        self.user_service.invitation_confirmation(user_id=user_id, email=email)
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["get", "put"], detail=False)
    def me(self, request, *args, **kwargs):
        user = self.request.user

        if request.method == "GET":
            serializer = self.get_serializer(user, many=False)
            me_data = serializer.data
            pm_current_plan = self.user_service.get_current_plan(user=user)
            user_type = self.user_service.get_user_type(user=user)
            block_by_source = self.user_service.is_blocked_by_source(
                user=user, utm_source=self.request.query_params.get("utm_source")
            )
            me_data.update({
                "block_by_source": block_by_source,
                "pwd_user_type": user_type,
                "pwd_plan": pm_current_plan.pm_plan.alias,
            })
            return Response(status=status.HTTP_200_OK, data=me_data)

        elif request.method == "PUT":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            try:
                self.user_service.update_user(user_id=user.user_id, user_update_data=validated_data)
            except UserDoesNotExistException:
                raise AuthenticationFailed
            return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["get"], detail=False)
    def login_method_me(self, request, *args, **kwargs):
        user = self.request.user
        login_method = user.login_method
        require_passwordless = self.user_service.is_require_passwordless(user_id=user.user_id)
        return Response(status=status.HTTP_200_OK, data={
            "set_up_passwordless": True if user.fd_credential_id else False,
            "login_method": login_method,
            "require_passwordless": require_passwordless
        })

    @action(methods=["get"], detail=False)
    def passwordless_require(self, request, *args, **kwargs):
        user = self.request.user
        require_passwordless = self.user_service.is_require_passwordless(
            user_id=user.user_id, require_enterprise_member_status=None
        )
        return Response(status=status.HTTP_200_OK, data={"require_passwordless": require_passwordless})

    @action(methods=["get"], detail=False)
    def block_by_2fa_policy(self, request, *args, **kwargs):
        user = self.request.user
        is_factor2 = user.is_factor2
        is_block = self.user_service.is_block_by_2fa_policy(user_id=user.user_id, is_factor2=is_factor2)
        return Response(status=status.HTTP_200_OK, data={"block": is_block})

    @action(methods=["get"], detail=False)
    def violation_me(self, request, *args, **kwargs):
        user = self.request.user
        failed_login = self.user_service.count_failed_login_event(user_id=user.user_id)
        return Response(status=status.HTTP_200_OK, data={"failed_login": failed_login})

    @action(methods=["get"], detail=False)
    def revision_date(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        return Response(status=status.HTTP_200_OK, data={"revision_date": user.revision_date})

    @action(methods=["post"], detail=False)
    def session(self, request, *args, **kwargs):
        ip = self.get_ip()
        ua_string = self.get_client_agent()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        client_id = validated_data.get("client_id")
        device_identifier = validated_data.get("device_identifier")
        device_name = validated_data.get("device_name")
        device_type = validated_data.get("device_type")
        email = validated_data.get("email")
        password = validated_data.get("password")
        try:
            user = self.user_service.retrieve_by_email(email=email)
        except UserDoesNotExistException:
            raise ValidationError(detail={"email": ["The email is not valid"]})
        is_factor2 = user.is_factor2
        try:
            result = self.user_service.user_session(
                user=user, password=password, client_id=client_id, device_identifier=device_identifier,
                device_name=device_name, device_type=device_type,
                is_factor2=is_factor2,
                token_auth_value=self.request.auth,
                secret=settings.SECRET_KEY,
                ip=ip,
                ua=ua_string
            )
            return Response(status=status.HTTP_200_OK, data=result)
        except UserAuthBlockingEnterprisePolicyException as e:
            error_detail = refer_error(gen_error("1008"))
            error_detail["wait"] = e.wait
            return Response(status=400, data=error_detail)
        except UserAuthBlockedEnterprisePolicyException as e:
            raise ValidationError(detail={
                "password": ["Password is not correct"],
                "failed_login_owner_email": e.failed_login_owner_email,
                "owner": e.owner,
                "lock_time": e.lock_time,
                "unlock_time": e.unlock_time,
                "ip": e.ip
            })
        except UserAuthFailedException:
            raise ValidationError(detail={"password": ["Password is not correct"]})
        except UserIsLockedByEnterpriseException:
            raise ValidationError({"non_field_errors": [gen_error("1009")]})
        except UserEnterprisePlanExpiredException:
            raise ValidationError({"non_field_errors": [gen_error("1010")]})
        except UserBelongEnterpriseException:
            raise ValidationError({"non_field_errors": [gen_error("1011")]})
        except User2FARequireException:
            raise ValidationError({"non_field_errors": [gen_error("1012")]})

    @action(methods=["post"], detail=False)
    def fcm_id(self, request, *args, **kwargs):
        # self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        fcm_id = validated_data.get("fcm_id")
        device_identifier = validated_data.get("device_identifier")
        try:
            self.user_service.update_device_fcm_id(
                user=self.request.user, device_identifier=device_identifier, fcm_id=fcm_id
            )
        except DeviceDoesNotExistException:
            raise ValidationError(detail={"device_identifier": ["The device identifier does not exist"]})
        return Response(status=status.HTTP_200_OK, data={"success": True})

    def _create_master_pwd_cipher(self, cipher_data):
        try:
            new_cipher = self.cipher_service.create_cipher(
                user=self.request.user, cipher_data=cipher_data, check_plan=False
            )
            return new_cipher
        except FolderDoesNotExistException:
            raise ValidationError(detail={"folderId": ["This folder does not exist"]})
        except TeamDoesNotExistException:
            raise ValidationError(detail={"organizationId": [
                "This team does not exist", "Team này không tồn tại"
            ]})
        except TeamLockedException:
            raise ValidationError({"non_field_errors": [gen_error("3003")]})
        except CollectionDoesNotExistException as e:
            raise ValidationError(detail={
                "collectionIds": ["The team collection id {} does not exist".format(e.collection_id)]
            })
        except CipherMaximumReachedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("5002")]})

    def _update_master_pwd_cipher(self, master_pwd_item_obj, cipher_data):
        try:
            return self.cipher_service.update_cipher(
                cipher=master_pwd_item_obj, user=self.request.user, cipher_data=cipher_data,
            )
        except FolderDoesNotExistException:
            raise ValidationError(detail={"folderId": ["This folder does not exist"]})
        except TeamDoesNotExistException:
            raise ValidationError(detail={"organizationId": [
                "This team does not exist", "Team này không tồn tại"
            ]})
        except TeamLockedException:
            raise ValidationError({"non_field_errors": [gen_error("3003")]})
        except CollectionCannotRemoveException as e:
            raise ValidationError(detail={"collectionIds": [
                f"You can not remove collection {e.collection_id}"
            ]})
        except CollectionCannotAddException as e:
            raise ValidationError(detail={"collectionIds": [
                f"You can not add collection {e.collection_id}"
            ]})
        except OnlyAllowOwnerUpdateException:
            raise ValidationError(detail={
                "organizationId": ["You must be owner of the item to change this field"]
            })
        except CipherMaximumReachedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("5002")]})

    @action(methods=["post"], detail=False)
    def password(self, request, *args, **kwargs):
        user = self.request.user
        ip = self.get_ip()
        # self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        master_password_hash = validated_data.get("master_password_hash")
        new_master_password_hash = validated_data.get("new_master_password_hash")
        new_master_password_hint = validated_data.get("new_master_password_hint", user.master_password_hint)
        key = validated_data.get("key")
        score = validated_data.get("score", user.master_password_score)
        login_method = validated_data.get("login_method", user.login_method)

        try:
            decoded_token = self.auth_service.decode_token(request.auth.access_token, secret=settings.SECRET_KEY)
            sso_token_id = decoded_token.get("sso_token_id") if decoded_token else None
            result = self.user_service.change_master_password(
                user=user, key=key, master_password_hash=master_password_hash,
                new_master_password_hash=new_master_password_hash,
                new_master_password_hint=new_master_password_hint,
                score=score, login_method=login_method,
                current_sso_token_id=sso_token_id
            )
        except UserAuthFailedPasswordlessRequiredException:
            raise ValidationError(detail={"login_method": ["Your enterprise requires passwordless method"]})
        except UserAuthFailedException:
            raise ValidationError(detail={"master_password_hash": ["The master password is not correct"]})

        # Update the master password cipher
        master_password_cipher = request.data.get("master_password_cipher")
        master_pwd_item_obj = self.cipher_service.get_master_pwd_item(user_id=user.user_id)
        if master_password_cipher:
            if not master_pwd_item_obj:
                serializer = VaultItemSerializer(
                    data=master_password_cipher, **{"context": self.get_serializer_context()}
                )
                serializer.is_valid(raise_exception=True)
                cipher_detail = serializer.save()
                cipher_detail = json.loads(json.dumps(cipher_detail))
                new_cipher = self._create_master_pwd_cipher(cipher_data=cipher_detail)
                PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user.user_id]).send(
                    data={"id": str(new_cipher.cipher_id)}
                )
            else:
                serializer = UpdateVaultItemSerializer(
                    data=master_password_cipher, **{"context": self.get_serializer_context()}
                )
                serializer.is_valid(raise_exception=True)
                cipher_detail = serializer.save()
                cipher_detail = json.loads(json.dumps(cipher_detail))
                master_password_cipher_obj = self._update_master_pwd_cipher(
                    master_pwd_item_obj=master_pwd_item_obj, cipher_data=cipher_detail
                )
                PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[request.user.user_id]).send(
                    data={"id": str(master_password_cipher_obj.cipher_id)}
                )

        # Re-create token
        if settings.SELF_HOSTED:
            device_access_token = request.auth
            new_device_access_token = self.device_service.fetch_device_access_token(
                device=device_access_token.device, renewal=True, sso_token_id=True
            )
            access_token = new_device_access_token.access_token

            mail_user_ids = result.get("mail_user_ids")
            # Sending mail when user changes master password
            if user.user_id in mail_user_ids:
                device = detect_device(ua_string=self.get_client_agent())
                ip_location = get_ip_location(ip=get_ip_by_request(request))
                browser = device.get("browser", None)
                browser = "" if browser is None else browser.get("family") + " " + browser.get("version", "")
                os = device.get("os", None)
                os = "" if os is None else os.get("family", "") + " " + os.get("version", "")
                location = ip_location.get("location", None)
                # Get location
                if location:
                    city = location.get("city", "")
                    country = location.get("country_name", "")
                    city_country = []
                    if city is not None and city != "":
                        city_country.append(city)
                    if country is not None and country != "":
                        city_country.append(country)
                    user_location = ", ".join(city_country)
                else:
                    user_location = ""
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_sending", **{
                        "user": user,
                        "job": PWD_MASTER_PASSWORD_CHANGED,
                        "changed_time": datetime.utcfromtimestamp(now()).strftime('%H:%M:%S %d-%m-%Y') + " (UTC+00)",
                        "account": user.email,
                        "location": user_location,
                        "ip": ip_location.get("ip", ""),
                        "os": os,
                        "browser": browser,
                    }
                )
            return Response(status=status.HTTP_200_OK, data={"success": True, "token": access_token})

        return Response(status=status.HTTP_200_OK, data={
            "notification": result.get("notification"),
            "client": result.get("client")
        })

    @action(methods=["post"], detail=False)
    def new_password(self, request, *args, **kwargs):
        return self.password(request, *args, **kwargs)

    @action(methods=["post"], detail=False)
    def check_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        master_password_hash = serializer.validated_data.get("master_password_hash")
        try:
            user = self.user_service.retrieve_by_email(email=email)
            valid = self.user_service.check_master_password(user=user, master_password_hash=master_password_hash)
        except UserDoesNotExistException:
            valid = False
        return Response(status=status.HTTP_200_OK, data={"valid": valid})

    @action(methods=["post"], detail=False)
    def password_hint(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        try:
            user = self.user_service.retrieve_by_id(user_id=user_id)
            if user.activated is False:
                raise ValidationError(detail={"email": ["There’s no account associated with this email"]})
        except UserDoesNotExistException:
            raise ValidationError(detail={"email": ["There’s no account associated with this email"]})
        master_password_hint = user.master_password_hint
        if settings.SELF_HOSTED:
            # Sending master password hint mail
            job = PWD_HINT_FOR_MASTER_PASSWORD if master_password_hint else PWD_NO_MASTER_PASSWORD_HINT
            BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                func_name="notify_sending", **{
                    "user": user, "job": job, "hint": master_password_hint
                }
            )
            return Response(status=status.HTTP_200_OK, data={"success": True})
        return Response(status=status.HTTP_200_OK, data={"master_password_hint": master_password_hint})

    @action(methods=["post"], detail=False)
    def revoke_all_sessions(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        master_password_hash = serializer.validated_data.get("master_password_hash")
        if not self.user_service.check_master_password(user=user, master_password_hash=master_password_hash):
            raise ValidationError(detail={"master_password_hash": ["The master password is not correct"]})
        self.user_service.revoke_all_sessions(user)
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def delete_me(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        master_password_hash = serializer.validated_data.get("master_password_hash")
        if not self.user_service.check_master_password(user=user, master_password_hash=master_password_hash):
            raise ValidationError(detail={"master_password_hash": ["The master password is not correct"]})
        self.user_service.delete_locker_user(user=user)
        # Sending mail when user deletes account
        if settings.SELF_HOSTED:
            BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                func_name="notify_sending", **{
                    "destinations": [{"email": user.email, "name": user.full_name, "language": user.language}],
                    "job": PWD_ACCOUNT_DELETED,
                    "email": user.email
                }
            )
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def purge_me(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        master_password_hash = serializer.validated_data.get("master_password_hash")
        if not self.user_service.check_master_password(user=user, master_password_hash=master_password_hash):
            raise ValidationError(detail={"master_password_hash": ["The master password is not correct"]})
        notification = self.user_service.purge_user(user=user)

        if settings.SELF_HOSTED:
            # Send web notification
            for cipher_member in notification:
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_sending", **{
                        "user_ids": [cipher_member["shared_member"]],
                        # "user": notification_users_dict.get(cipher_member["shared_member"]),
                        "job": PWD_DELETE_SHARE_ITEM,
                        "owner": user.full_name,
                        "cipher_id": cipher_member["id"]
                    }
                )
            return Response(status=status.HTTP_200_OK, data={"success": True})
        return Response(status=status.HTTP_200_OK, data=notification)

    @action(methods=["get", "put"], detail=False)
    def onboarding_process(self, request, *args, **kwargs):
        user = self.request.user
        onboarding_process = user.onboarding_process
        if request.method == "GET":
            return Response(status=200, data=onboarding_process)
        elif request.method == "PUT":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            vault_to_dashboard = validated_data.get(
                "vault_to_dashboard", onboarding_process.get(ONBOARDING_CATEGORY_TO_DASHBOARD)
            )
            welcome = validated_data.get("welcome", onboarding_process.get(ONBOARDING_CATEGORY_WELCOME))
            tutorial = validated_data.get("tutorial", onboarding_process.get(ONBOARDING_CATEGORY_TUTORIAL))
            tutorial_process = validated_data.get(
                "tutorial_process", onboarding_process.get(ONBOARDING_CATEGORY_TUTORIAL_PROCESS, [])
            )
            enterprise_onboarding = validated_data.get(
                "enterprise_onboarding", onboarding_process.get(ONBOARDING_CATEGORY_ENTERPRISE)
            )
            enterprise_onboarding_skip = validated_data.get(
                "enterprise_onboarding_skip", onboarding_process.get(ONBOARDING_CATEGORY_ENTERPRISE_SKIP)
            )
            onboarding_process.update({
                ONBOARDING_CATEGORY_TO_DASHBOARD: vault_to_dashboard,
                ONBOARDING_CATEGORY_WELCOME: welcome,
                ONBOARDING_CATEGORY_TUTORIAL: tutorial,
                ONBOARDING_CATEGORY_TUTORIAL_PROCESS: tutorial_process,
                ONBOARDING_CATEGORY_ENTERPRISE: enterprise_onboarding,
                ONBOARDING_CATEGORY_ENTERPRISE_SKIP: enterprise_onboarding_skip,
            })
            user = self.user_service.update_user(user_id=user.user_id, user_update_data={
                "onboarding_process": onboarding_process
            })
            return Response(status=200, data=user.onboarding_process)

    @action(methods=["get"], detail=False)
    def invitations(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        member_invitations = self.user_service.list_sharing_invitations(user=user)
        serializer = self.get_serializer(member_invitations, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["put"], detail=False)
    def invitation_update(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        user = self.request.user
        status_param = request.data.get("status")
        if status_param not in ["accept", "reject"]:
            raise ValidationError(detail={"status": ["This status is not valid"]})
        try:
            result = self.user_service.update_sharing_invitation(
                user=user,
                member_id=kwargs.get("pk"),
                status=status_param
            )
        except TeamMemberDoesNotExistException:
            return NotFound
        if settings.SELF_HOSTED and result.get("status") == "accept":
            owner_user_id = result.get("owner")
            try:
                owner = self.user_service.retrieve_by_id(user_id=owner_user_id)
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_sending", **{
                        "user": owner,
                        "job": PWD_CONFIRM_INVITATION,
                        "team_name": result.get("team_name"),
                        "member_email": user.email,
                        "member_name": user.full_name
                    }
                )
            except UserDoesNotExistException:
                pass
            return Response(status=status.HTTP_200_OK, data={"success": True})
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def family(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request)
        team_ids = self.user_service.list_team_ids_owner_family_plan(user_id=user.user_id)
        return Response(status=status.HTTP_200_OK, data=list(team_ids))

    @action(methods=["get"], detail=False)
    def devices(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        devices = self.user_service.list_user_devices(user_id=user.user_id)
        serializer = self.get_serializer(devices, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["delete"], detail=False)
    def device_destroy(self, request, *args, **kwargs):
        user = request.user
        device_identifier = kwargs.get("pk")
        self.check_pwd_session_auth(request)
        try:
            sso_token_ids = self.user_service.remove_user_device(
                user_id=user.user_id, device_identifier=device_identifier
            )
        except DeviceDoesNotExistException:
            raise NotFound
        return Response(status=status.HTTP_200_OK, data={"sso_token_ids": sso_token_ids})

    @action(methods=["get"], detail=False)
    def exist(self, request, *args, **kwargs):
        exist = self.user_service.check_exist()
        return Response(status=status.HTTP_200_OK, data={"exist": exist})

    @action(methods=["post"], detail=False)
    def prelogin(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        try:
            user = self.user_service.retrieve_by_email(
                email=email
            )
            login_method = user.login_method
            require_passwordless = self.user_service.is_require_passwordless(user_id=user.user_id)
            return Response(
                status=status.HTTP_200_OK,
                data={
                    "email": user.email,
                    "name": user.full_name or user.username,
                    "avatar": user.get_avatar(),
                    "activated": user.activated,
                    "set_up_passwordless": True if user.fd_credential_id else False,
                    "login_method": login_method,
                    "require_passwordless": require_passwordless
                }
            )
        except UserDoesNotExistException:
            raise ValidationError(detail={"email": ["User with email does not exist"]})

    @action(methods=["post"], detail=False)
    def reset_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            self.user_service.reset_password_by_token(
                token_value=validated_data.get("token"),
                new_password=validated_data.get("new_password"),
                new_key=validated_data.get("new_key"),
                secret=settings.SECRET_KEY
            )
        except UserResetPasswordTokenInvalidException:
            raise ValidationError(detail=[{"token": "The reset password token is invalid"}])
        return Response(status=status.HTTP_204_NO_CONTENT)
