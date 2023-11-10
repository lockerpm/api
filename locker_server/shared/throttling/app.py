from django.contrib.auth.models import AnonymousUser
from rest_framework import throttling
from rest_framework.settings import api_settings


class AppBaseThrottle(throttling.ScopedRateThrottle):
    """
    General throttle class
    """

    def get_ident(self, request):
        """
        This function to get ident for request, not using IP as default
        We will use username as ident
        :param request:
        :return:
        """

        try:
            username = request.data.get("username")
        except AttributeError:
            username = None
        request_path = request.path
        # Get ident by username
        if username:
            return username

        # Else, ident by IP
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        remote_addr = request.META.get('REMOTE_ADDR')
        num_proxies = api_settings.NUM_PROXIES

        if num_proxies is not None:
            if num_proxies == 0 or xff is None:
                return remote_addr
            addrs = xff.split(',')
            client_addr = addrs[-min(num_proxies, len(addrs))]
            return client_addr.strip()

        ident = ''.join(xff.split()) if xff else remote_addr
        return ident

    def get_cache_key(self, request, view):
        """
        If `view.throttle_scope` is not set, don't apply this throttle.

        Otherwise generate the unique cache key by concatenating the user id
        with the '.throttle_scope` property of the view.
        """
        if request.user and not isinstance(request.user, AnonymousUser):
            try:
                ident = request.auth.user.user_id
            except AttributeError:
                # The auth user is AccessKey
                try:
                    ident = request.auth.user.client_id
                except AttributeError:
                    ident = self.get_ident(request)
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
