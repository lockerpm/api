from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models.notifications.notification_settings import NotificationSetting
from shared.constants.members import *
from shared.constants.emergency_access import *
from shared.constants.user_notification import NOTIFY_EMERGENCY_ACCESS, NOTIFY_CHANGE_MASTER_PASSWORD
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.emergency_access_pwd_permission import EmergencyAccessPermission
from shared.services.pm_sync import PwdSync, SYNC_EMERGENCY_ACCESS
from cystack_models.models.emergency_access.emergency_access import EmergencyAccess
from v1_0.emergency_access.serializers import EmergencyAccessGranteeSerializer, EmergencyAccessGrantorSerializer, \
    InviteEmergencyAccessSerializer, PasswordEmergencyAccessSerializer
from v1_0.sync.serializers import SyncCipherSerializer
from v1_0.apps import PasswordManagerViewSet


class EmergencyAccessPwdViewSet(PasswordManagerViewSet):
    permission_classes = (EmergencyAccessPermission, )
    lookup_value_regex = r'[0-9a-z\-]+'
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "trusted":
            self.serializer_class = EmergencyAccessGranteeSerializer
        elif self.action == "granted":
            self.serializer_class = EmergencyAccessGrantorSerializer
        elif self.action == "invite":
            self.serializer_class = InviteEmergencyAccessSerializer
        elif self.action == "password":
            self.serializer_class = PasswordEmergencyAccessSerializer
        return super(EmergencyAccessPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            emergency_access = self.emergency_repository.get_by_id(emergency_access_id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=emergency_access)
            return emergency_access
        except EmergencyAccess.DoesNotExist:
            raise NotFound

    def allow_emergency_access(self, user):
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        plan_obj = current_plan.get_plan_obj()
        if plan_obj.allow_emergency_access() is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})
        return user

    @action(methods=["get"], detail=False)
    def trusted(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        trusted_grantees = self.emergency_repository.get_multiple_by_grantor(grantor=user)
        serializer = self.get_serializer(trusted_grantees, many=True)
        return Response(status=200, data=serializer.data)

    @action(methods=["get"], detail=False)
    def granted(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        granted_grantors = self.emergency_repository.get_multiple_by_grantee(grantee=user)
        serializer = self.get_serializer(granted_grantors, many=True)
        return Response(status=200, data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        status = emergency_access.status
        grantor_user_id = emergency_access.grantor.user_id
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = NotificationSetting.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantor_user_id, grantee_user_id]
        )
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantor_user_id, grantee_user_id]
        )
        self.emergency_repository.delete_emergency_access(emergency_access)
        return Response(status=200, data={
            "grantor_user_id": grantor_user_id,
            "grantee_user_id": grantee_user_id,
            "status": status,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["post"], detail=False)
    def invite(self, request, *args, **kwargs):
        grantor = self.request.user
        grantor = self.allow_emergency_access(user=grantor)
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        new_emergency_access = self.emergency_repository.invite_emergency_access(
            access_type=validated_data.get("type"),
            wait_time_days=validated_data.get("wait_time_days"),
            grantor=grantor,
            grantee=validated_data.get("grantee"),
            email=validated_data.get("email"),
            key_encrypted=validated_data.get("key")
        )
        # Send notification via ws for grantee
        mail_user_ids = []
        notification_user_ids = []
        if new_emergency_access.grantee_id:
            PwdSync(event=SYNC_EMERGENCY_ACCESS, user_ids=[new_emergency_access.grantee_id]).send()
            mail_user_ids = NotificationSetting.get_user_mail(
                category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[new_emergency_access.grantee_id]
            )
            notification_user_ids = NotificationSetting.get_user_notification(
                category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[new_emergency_access.grantee_id]
            )

        return Response(status=200, data={
            "id": new_emergency_access.id,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["post"], detail=False)
    def reinvite(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        self.allow_emergency_access(user=emergency_access.grantor)
        # Send notification via ws for grantee
        if emergency_access.grantee_id:
            PwdSync(event=SYNC_EMERGENCY_ACCESS, user_ids=[emergency_access.grantee_id]).send()
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = []
        notification_user_ids = []
        if grantee_user_id:
            mail_user_ids = NotificationSetting.get_user_mail(
                category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
            )
            notification_user_ids = NotificationSetting.get_user_notification(
                category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
            )

        return Response(status=200, data={
            "id": emergency_access.id, "grantee_user_id": grantee_user_id, "grantee_email": emergency_access.email,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["post"], detail=True)
    def accept(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        if emergency_access.status != EMERGENCY_ACCESS_STATUS_INVITED:
            raise NotFound
        if emergency_access.key_encrypted:
            emergency_access = self.emergency_repository.confirm_emergency_access(
                emergency_access, emergency_access.key_encrypted
            )
        else:
            emergency_access = self.emergency_repository.accept_emergency_access(emergency_access)

        grantor_user_id = emergency_access.grantor.user_id
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = NotificationSetting.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantor_user_id, grantee_user_id]
        )
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantor_user_id, grantee_user_id]
        )

        return Response(status=200, data={
            "success": True,
            "grantor_user_id": grantor_user_id,
            "grantee_user_id": grantee_user_id,
            "grantee_email": emergency_access.email,
            "status": emergency_access.status,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["get"], detail=True)
    def public_key(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        public_key = emergency_access.grantee.public_key
        return Response(status=200, data={"public_key": public_key})

    @action(methods=["post"], detail=True)
    def confirm(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        ip = request.data.get("ip")
        emergency_access = self.get_object()
        self.allow_emergency_access(user=emergency_access.grantor)
        key_encrypted = request.data.get("key")
        if not key_encrypted:
            raise ValidationError(detail={"key": ["This field is required"]})
        if emergency_access.status != EMERGENCY_ACCESS_STATUS_ACCEPTED:
            raise NotFound
        self.emergency_repository.confirm_emergency_access(emergency_access, key_encrypted)
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = NotificationSetting.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        return Response(status=200, data={
            "grantee_user_id": grantee_user_id,
            "grantee_email": emergency_access.email,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["post"], detail=True)
    def initiate(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        if emergency_access.status != EMERGENCY_ACCESS_STATUS_CONFIRMED:
            raise NotFound
        self.emergency_repository.initiate_emergency_access(emergency_access)
        mail_user_ids = NotificationSetting.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[emergency_access.grantor.user_id]
        )
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[emergency_access.grantor.user_id]
        )
        return Response(status=200, data={
            "type": emergency_access.type,
            "grantor_user_id": emergency_access.grantor.user_id,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["post"], detail=True)
    def reject(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        self.allow_emergency_access(user=emergency_access.grantor)
        if emergency_access.status not in [EMERGENCY_ACCESS_STATUS_RECOVERY_INITIATED,
                                           EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED]:
            raise NotFound
        self.emergency_repository.reject_emergency_access(emergency_access)
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = NotificationSetting.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )

        return Response(status=200, data={
            "grantee_user_id": grantee_user_id,
            "grantee_email": emergency_access.email,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["post"], detail=True)
    def approve(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        self.allow_emergency_access(user=emergency_access.grantor)
        if emergency_access.status != EMERGENCY_ACCESS_STATUS_RECOVERY_INITIATED:
            raise NotFound
        self.emergency_repository.approve_emergency_access(emergency_access)
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = NotificationSetting.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        notification_user_ids = NotificationSetting.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        return Response(status=200, data={
            "grantee_user_id": grantee_user_id,
            "grantee_email": emergency_access.email,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        })

    @action(methods=["post"], detail=True)
    def view(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        if emergency_access.type != EMERGENCY_ACCESS_TYPE_VIEW or emergency_access.status != EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED:
            raise NotFound
        ciphers = self.cipher_repository.get_multiple_by_user(
            user=emergency_access.grantor, only_personal=True
        ).prefetch_related('collections_ciphers')
        key_encrypted = emergency_access.key_encrypted

        return Response(status=200, data={
            "object": "emergencyAccessView",
            "ciphers": SyncCipherSerializer(ciphers, many=True, context={"user": emergency_access.grantor}).data,
            "key_encrypted": key_encrypted
        })

    @action(methods=["post"], detail=True)
    def takeover(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        if emergency_access.type != EMERGENCY_ACCESS_TYPE_TAKEOVER or \
                emergency_access.status != EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED:
            raise NotFound
        grantor = emergency_access.grantor
        result = {
            "obj": "emergencyAccessTakeover",
            "key_encrypted": emergency_access.key_encrypted,
            "kdf": grantor.kdf,
            "kdf_iterations": grantor.kdf_iterations
        }
        return Response(status=200, data=result)

    @action(methods=["post"], detail=True)
    def password(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        emergency_access = self.get_object()
        if emergency_access.type != EMERGENCY_ACCESS_TYPE_TAKEOVER or \
                emergency_access.status != EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED:
            raise NotFound
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        key = validated_data.get("key")
        new_master_password_hash = validated_data.get("new_master_password_hash")

        grantor = emergency_access.grantor
        self.user_repository.change_master_password_hash(
            user=grantor, new_master_password_hash=new_master_password_hash, key=key
        )
        self.user_repository.revoke_all_sessions(user=grantor)
        # Remove grantor from all teams unless Owner
        grantor_teams = self.team_repository.get_multiple_team_by_user(
            user=grantor, status=PM_MEMBER_STATUS_CONFIRMED, personal_share=False
        ).order_by('-creation_date')
        for grantor_team in grantor_teams:
            member = grantor_team.team_members.get(user=grantor)
            if member.role.name != MEMBER_ROLE_OWNER:
                member.delete()

        mail_user_ids = NotificationSetting.get_user_mail(
            category_id=NOTIFY_CHANGE_MASTER_PASSWORD, user_ids=[grantor.user_id]
        )

        return Response(status=200, data={"notification": True if grantor.user_id in mail_user_ids else False})
