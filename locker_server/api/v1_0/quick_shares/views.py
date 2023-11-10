import json

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.quick_share_pwd_permission import QuickSharePwdPermission
from locker_server.core.exceptions.cipher_exception import *
from locker_server.core.exceptions.quick_share_exception import QuickShareDoesNotExistException, \
    QuickShareNotValidAccessException, QuickShareRequireOTPException
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.utils.app import camel_snake_data
from .serializers import CreateQuickShareSerializer, ListQuickShareSerializer, DetailQuickShareSerializer, \
    PublicQuickShareSerializer, CheckAccessQuickShareSerializer, PublicAccessQuickShareSerializer


class QuickSharePwdViewSet(APIBaseViewSet):
    permission_classes = (QuickSharePwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9a-z-]+'

    def get_throttles(self):
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            self.serializer_class = CreateQuickShareSerializer
        elif self.action == "list":
            self.serializer_class = ListQuickShareSerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailQuickShareSerializer
        elif self.action == "public":
            self.serializer_class = PublicQuickShareSerializer
        elif self.action in ["access", "otp"]:
            self.serializer_class = CheckAccessQuickShareSerializer
        return super().get_serializer_class()

    def get_cipher(self, cipher_id):
        try:
            cipher = self.cipher_service.get_by_id(cipher_id=cipher_id)
            if cipher.team:
                self.check_object_permissions(request=self.request, obj=cipher)
            else:
                if cipher.user.user_id != self.request.user.user_id:
                    raise NotFound
            return cipher
        except CipherDoesNotExistException:
            raise NotFound

    def get_object(self):
        try:
            quick_share = self.quick_share_service.get_by_id(quick_share_id=self.kwargs.get("pk"))
            self.get_cipher(cipher_id=quick_share.cipher.cipher_id)
            return quick_share
        except QuickShareDoesNotExistException:
            raise NotFound

    def get_quick_share_by_access_id(self):
        try:
            return self.quick_share_service.get_by_access_id(access_id=self.kwargs.get("pk"))
        except QuickShareDoesNotExistException:
            raise NotFound

    def get_queryset(self):
        user = self.request.user
        quick_shares = self.quick_share_service.list_user_quick_shares(user_id=user.user_id)
        return quick_shares

    def list(self, request, *args, **kwargs):
        # self.check_pwd_session_auth(request)
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10
        response = super().list(request, *args, **kwargs)
        response.data = camel_snake_data(response.data, snake_to_camel=True)
        return response

    def create(self, request, *args, **kwargs):
        ip = self.get_ip()
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        validated_data = json.loads(json.dumps(validated_data))
        cipher_id = validated_data.get("cipher_id")
        self.get_cipher(cipher_id=cipher_id)
        quick_share = self.quick_share_service.create_user_quick_share(
            user_id=user.user_id, ip=ip, **validated_data
        )
        return Response(status=status.HTTP_200_OK, data={
            "id": quick_share.quick_share_id,
            "cipher_id": quick_share.cipher.cipher_id,
            "access_id": quick_share.access_id
        })

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        response.data = camel_snake_data(response.data, snake_to_camel=True)
        return response

    def update(self, request, *args, **kwargs):
        quick_share = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        validated_data = json.loads(json.dumps(validated_data))

        try:
            quick_share = self.quick_share_service.update_user_quick_share(
                quick_share=quick_share, **validated_data
            )
        except QuickShareDoesNotExistException:
            raise NotFound
        return Response(status=status.HTTP_200_OK, data={
            "id": quick_share.quick_share_id,
            "cipher_id": quick_share.cipher.cipher_id,
            "access_id": quick_share.access_id
        })

    def destroy(self, request, *args, **kwargs):
        quick_share = self.get_object()
        self.quick_share_service.delete_user_quick_share(user_id=request.user.user_id, quick_share=quick_share)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["post"], detail=False)
    def public(self, request, *args, **kwargs):
        quick_share = self.get_quick_share_by_access_id()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        code = validated_data.get("code")
        token = validated_data.get("token")

        try:
            quick_share, token, expired_time = self.quick_share_service.public_quick_share(
                quick_share=quick_share, email=email, code=code, token=token
            )
        except QuickShareNotValidAccessException:
            raise ValidationError({"non_field_errors": [gen_error("9000")]})
        result = PublicAccessQuickShareSerializer(quick_share, many=False).data
        result.pop("emails", None)
        if token:
            result["token"] = {"value": token, "expired_time": expired_time}
        return Response(status=status.HTTP_200_OK, data=camel_snake_data(result, snake_to_camel=True))

    @action(methods=["get", "post"], detail=False)
    def access(self, request, *args, **kwargs):
        quick_share = self.get_quick_share_by_access_id()

        if request.method == "POST":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            email = validated_data.get("email")

            is_valid_access = self.quick_share_service.check_access(quick_share=quick_share, email=email)
            if is_valid_access:
                return Response(status=status.HTTP_200_OK, data={"success": True})
            raise ValidationError(detail={"email": ["The email is not valid"]})

        elif request.method == "GET":
            try:
                quick_share = self.quick_share_service.get_email_access(quick_share=quick_share)
            except QuickShareNotValidAccessException:
                raise ValidationError({"non_field_errors": [gen_error("9000")]})
            except QuickShareRequireOTPException:
                return Response(status=status.HTTP_200_OK, data={"require_otp": quick_share.require_otp})
            result = PublicAccessQuickShareSerializer(quick_share, many=False).data
            return Response(status=status.HTTP_200_OK, data=camel_snake_data(result, snake_to_camel=True))

    @action(methods=["post"], detail=False)
    def otp(self, request, *args, **kwargs):
        quick_share = self.get_quick_share_by_access_id()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        try:
            code = self.quick_share_service.set_email_otp(quick_share=quick_share, email=email)
        except QuickShareDoesNotExistException:
            raise ValidationError(detail={"email": ["The email is not valid"]})
        return Response(status=status.HTTP_200_OK, data={"code": code, "email": email})
