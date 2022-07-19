import jwt

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from shared.constants.token import TOKEN_PREFIX


CACHE_ROLE_PERMISSION_PREFIX = "cs_role_permission_"
CACHE_ROLE_ENTERPRISE_PERMISSION_PREFIX = "e_role_permission_"


class AppBasePermission(BasePermission):
    scope = 'general'

    def has_permission(self, request, view):
        if self.is_admin(request):
            return True
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        role_permissions = role.get_permissions()
        role_pattern = self.get_role_pattern(view)

        return role_pattern in role_permissions

    @staticmethod
    def is_auth(request):
        if request.user and (request.auth is not None):
            if isinstance(request.user, AnonymousUser):
                return False
            return True
        return False

    @staticmethod
    def get_team_member(user, obj):
        """
        Get member of the team
        :param user:
        :param obj: (obj) Team object
        :return:
        """
        member = obj.get_member_obj(user=user)
        if member is None:
            raise PermissionDenied
        return member

    @staticmethod
    def _decode_token(token_value):
        # Remove `cs.` and decode
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

    def get_role_pattern(self, view):
        role_pattern = "{}.{}".format(self.scope, view.action)
        return role_pattern

    def get_role(self, user, obj):
        """
        This method to get role name of the user
        :param user:
        :param obj
        :return:
        """
        member = self.get_team_member(user, obj)
        return member.role
