from django.conf import settings

API_USERS = "{}/micro_services/users".format(settings.GATEWAY_API)
HEADERS = {
    "User-agent": "CyStack Locker",
    "Authorization": settings.MICRO_SERVICE_USER_AUTH
}
