import random

from rest_framework.response import Response
from rest_framework.decorators import action

from shared.constants.account import LOGIN_METHOD_PASSWORDLESS
from shared.log.cylog import CyLog
from shared.permissions.locker_permissions.passwordless_pwd_permission import PasswordlessPwdPermission
from v1_0.apps import PasswordManagerViewSet
from .serializers import PasswordlessCredentialSerializer


class PasswordlessPwdViewSet(PasswordManagerViewSet):
    permission_classes = (PasswordlessPwdPermission, )
    http_method_names = ["head", "options", "get", "post", ]

    def get_serializer_class(self):
        if self.action == "credential":
            self.serializer_class = PasswordlessCredentialSerializer
        return super(PasswordlessPwdViewSet, self).get_serializer_class()

    @action(methods=["get", "post"], detail=False)
    def credential(self, request, *args, **kwargs):
        user = self.request.user
        CyLog.debug(**{"message": "Passwordless cred: {}".format(request.data)})
        if request.method == "GET":
            return Response(status=200, data={
                "credential_id": user.fd_credential_id,
                "random": user.fd_random
            })
        elif request.method == "POST":
            # Saving the cred id of the user
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            credential_id = validated_data.get("credential_id")
            credential_random = random.randbytes(32).hex()
            if not user.fd_credential_id:
                user.fd_credential_id = credential_id
                user.fd_random = credential_random
                user.login_method = LOGIN_METHOD_PASSWORDLESS
                user.save()
            return Response(status=200, data={"credential_id": user.fd_credential_id, "random": user.fd_random})
