import json

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

from core.utils.data_helpers import camel_snake_data
from cystack_models.models.quick_shares.quick_shares import QuickShare
from shared.background import LockerBackgroundFactory, BG_CIPHER
from shared.constants.account import LOGIN_METHOD_PASSWORDLESS
from shared.constants.ciphers import CIPHER_TYPE_MASTER_PASSWORD, IMMUTABLE_CIPHER_TYPES
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.quick_share_pwd_permission import QuickSharePwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_UPDATE, SYNC_EVENT_VAULT
from v1_0.ciphers.serializers import VaultItemSerializer, UpdateVaultItemSerializer, \
    MutipleItemIdsSerializer, MultipleMoveSerializer, ShareVaultItemSerializer, ImportCipherSerializer, \
    SyncOfflineCipherSerializer, DetailCipherSerializer, UpdateCipherUseSerializer
from v1_0.quick_shares.serializers import CreateQuickShareSerializer, ListQuickShareSerializer
from v1_0.sync.serializers import SyncCipherSerializer
from v1_0.general_view import PasswordManagerViewSet


class QuickSharePwdViewSet(PasswordManagerViewSet):
    permission_classes = (QuickSharePwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "create":
            self.serializer_class = CreateQuickShareSerializer
        elif self.action in ["list", "retrieve"]:
            self.serializer_class = ListQuickShareSerializer
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
            cipher = self.get_cipher(cipher_id=self.kwargs.get("pk"))
            return cipher.quick_share
        except (ObjectDoesNotExist, AttributeError):
            raise NotFound

    def get_queryset(self):
        user = self.request.user
        exclude_types = []
        if user.login_method == LOGIN_METHOD_PASSWORDLESS:
            exclude_types = [CIPHER_TYPE_MASTER_PASSWORD]
        ciphers = self.cipher_repository.get_multiple_by_user(
            user=user, exclude_types=exclude_types, only_edited=True
        ).values_list('id', flat=True)
        quick_share = QuickShare.objects.filter(cipher_id__in=list(ciphers))

        return quick_share

    def list(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save(**{"check_plan": True})
        cipher_id = validated_data.get("cipher_id")
        cipher = self.get_cipher(cipher_id=cipher_id)

        quick_share = QuickShare.update_or_create(cipher, **validated_data)
        return Response(status=200, data={"access_id": quick_share.access_id, "cipher_id": quick_share.cipher_id})

    def retrieve(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
