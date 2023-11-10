from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from locker_server.shared.general_view import AppGeneralViewSet
from locker_server.containers.containers import *
from locker_server.shared.utils.network import get_ip_by_request


class APIBaseViewSet(AppGeneralViewSet):
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (APIPermission,)
    # throttle_classes = (AppBaseThrottle,)
    throttle_scope = 'anonymous'

    resource_service = resource_service
    auth_service = auth_service
    user_service = user_service
    device_service = device_service
    family_service = family_service
    emergency_access_service = emergency_access_service
    exclude_domain_service = exclude_domain_service
    backup_credential_service = backup_credential_service

    payment_service = payment_service
    mobile_payment_service = mobile_payment_service
    payment_hook_service = payment_hook_service

    cipher_service = cipher_service
    folder_service = folder_service

    team_member_service = team_member_service
    collection_service = collection_service
    sharing_service = sharing_service

    quick_share_service = quick_share_service

    enterprise_service = enterprise_service
    enterprise_member_service = enterprise_member_service
    enterprise_group_service = enterprise_group_service
    enterprise_domain_service = enterprise_domain_service
    enterprise_billing_contact_service = enterprise_billing_contact_service

    relay_address_service = relay_address_service
    relay_subdomain_service = relay_subdomain_service
    reply_service = reply_service

    affiliate_submission_service = affiliate_submission_service
    release_service = release_service
    notification_setting_service = notification_setting_service
    user_reward_mission_service = user_reward_mission_service

    event_service = event_service
    factor2_service = factor2_service
    notification_service = notification_service

    mail_configuration_service = mail_configuration_service

    sso_configuration_service = sso_configuration_service

    def get_throttles(self):
        if self.request.user and not isinstance(self.request.user, AnonymousUser):
            self.throttle_scope = 'user_authenticated'
        else:
            self.throttle_scope = 'anonymous'
        return super(APIBaseViewSet, self).get_throttles()

    def check_pwd_session_auth(self, request):
        # TODO: Check pwd session token
        return True

    def get_client_agent(self):
        if settings.SELF_HOSTED:
            return self.request.META.get("HTTP_USER_AGENT") or ''
        return self.request.META.get("HTTP_LOCKER_CLIENT_AGENT") or self.request.META.get("HTTP_USER_AGENT") or ''

    def get_ip(self):
        if settings.SELF_HOSTED:
            return get_ip_by_request(request=self.request)
        return self.request.data.get("ip") or get_ip_by_request(request=self.request)
