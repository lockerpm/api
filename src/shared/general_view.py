import jwt

from django.conf import settings
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from shared.constants.token import TOKEN_PREFIX


class AppGeneralViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin, mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        GenericViewSet):
    """
    This class is general view for all apps Django
    """

    # throttle_classes = ()

    def initial(self, request, *args, **kwargs):
        super(AppGeneralViewSet, self).initial(request, *args, **kwargs)

    @staticmethod
    def decode_token(token_value):
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
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidAlgorithmError):
            return None

    @staticmethod
    def check_int_param(param):
        try:
            param = int(param)
            if param < 0:
                return None
            return param
        except (ValueError, TypeError):
            return None

    def is_admin(self, request, *args, **kwargs):
        token_value = request.auth
        payload = self.decode_token(token_value)
        check_admin = payload.get("is_admin") if payload is not None else False
        if (check_admin == "1") or (check_admin == 1) or (check_admin is True):
            return True
        return False
