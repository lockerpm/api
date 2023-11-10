import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission

from locker_server.shared.constants.token import TOKEN_PREFIX

CACHE_ROLE_PERMISSION_PREFIX = "cs_role_permission_"
CACHE_ROLE_ENTERPRISE_PERMISSION_PREFIX = "e_role_permission_"


class AppBasePermission(BasePermission):
    scope = 'general'

    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        return super(AppBasePermission, self).has_object_permission(request, view, obj)

    @staticmethod
    def is_auth(request):
        if request.user and (request.auth is not None):
            return False if isinstance(request.user, AnonymousUser) else True
        return False

    @staticmethod
    def is_super_admin(request):
        try:
            return request.user and request.user.is_supper_admin
        except AttributeError:
            return False

    @staticmethod
    def _decode_token(token_value):
        # Remove `cs.` and decode
        if not isinstance(token_value, str):
            try:
                non_prefix_token = getattr(token_value, "access_token")
            except AttributeError:
                return None
        else:
            non_prefix_token = token_value[len(TOKEN_PREFIX):]
        try:
            payload = jwt.decode(non_prefix_token, settings.SECRET_KEY, algorithms=['HS256'])
            return payload
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.exceptions.InvalidAlgorithmError):
            return None

    def is_admin(self, request):
        if self.is_auth(request):
            token = request.auth
            payload = self._decode_token(token)
            check_admin = payload.get("is_admin") if payload is not None else False
            if (check_admin == "1") or (check_admin == 1) or (check_admin is True):
                return True
        return False
