import json

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.decorators import action

from cystack_models.models.relay.relay_addresses import RelayAddress
from cystack_models.models.relay.reply import Reply
from relay.apps import RelayViewSet
from relay.relay_hook.serializer import ReplySerializer
from shared.log.cylog import CyLog
from shared.services.rabbitmq.rabbitmq import RelayQueue


class RelayHookViewSet(RelayViewSet):
    permission_classes = (AllowAny, )
    http_method_names = ["head", "options", "get", "post"]
    lookup_value_regex = r'[0-9]+'
    
    def get_serializer_class(self):
        if self.action == "reply":
            self.serializer_class = ReplySerializer
        return super(RelayHookViewSet, self).get_serializer_class()

    def check_auth_token(self):
        auth_header = self.request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            token = self.request.query_params.get("token")
            if token == settings.MAIL_WEBHOOK_TOKEN:
                return True
            raise PermissionDenied
        try:
            token = auth_header.split()[1]
            if token != settings.MAIL_WEBHOOK_TOKEN:
                raise PermissionDenied
            return True
        except IndexError:
            raise PermissionDenied

    @staticmethod
    def get_relay_address_obj(email: str):
        address = email.split("@")[0]
        domain = email.split("@")[1]
        relay_address = RelayAddress.objects.get(address=address, domain=domain)
        return relay_address

    @staticmethod
    def get_receiver(mail_data):
        envelope = mail_data.get("envelope")
        if isinstance(envelope, list) and envelope:
            envelope = envelope[0]
        envelope = json.loads(envelope)
        receiver = envelope.get("to")
        if isinstance(receiver, list) and receiver:
            return receiver[0]
        return receiver

    @action(methods=["post"], detail=False)
    def sendgrid_hook(self, request, *args, **kwargs):
        token = self.request.query_params.get("token")
        if not token or token != settings.MAIL_WEBHOOK_TOKEN:
            raise PermissionDenied

        mail_data = request.data
        try:
            mail_data = json.loads(json.dumps(mail_data))
        except Exception:
            CyLog.error(**{"message": "[sendgrid_hook] Json loads error"})
            return Response(status=400, data={"message": ["Invalid JSON data"]})

        receiver = self.get_receiver(mail_data=mail_data)
        try:
            relay_address = self.get_relay_address_obj(email=receiver)
        except RelayAddress.DoesNotExist:
            return Response(status=200, data={
                "success": False,
                "error": "The email {} does not exist".format(receiver)
            })

        user = relay_address.user
        email = user.get_from_cystack_id().get("email")
        if not email:
            return Response(status=200, data={
                "success": False,
                "error": "The email of user {} does not exist".format(user.user_id)
            })

        # Send to queue
        mail_data["destination"] = email
        RelayQueue().send(data=mail_data)

        return Response(status=200, data={"success": True})

    @action(methods=["get"], detail=False)
    def destination(self, request, *args, **kwargs):
        self.check_auth_token()
        relay_address = self.request.query_params.get("relay_address")
        try:
            relay_address = self.get_relay_address_obj(email=relay_address)
        except RelayAddress.DoesNotExist:
            raise NotFound
        return Response(status=200, data={"user_id": relay_address.user_id})

    @action(methods=["post"], detail=False)
    def reply(self, request, *args, **kwargs):
        self.check_auth_token()
        if request.method == "GET":
            lookup_param = self.request.query_params.get("lookup")
            if not lookup_param:
                raise NotFound
            try:
                reply = Reply.objects.get(lookup=lookup_param)
            except Reply.DoesNotExist:
                raise NotFound
            return Response(status=200, data={
                "id": reply.id,
                "lookup": reply.lookup,
                "encrypted_metadata": reply.encrypted_metadata
            })

        elif request.method == "POST":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            lookup = validated_data.get("lookup")
            encrypted_metadata = validated_data.get("encrypted_metadata")
            new_reply = Reply.create(lookup=lookup, encrypted_metadata=encrypted_metadata)
            return Response(status=200, data={"id": new_reply.id})

