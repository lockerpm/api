import json

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action

from cystack_models.models.relay.relay_addresses import RelayAddress
from relay.apps import RelayViewSet
from shared.log.cylog import CyLog
from shared.services.rabbitmq.rabbitmq import RelayQueue


class RelayHookViewSet(RelayViewSet):
    permission_classes = (AllowAny, )
    http_method_names = ["head", "options", "get", "post", "delete"]
    lookup_value_regex = r'[0-9]+'

    @staticmethod
    def get_relay_address_obj(email: str):
        address = email.split("@")[0]
        domain = email.split("@")[1]
        print(address, domain)
        relay_address = RelayAddress.objects.get(address=address, domain=domain)
        return relay_address

    @action(methods=["post"], detail=False)
    def sendgrid_hook(self, request, *args, **kwargs):
        token = self.request.query_params.get("token")
        if not token or token != settings.MAIL_WEBHOOK_TOKEN:
            CyLog.error(**{"message": "[sendgrid_hook] Permission denied"})
            raise PermissionDenied

        mail_data = request.data
        try:
            mail_data = json.loads(json.dumps(mail_data))
        except Exception:
            CyLog.error(**{"message": "[sendgrid_hook] Json loads error"})
            return Response(status=400, data={"message": ["Invalid JSON data"]})

        receiver = mail_data.get("to")
        CyLog.error(**{"message": "[sendgrid_hook] RelayAddress {}".format(receiver)})
        try:
            relay_address = self.get_relay_address_obj(email=receiver)
        except RelayAddress.DoesNotExist:
            CyLog.error(**{"message": "[sendgrid_hook] RelayAddress {} does not exist".format(receiver)})
            return Response(status=200, data={
                "success": False,
                "error": "The email {} does not exist".format(receiver)
            })

        user = relay_address.user
        email = user.get_from_cystack_id().get("email")
        if not email:
            CyLog.error(**{"message": "[sendgrid_hook] RelayAddress not found email"})
            return Response(status=200, data={
                "success": False,
                "error": "The email of user {} does not exist".format(user.user_id)
            })

        # Send to queue
        mail_data["destination"] = email
        CyLog.error(**{"message": "[sendgrid_hook] Starting send data: {}".format(mail_data)})
        RelayQueue().send(data=mail_data)

        return Response(status=200, data={"success": True})
