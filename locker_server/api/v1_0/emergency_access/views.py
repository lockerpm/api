import json
from datetime import datetime

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.emergency_access_pwd_permission import \
    EmergencyAccessPwdPermission
from locker_server.api.v1_0.ciphers.serializers import VaultItemSerializer, UpdateVaultItemSerializer
from locker_server.api.v1_0.sync.serializers import SyncCipherSerializer
from locker_server.core.exceptions.cipher_exception import *
from locker_server.core.exceptions.collection_exception import *
from locker_server.core.exceptions.emergency_access_exception import EmergencyAccessDoesNotExistException, \
    EmergencyAccessEmailExistedException, EmergencyAccessGranteeExistedException
from locker_server.core.exceptions.team_exception import *
from locker_server.core.exceptions.team_member_exception import *
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.shared.constants.emergency_access import EMERGENCY_ACCESS_STATUS_ACCEPTED, \
    EMERGENCY_ACCESS_STATUS_CONFIRMED
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY
from locker_server.shared.external_services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_UPDATE
from locker_server.shared.external_services.user_notification.list_jobs import PWD_JOIN_EMERGENCY_ACCESS, \
    PWD_DECLINED_INVITATION_EMERGENCY_ACCESS, PWD_CONFIRM_EMERGENCY_ACCESS, PWD_EMERGENCY_ACCESS_GRANTED, \
    PWD_ACCEPT_INVITATION_EMERGENCY_ACCESS, PWD_NEW_EMERGENCY_ACCESS_REQUEST, PWD_EMERGENCY_REQUEST_DECLINED, \
    PWD_EMERGENCY_REQUEST_ACCEPTED, PWD_MASTER_PASSWORD_CHANGED
from locker_server.shared.external_services.user_notification.notification_sender import \
    SENDING_SERVICE_WEB_NOTIFICATION
from locker_server.shared.utils.app import now
from .serializers import EmergencyAccessGranteeSerializer, EmergencyAccessGrantorSerializer, \
    InviteEmergencyAccessSerializer, PasswordEmergencyAccessSerializer, ViewOrgSerializer


