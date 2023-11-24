from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.core.exceptions.factor2_method_exception import Factor2CodeInvalidException, \
    Factor2MethodInvalidException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException, UserPasswordInvalidException
from locker_server.shared.error_responses.error import refer_error, gen_error
from locker_server.shared.utils.network import detect_device, get_ip_by_request
from .serializers import *
from locker_server.api.permissions.locker_permissions.factor2_pwd_permission import Factor2PwdPermission


class Factor2ViewSet(APIBaseViewSet):
    http_method_names = ["head", "options", "get", "post"]
    permission_classes = (Factor2PwdPermission,)

    def check_captcha_permission(self):
        # TODO: Check the captcha
        return True

    def get_client_agent(self):
        return self.request.META.get("HTTP_USER_AGENT") or ''

    def get_serializer_class(self):
        if self.action in ["auth_otp_mail"]:
            return Factor2MailOTPSerializer
        elif self.action in ["factor2"]:
            return Factor2Serializer
        elif self.action in ["factor2_is_activate"]:
            return Factor2ActivateSerializer

        return super().get_serializer_class()

    @action(methods=["post"], detail=False)
    def auth_otp_mail(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get('email')
        password = validated_data.get('password')
        try:
            self.factor2_service.auth_otp_mail(
                email=email,
                raw_password=password,
                device_info=detect_device(ua_string=self.get_client_agent()),
                ip_address=get_ip_by_request(request)
            )
        except UserDoesNotExistException:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=refer_error(gen_error("1001")))
        except UserPasswordInvalidException:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=refer_error(gen_error("1001")))

        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["get", "post"], detail=False)
    def factor2(self, request):
        """
        Get factor2 information or Turn on/off factor2
        :param request:
        :return:
        """
        user = self.request.user

        if request.method == "GET":
            try:
                user_factor2_info = self.factor2_service.get_factor2(user_id=user.user_id)
                return Response(status=status.HTTP_200_OK, data=user_factor2_info)
            except UserDoesNotExistException:
                raise NotFound
        if request.method == "POST":
            _serializer = self.get_serializer(data=request.data)
            _serializer.is_valid(raise_exception=True)
            _validated_data = _serializer.validated_data
            user_otp = _validated_data.get("otp")
            method = _validated_data.get("method")
            device = request.auth
            try:
                user = self.factor2_service.update_factor2(
                    user_id=user.user_id,
                    method=method,
                    user_otp=user_otp,
                    device=device
                )
            except UserDoesNotExistException:
                raise NotFound
            except Factor2CodeInvalidException:
                return Response(status=status.HTTP_400_BAD_REQUEST, data=refer_error(gen_error("1002")))
            except Factor2MethodInvalidException:
                raise ValidationError(detail={"method": [{"Method invalid"}]})

            return Response(status=status.HTTP_200_OK, data={"success": True, "is_factor2": user.is_factor2})

    @action(methods=["post"], detail=False)
    def factor2_activate_code(self, request):
        """
        This API Endpoint to generate random active code for factor2 mail method
        :param request:
        :return:
        """
        # self.check_captcha_permission()
        user = self.request.user
        method = request.data.get("method")
        try:
            mail_otp = self.factor2_service.create_mail_activate_code(
                user_id=user.user_id,
                method=method
            )
        except Factor2MethodInvalidException:
            raise ValidationError(detail={"method": ["Method is not valid", "Phương thức không hợp lệ"]})
        except UserDoesNotExistException:
            raise NotFound

        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def factor2_is_activate(self, request):
        """
        This API to turn off all factor2 method
        :param request: password: Require user password for this action
        :return:
        """
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        raw_password = validated_data.get("password")
        try:
            user = self.factor2_service.disable_factor2(
                user_id=user.user_id,
                raw_password=raw_password
            )
        except UserDoesNotExistException:
            raise NotFound
        except UserPasswordInvalidException:
            raise ValidationError(detail={"password": ["Password is not valid", "Mật khẩu không chính xác"]})

        return Response(status=status.HTTP_200_OK, data={"success": True, "is_factor2": user.is_factor2})
