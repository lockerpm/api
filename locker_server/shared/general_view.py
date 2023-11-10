from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from locker_server.shared.utils.network import get_ip_by_request


class AppGeneralViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin, mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        GenericViewSet):
    """
    This class is general view for all apps Django
    """

    def initial(self, request, *args, **kwargs):
        super(AppGeneralViewSet, self).initial(request, *args, **kwargs)

    @staticmethod
    def check_int_param(param, check_lt_zero=True):
        try:
            param = int(param)
            if check_lt_zero and param < 0:
                return None
            return param
        except (ValueError, TypeError):
            return None

    def get_ip(self):
        ip = get_ip_by_request(request=self.request)
        return ip

    def get_user_agent(self):
        return self.request.META.get("HTTP_USER_AGENT")
