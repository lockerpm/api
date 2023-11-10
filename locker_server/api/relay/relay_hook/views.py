import json

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from rest_framework.decorators import action

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.relay_permissions.relay_hook_permission import RelayHookPermission
from locker_server.core.exceptions.relay_exceptions.reply_exception import *
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.shared.constants.relay_address import *
from locker_server.shared.external_services.rabbitmq.rabbitmq import RelayQueue
from locker_server.shared.log.cylog import CyLog
from .serializers import ReplySerializer, StatisticSerializer


class RelayHookViewSet(APIBaseViewSet):
    permission_classes = (RelayHookPermission,)
    http_method_names = ["head", "options", "get", "post"]
    lookup_value_regex = r'[0-9]+'

    def get_serializer_class(self):
        if self.action == "reply":
            self.serializer_class = ReplySerializer
        elif self.action == "statistics":
            self.serializer_class = StatisticSerializer
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

    def allow_relay_premium(self, user) -> bool:
        user = self.request.user
        current_plan = self.user_service.get_current_plan(user=user)
        plan = current_plan.pm_plan
        is_active_enterprise_member = self.user_service.is_active_enterprise_member(user_id=user.user_id)
        return plan.relay_premium or is_active_enterprise_member

    def get_relay_address(self, email: str):
        address = email.split("@")[0]
        full_domain = email.split("@")[1]

        if full_domain.count(".") == 1:
            domain_id = full_domain
            subdomain = None
        else:
            subdomain = full_domain.split(".")[0]
            domain_id = full_domain.replace(f"{subdomain}.", "")
        relay_address = self.relay_address_service.get_relay_address_by_full_domain(
            address=address,
            domain_id=domain_id,
            subdomain=subdomain
        )
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
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": ["Invalid JSON data"]})

        receiver = self.get_receiver(mail_data=mail_data)
        relay_address = self.get_relay_address(email=receiver)
        if not relay_address:
            return Response(status=status.HTTP_200_OK, data={
                "success": False,
                "error": "The email {} does not exist".format(receiver)
            })

        user = relay_address.user
        email = self.user_service.get_from_cystack_id().get("email")
        if not email:
            return Response(status=status.HTTP_200_OK, data={
                "success": False,
                "error": "The email of user {} does not exist".format(user.user_id)
            })

        # Send to queue
        mail_data["destination"] = email
        RelayQueue().send(data=mail_data)

        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["get"], detail=False)
    def destination(self, request, *args, **kwargs):
        self.check_auth_token()
        relay_address = self.request.query_params.get("relay_address")
        relay_address = self.get_relay_address(email=relay_address)
        if not relay_address:
            # CyLog.debug(**{"message": "Can not get relay address destination: {}".format(relay_address)})
            raise NotFound
        return Response(status=status.HTTP_200_OK, data={"user_id": relay_address.user.user_id})

    @action(methods=["post"], detail=False)
    def reply(self, request, *args, **kwargs):
        self.check_auth_token()
        if request.method == "GET":
            lookup_param = self.request.query_params.get("lookup")
            if not lookup_param:
                raise NotFound
            try:
                reply = self.reply_service.get_reply_by_lookup(lookup=lookup_param)
            except ReplyDoesNotExistException:
                raise NotFound
            return Response(status=status.HTTP_200_OK, data={
                "id": reply.reply_id,
                "lookup": reply.lookup,
                "encrypted_metadata": reply.encrypted_metadata
            })

        elif request.method == "POST":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            lookup = validated_data.get("lookup")
            encrypted_metadata = validated_data.get("encrypted_metadata")
            try:
                new_reply = self.reply_service.create_reply(lookup=lookup, encrypted_metadata=encrypted_metadata)
            except ReplyLookupExistedException:
                raise ValidationError(detail={"lookup": ["This lookup existed"]})
            return Response(status=status.HTTP_200_OK, data={"id": new_reply.reply_id})

    @action(methods=["get"], detail=False)
    def plan(self, request, *args, **kwargs):
        self.check_auth_token()
        relay_address_param = self.request.query_params.get("relay_address")
        user_id_param = self.request.query_params.get("user_id")

        if user_id_param:
            try:
                user = self.user_service.retrieve_by_id(user_id=user_id_param)
            except UserDoesNotExistException:
                CyLog.debug(**{"message": "Can not get plan of user: {}".format(user_id_param)})
                raise NotFound
            is_premium = self.allow_relay_premium(user=user)
            return Response(status=status.HTTP_200_OK, data={
                "is_premium": is_premium,
            })

        relay_address = self.get_relay_address(email=relay_address_param)
        if not relay_address:
            CyLog.debug(**{"message": "Can not get plan of address destination: {}".format(relay_address_param)})
            raise NotFound
        is_premium = self.allow_relay_premium(user=relay_address.user)
        return Response(status=status.HTTP_200_OK, data={
            "is_premium": is_premium,
            "block_spam": relay_address.block_spam if is_premium is True else False,
            "enabled": relay_address.enabled
        })

    @action(methods=["post"], detail=False)
    def statistics(self, request, *args, **kwargs):
        self.check_auth_token()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        relay_address = validated_data.get("relay_address")
        statistic_type = validated_data.get("type")
        amount = validated_data.get("amount", 1)

        relay_address = self.get_relay_address(email=relay_address)
        if not relay_address:
            CyLog.debug(**{"message": "Can not statistics relay address destination: {}".format(relay_address)})
            raise ValidationError(detail={"relay_address": ["The relay address does not exist"]})
        self.relay_address_service.update_relay_address_statistic(
            relay_address_id=relay_address.relay_address_id,
            statistic_type=statistic_type,
            amount=amount
        )
        return Response(status=status.HTTP_200_OK, data={"success": True})