class EmergencyAccessPwdViewSet(APIBaseViewSet):
    permission_classes = (EmergencyAccessPwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9a-z-]+'

    def get_throttles(self):
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == "trusted":
            self.serializer_class = EmergencyAccessGranteeSerializer
        elif self.action == "granted":
            self.serializer_class = EmergencyAccessGrantorSerializer
        elif self.action == "invite":
            self.serializer_class = InviteEmergencyAccessSerializer
        elif self.action == "password":
            self.serializer_class = PasswordEmergencyAccessSerializer
        return super().get_serializer_class()

    def get_object(self):
        try:
            emergency_access = self.emergency_access_service.get_by_id(emergency_access_id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=emergency_access)
            return emergency_access
        except EmergencyAccessDoesNotExistException:
            raise NotFound

    def allow_emergency_access(self, user):
        current_plan = self.user_service.get_current_plan(user=user)
        plan_obj = current_plan.pm_plan
        if self.user_service.is_active_enterprise_member(user_id=user.user_id) is False and \
                plan_obj.emergency_access is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})
        return user

    @staticmethod
    def send_invite_mail(owner, grantee_user, grantee_email):
        if not grantee_email and not grantee_user:
            return
        if grantee_user:
            destinations = [{
                "email": grantee_user.email, "name": grantee_user.full_name, "language": grantee_user.language
            }]
        else:
            destinations = [{
                "email": grantee_email,
                "name": "bạn" if owner.language == "vi" else "there",
                "language": owner.language
            }]
        BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
            func_name="notify_sending", **{
                "destinations": destinations,
                "job": PWD_JOIN_EMERGENCY_ACCESS,
                "grantor_email": owner.email,
                "grantor_name": owner.full_name
            }
        )

    @staticmethod
    def send_invite_notification(owner, grantee_user):
        BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
            func_name="notify_sending", **{
                "user_ids": [grantee_user.user_id],
                "job": PWD_JOIN_EMERGENCY_ACCESS,
                "services": [SENDING_SERVICE_WEB_NOTIFICATION],
                "grantor_email": owner.email,
                "grantor_name": owner.full_name,
                "is_grantee": True
            }
        )

    @staticmethod
    def send_status_mail(job, user_ids, **data):
        data.update({
            "user_ids": user_ids, "job": job,
        })
        BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(func_name="notify_sending", **data)

    @staticmethod
    def send_status_notification(job, user_ids, **data):
        data.update({
            "user_ids": user_ids, "job": job, "services": [SENDING_SERVICE_WEB_NOTIFICATION]
        })
        BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(func_name="notify_sending", **data)

    @action(methods=["get"], detail=False)
    def trusted(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        trusted_grantees = self.emergency_access_service.list_by_grantor_id(grantor_id=user.user_id)
        serializer = self.get_serializer(trusted_grantees, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["get"], detail=False)
    def granted(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        granted_grantors = self.emergency_access_service.list_by_grantee_id(grantee_id=user.user_id)
        serializer = self.get_serializer(granted_grantors, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        result = self.emergency_access_service.destroy_emergency_access(
            user=user,
            emergency_access=emergency_access,
            full_name=user.full_name or request.data.get("user_fullname")
        )
        if settings.SELF_HOSTED:
            emergency_access_status = result.get("status")
            grantor_user_id = result.get("grantor_user_id")
            grantee_user_id = result.get("grantee_user_id")
            mail_user_ids = result.get("mail_user_ids", [])
            notification_user_ids = result.get("notification_user_ids", [])
            if user.user_id == grantee_user_id and emergency_access_status == "invited":
                if grantor_user_id in mail_user_ids:
                    self.send_status_mail(PWD_DECLINED_INVITATION_EMERGENCY_ACCESS, user_ids=[grantor_user_id], **{
                        "grantee_email": user.email,
                        "grantee_name": user.full_name
                    })
                if grantor_user_id in notification_user_ids:
                    self.send_status_notification(
                        PWD_DECLINED_INVITATION_EMERGENCY_ACCESS, user_ids=[grantor_user_id], **{
                            "grantee_email": user.email,
                            "grantee_name": user.full_name
                        }
                    )
            return Response(status=status.HTTP_200_OK, data={"success": True})
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["post"], detail=False)
    def invite(self, request, *args, **kwargs):
        grantor = self.request.user
        grantor = self.allow_emergency_access(user=grantor)
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")

        try:
            grantee = self.user_service.retrieve_by_email(email=email)
            if grantee.activated is False:
                raise ValidationError(detail={"email": ["Grantee email does not exist"]})
            validated_data["grantee_id"] = grantee.user_id
            validated_data["email"] = None
        except UserDoesNotExistException:
            raise ValidationError(detail={"email": ["Grantee email does not exist"]})
        try:
            new_emergency_access, mail_user_ids, \
                notification_user_ids = self.emergency_access_service.invite_emergency_access(
                grantor=grantor,
                emergency_access_type=validated_data.get("type"),
                wait_time_days=validated_data.get("wait_time_days"),
                grantee_id=validated_data.get("grantee_id"),
                email=validated_data.get("email"),
                key=validated_data.get("key"),
                grantor_fullname=grantor.full_name or self.request.data.get("grantor_fullname")
            )
        except UserDoesNotExistException:
            raise ValidationError(detail={'email': ["Grantee email does not exist"]})
        except EmergencyAccessGranteeExistedException:
            raise ValidationError(detail={"email": ["The emergency already exists"]})
        except EmergencyAccessEmailExistedException:
            raise ValidationError(detail={"email": ["The emergency already exists"]})

        # Send notification via ws for grantee
        if settings.SELF_HOSTED and new_emergency_access.grantee:
            if mail_user_ids:
                self.send_invite_mail(grantor, new_emergency_access.grantee, new_emergency_access.email)
            if notification_user_ids:
                self.send_invite_notification(grantor, new_emergency_access.grantee)
            return Response(status=status.HTTP_200_OK, data={"id": new_emergency_access.emergency_access_id})

        return Response(status=status.HTTP_200_OK, data={
            "id": new_emergency_access.emergency_access_id,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["post"], detail=False)
    def reinvite(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        self.allow_emergency_access(user=emergency_access.grantor)

        emergency_access, mail_user_ids, notification_user_ids = self.emergency_access_service.reinvite_emergency_access(
            emergency_access=emergency_access,
            grantor_fullname=emergency_access.grantor.full_name or request.data.get("grantor_fullname")
        )
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None

        if settings.SELF_HOSTED:
            grantee_email = emergency_access.email
            grantee_user = emergency_access.grantee
            if grantee_user:
                if mail_user_ids:
                    self.send_invite_mail(request.user, grantee_user, grantee_email)
                if notification_user_ids:
                    self.send_invite_notification(request.user, grantee_user)
            else:
                self.send_invite_mail(owner=request.user, grantee_user=grantee_user, grantee_email=grantee_email)
            return Response(status=status.HTTP_201_CREATED, data={"id": emergency_access.emergency_access_id})

        return Response(status=status.HTTP_200_OK, data={
            "id": emergency_access.emergency_access_id,
            "grantee_user_id": grantee_user_id,
            "grantee_email": emergency_access.email,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["post"], detail=True)
    def accept(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        grantee_fullname = None
        if emergency_access.grantee:
            grantee_fullname = emergency_access.grantee.full_name
        if not grantee_fullname:
            grantee_fullname = request.data.get("grantee_fullname")
        try:
            result = self.emergency_access_service.accept_emergency_access(
                emergency_access=emergency_access,
                grantee_fullname=grantee_fullname
            )
        except EmergencyAccessDoesNotExistException:
            raise NotFound
        grantee_user = request.user
        grantor_user_id = emergency_access.grantor.user_id
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = result.get("mail_user_ids", [])
        notification_user_ids = result.get("notification_user_ids", [])
        if emergency_access.status == EMERGENCY_ACCESS_STATUS_ACCEPTED:
            if grantor_user_id in mail_user_ids:
                self.send_status_mail(PWD_CONFIRM_EMERGENCY_ACCESS, user_ids=[grantor_user_id], **{
                    "grantee_email": grantee_user.email,
                    "grantee_name": grantee_user.full_name
                })
            if grantor_user_id in notification_user_ids:
                self.send_status_notification(PWD_CONFIRM_EMERGENCY_ACCESS, user_ids=[grantor_user_id], **{
                    "grantee_email": grantee_user.email,
                    "grantee_name": grantee_user.full_name,
                    "is_grantor": True
                })

        if emergency_access.status == EMERGENCY_ACCESS_STATUS_CONFIRMED:
            grantor = emergency_access.grantor
            if grantee_user_id in mail_user_ids:
                self.send_status_mail(PWD_EMERGENCY_ACCESS_GRANTED, user_ids=[grantee_user_id], **{
                    "grantor_email": grantor.email,
                    "grantor_name": grantor.full_name
                })
            if grantee_user_id in notification_user_ids:
                self.send_status_notification(PWD_EMERGENCY_ACCESS_GRANTED, user_ids=[grantee_user_id], **{
                    "grantor_email": grantor.email,
                    "grantor_name": grantor.full_name,
                    "is_grantee": True
                })
            if grantor_user_id in mail_user_ids:
                self.send_status_mail(PWD_ACCEPT_INVITATION_EMERGENCY_ACCESS, user_ids=[grantor_user_id], **{
                    "grantee_email": grantee_user.email,
                    "grantee_name": grantee_user.full_name
                })
            if grantor_user_id in notification_user_ids:
                self.send_status_notification(
                    PWD_ACCEPT_INVITATION_EMERGENCY_ACCESS, user_ids=[grantor_user_id], **{
                        "grantee_email": grantee_user.email,
                        "grantee_name": grantee_user.full_name,
                        "is_grantor": True
                    }
                )

        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["get"], detail=True)
    def public_key(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        public_key = emergency_access.grantee.public_key if emergency_access.grantee else None
        return Response(status=status.HTTP_200_OK, data={"public_key": public_key})

    @action(methods=["post"], detail=True)
    def confirm(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        ip = self.get_ip()
        emergency_access = self.get_object()
        self.allow_emergency_access(user=emergency_access.grantor)
        key_encrypted = request.data.get("key")
        if not key_encrypted:
            raise ValidationError(detail={"key": ["This field is required"]})
        try:
            result = self.emergency_access_service.confirm_emergency_access(
                emergency_access=emergency_access,
                key=key_encrypted,

            )
        except EmergencyAccessDoesNotExistException:
            raise NotFound
        if settings.SELF_HOSTED:
            owner = request.user
            mail_user_ids = result.get("mail_user_ids", [])
            notification_user_ids = result.get("notification_user_ids", [])
            notify_data = {"grantor_email": owner.email, "grantor_name": owner.full_name, "is_grantee": True}
            # Sending mail
            self.send_status_mail(PWD_EMERGENCY_ACCESS_GRANTED, mail_user_ids, **notify_data)
            self.send_status_notification(PWD_EMERGENCY_ACCESS_GRANTED, notification_user_ids, **notify_data)
            return Response(status=status.HTTP_200_OK, data={"success": True})
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["post"], detail=True)
    def initiate(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        grantee_fullname = None
        if emergency_access.grantee:
            grantee_fullname = emergency_access.grantee.full_name
        if not grantee_fullname:
            grantee_fullname = request.data.get("grantee_fullname")
        try:
            result = self.emergency_access_service.initiate_emergency_access(
                emergency_access=emergency_access,
                grantee_fullname=grantee_fullname
            )
        except EmergencyAccessDoesNotExistException:
            raise NotFound
        if settings.SELF_HOSTED:
            grantee_user = request.user
            mail_user_ids = result.get("mail_user_ids", [])
            notification_user_ids = result.get("notification_user_ids", [])
            notify_data = {
                "request": emergency_access.emergency_access_type,
                "approve_after": emergency_access.wait_time_days,
                "grantee_email": grantee_user.email,
                "grantee_name": grantee_user.full_name,
                "is_grantor": True
            }
            # Sending mail
            self.send_status_mail(PWD_NEW_EMERGENCY_ACCESS_REQUEST, mail_user_ids, **notify_data)
            self.send_status_notification(PWD_NEW_EMERGENCY_ACCESS_REQUEST, notification_user_ids, **notify_data)
            return Response(status=status.HTTP_200_OK, data={"success": True})
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["post"], detail=True)
    def reject(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        self.allow_emergency_access(user=emergency_access.grantor)
        grantor_fullname = emergency_access.grantor.full_name or self.request.data.get("grantor_fullname")
        try:
            result = self.emergency_access_service.reject_emergency_access(
                emergency_access=emergency_access, grantor_fullname=grantor_fullname
            )
        except EmergencyAccessDoesNotExistException:
            raise NotFound
        if settings.SELF_HOSTED:
            grantor = request.user
            mail_user_ids = result.get("mail_user_ids", [])
            notification_user_ids = result.get("notification_user_ids", [])

            notify_data = {
                "grantor_email": grantor.email,
                "grantor_name": grantor.full_name,
                "is_grantee": True
            }
            # Sending email
            self.send_status_mail(PWD_EMERGENCY_REQUEST_DECLINED, mail_user_ids, **notify_data)
            self.send_status_notification(PWD_EMERGENCY_REQUEST_DECLINED, notification_user_ids, **notify_data)
            return Response(status=status.HTTP_200_OK, data={"success": True})
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["post"], detail=True)
    def approve(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        self.allow_emergency_access(user=emergency_access.grantor)
        grantor_fullname = emergency_access.grantor.full_name or self.request.data.get("grantor_fullname")
        try:
            result = self.emergency_access_service.approve_emergency_access(
                emergency_access=emergency_access, grantor_fullname=grantor_fullname
            )
        except EmergencyAccessDoesNotExistException:
            raise NotFound
        if settings.SELF_HOSTED:
            grantor = request.user
            mail_user_ids = result.get("mail_user_ids", [])
            notification_user_ids = result.get("notification_user_ids", [])
            notify_data = {
                "grantor_email": grantor.email,
                "grantor_name": grantor.full_name,
                "is_grantee": True
            }
            # Sending mail
            self.send_status_mail(PWD_EMERGENCY_REQUEST_ACCEPTED, mail_user_ids, **notify_data)
            self.send_status_notification(PWD_EMERGENCY_REQUEST_ACCEPTED, notification_user_ids, **notify_data)
            return Response(status=status.HTTP_200_OK, data={"success": True})
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["post"], detail=True)
    def view(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()

        try:
            ciphers, team_members = self.emergency_access_service.view_emergency_access(
                emergency_access=emergency_access
            )
        except EmergencyAccessDoesNotExistException:
            raise NotFound
        key_encrypted = emergency_access.key_encrypted
        organizations = []
        for team_member in team_members:
            organizations.append(ViewOrgSerializer(team_member, many=False).data)

        return Response(status=status.HTTP_200_OK, data={
            "object": "emergencyAccessView",
            "ciphers": SyncCipherSerializer(ciphers, many=True, context={"user": emergency_access.grantor}).data,
            "organizations": organizations,
            "key_encrypted": key_encrypted,
            "private_key": emergency_access.grantor.private_key
        })

    @action(methods=["post"], detail=True)
    def takeover(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        try:
            result = self.emergency_access_service.takeover_emergency_access(emergency_access=emergency_access)
        except EmergencyAccessDoesNotExistException:
            raise NotFound
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["post"], detail=True)
    def password(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        key = validated_data.get("key")
        new_master_password_hash = validated_data.get("new_master_password_hash")

        try:
            result = self.emergency_access_service.password_emergency_access(
                emergency_access=emergency_access,
                new_master_password_hash=new_master_password_hash,
                key=key
            )
        except EmergencyAccessDoesNotExistException:
            raise NotFound

        # Update the master password cipher
        user_id = emergency_access.grantor.user_id
        master_password_cipher = request.data.get("master_password_cipher")
        master_pwd_item_obj = self.cipher_service.get_master_pwd_item(user_id=user_id)
        if master_password_cipher:
            if not master_pwd_item_obj:
                request_context = self.request
                request_context.user = emergency_access.grantor
                serializer = VaultItemSerializer(
                    data=master_password_cipher, **{
                        "context": {'request': request_context, 'format': self.format_kwarg, 'view': self}
                    }
                )
                serializer.is_valid(raise_exception=True)
                cipher_detail = serializer.save()
                cipher_detail = json.loads(json.dumps(cipher_detail))
                new_cipher = self._create_master_pwd_cipher(cipher_data=cipher_detail)
                PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user_id]).send(
                    data={"id": str(new_cipher.cipher_id)}
                )
            else:
                request_context = self.request
                request_context.user = emergency_access.grantor
                serializer = UpdateVaultItemSerializer(
                    data=master_password_cipher, **{
                        "context": {'request': request_context, 'format': self.format_kwarg, 'view': self}
                    }
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

        if settings.SELF_HOSTED:
            grantor_user_id = result.get("grantor_user_id")
            mail_user_ids = result.get("mail_user_ids", [])
            if grantor_user_id in mail_user_ids:
                # Sending email
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_sending", **{
                        "user_ids": [grantor_user_id],
                        "job": PWD_MASTER_PASSWORD_CHANGED,
                        "changed_time": datetime.utcfromtimestamp(now()).strftime('%H:%M:%S %d-%m-%Y') + " (UTC+00)",
                    }
                )
            return Response(status=status.HTTP_200_OK, data={"success": True})
        return Response(status=status.HTTP_200_OK, data=result)

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

    @action(methods=["post"], detail=True)
    def id_password(self, request, *args, **kwargs):
        if settings.SELF_HOSTED:
            raise NotFound
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        try:
            result = self.emergency_access_service.id_password_emergency_access(emergency_access=emergency_access)
        except EmergencyAccessDoesNotExistException:
            raise NotFound
        return Response(status=status.HTTP_200_OK, data=result)
