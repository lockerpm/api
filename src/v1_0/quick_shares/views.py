import json

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models.quick_shares.quick_shares import QuickShare
from shared.constants.account import LOGIN_METHOD_PASSWORDLESS
from shared.constants.ciphers import CIPHER_TYPE_MASTER_PASSWORD
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.quick_share_pwd_permission import QuickSharePwdPermission
from shared.utils.app import now, diff_list
from v1_0.quick_shares.serializers import CreateQuickShareSerializer, ListQuickShareSerializer, \
    PublicQuickShareSerializer, CheckAccessQuickShareSerializer
from v1_0.general_view import PasswordManagerViewSet


class QuickSharePwdViewSet(PasswordManagerViewSet):
    permission_classes = (QuickSharePwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            self.serializer_class = CreateQuickShareSerializer
        elif self.action in ["list", "retrieve"]:
            self.serializer_class = ListQuickShareSerializer
        elif self.action == "public":
            self.serializer_class = PublicQuickShareSerializer
        elif self.action in ["access", "otp"]:
            self.serializer_class = CheckAccessQuickShareSerializer
        return super().get_serializer_class()

    def get_cipher(self, cipher_id):
        try:
            cipher = self.cipher_repository.get_by_id(cipher_id=cipher_id)
            if cipher.team:
                self.check_object_permissions(request=self.request, obj=cipher)
            else:
                if cipher.user != self.request.user:
                    raise NotFound
            return cipher
        except ObjectDoesNotExist:
            raise NotFound

    def get_object(self):
        try:
            quick_share = QuickShare.objects.get(id=self.kwargs.get("pk"))
            self.get_cipher(cipher_id=quick_share.cipher_id)
            return quick_share
        except ObjectDoesNotExist:
            raise NotFound

    def get_quick_share_access_obj(self):
        try:
            quick_share = QuickShare.objects.get(id=self.kwargs.get("pk"))
            return quick_share
        except ObjectDoesNotExist:
            raise NotFound

    def get_queryset(self):
        user = self.request.user
        exclude_types = []
        if user.login_method == LOGIN_METHOD_PASSWORDLESS:
            exclude_types = [CIPHER_TYPE_MASTER_PASSWORD]
        cipher_ids = self.cipher_repository.get_multiple_by_user(
            user=user, exclude_types=exclude_types, only_personal=True
        ).values_list('id', flat=True)
        quick_share = QuickShare.objects.filter(cipher_id__in=list(cipher_ids)).order_by('-creation_date')
        return quick_share

    def list(self, request, *args, **kwargs):
        # self.check_pwd_session_auth(request)
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        validated_data = json.loads(json.dumps(validated_data))
        cipher_id = validated_data.get("cipher_id")
        self.get_cipher(cipher_id=cipher_id)
        quick_share = QuickShare.create(**validated_data)
        return Response(status=200, data={
            "id": quick_share.id,
            "cipher_id": quick_share.cipher_id,
            "access_id": quick_share.access_id
        })

    def retrieve(self, request, *args, **kwargs):
        # self.check_pwd_session_auth(request=request)
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # self.check_pwd_session_auth(request=request)
        quick_share = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        validated_data = json.loads(json.dumps(validated_data))
        quick_share.revision_date = now()
        quick_share.data = validated_data.get("data") or quick_share.data
        quick_share.key = validated_data.get("key") or quick_share.key
        quick_share.password = validated_data.get("password") or quick_share.password
        quick_share.max_access_count = validated_data.get("max_access_count") or quick_share.max_access_count
        quick_share.expired_date = validated_data.get("expired_date") or quick_share.expired_date
        quick_share.is_public = validated_data.get("is_public") or quick_share.is_public
        quick_share.disabled = validated_data.get("disabled") or quick_share.disabled
        quick_share.require_otp = validated_data.get("require_otp") or quick_share.require_otp
        quick_share.save()

        quick_share_emails = list(quick_share.quick_share_emails.values_list('email', flat=True))
        emails_data = validated_data.get("emails", [])
        emails = [email_data.get("email") for email_data in emails_data]
        removed_emails = diff_list(quick_share_emails, emails)
        added_emails = diff_list(emails, quick_share_emails)
        if removed_emails:
            quick_share.quick_share_emails.filter(email__in=removed_emails).delete()
        if added_emails:
            added_emails_data = [{"email": e} for e in added_emails]
            quick_share.quick_share_emails.model.create_multiple(quick_share, added_emails_data)

        return Response(status=200, data={
            "id": quick_share.id,
            "cipher_id": quick_share.cipher_id,
            "access_id": quick_share.access_id
        })

    def destroy(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        return super().destroy(request, *args, **kwargs)

    @action(methods=["post"], detail=False)
    def public(self, request, *args, **kwargs):
        quick_share = self.get_quick_share_access_obj()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        code = validated_data.get("code")
        if not quick_share.check_valid_access(email=email, code=code):
            raise ValidationError({"non_field_errors": [gen_error("9000")]})
        quick_share.access_count = F('access_count') + 1
        quick_share.revision_date = now()
        quick_share.save()
        quick_share.refresh_from_db()
        if email:
            try:
                quick_share_email = quick_share.quick_share_emails.get(email=email)
                quick_share_email.clear_code()
            except ObjectDoesNotExist:
                pass

        result = ListQuickShareSerializer(quick_share, many=False)
        return Response(status=200, data=result.data)

    @action(methods=["post"], detail=False)
    def access(self, request, *args, **kwargs):
        quick_share = self.get_quick_share_access_obj()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        if quick_share.is_public is True or quick_share.quick_share_emails.filter(email=email).exists():
            return Response(status=200, data={"success": True})
        raise ValidationError(detail={"email": ["The email is not valid"]})

    @action(methods=["post"], detail=False)
    def otp(self, request, *args, **kwargs):
        quick_share = self.get_quick_share_access_obj()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        try:
            quick_share_email = quick_share.quick_share_emails.get(email=email)

        except ObjectDoesNotExist:
            raise ValidationError(detail={"email": ["The email is not valid"]})
        quick_share_email.set_random_code()
        return Response(status=200, data={"code": quick_share_email.code})
