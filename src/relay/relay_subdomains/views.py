import json
import os

from django.conf import settings
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, NotFound

from cystack_models.models.relay.relay_subdomains import RelaySubdomain, MaxRelaySubdomainReachedException
from relay.apps import RelayViewSet
from shared.error_responses.error import gen_error
from shared.permissions.relay_permissions.relay_address_permission import RelayAddressPermission
from shared.services.sqs.sqs import sqs_service
from .serializers import SubdomainSerializer, UpdateSubdomainSerializer, UseRelaySubdomainSerializer


class RelaySubdomainViewSet(RelayViewSet):
    permission_classes = (RelayAddressPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9]+'

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = SubdomainSerializer
        elif self.action in ["create", "update"]:
            self.serializer_class = UpdateSubdomainSerializer
        elif self.action == "use_subdomain":
            self.serializer_class = UseRelaySubdomainSerializer
        return super(RelaySubdomainViewSet, self).get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        relay_subdomains = user.relay_subdomains.filter(is_deleted=False).order_by('created_time')
        return relay_subdomains

    def get_object(self):
        user = self.request.user
        try:
            relay_subdomain = user.relay_subdomains.get(user=user, id=self.kwargs.get("pk"), is_deleted=False)
            return relay_subdomain
        except RelaySubdomain.DoesNotExist:
            raise NotFound

    def allow_relay_premium(self):
        user = self.request.user
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        plan_obj = current_plan.get_plan_obj()
        if plan_obj.allow_relay_premium() is False and user.is_active_enterprise_member() is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})
        return current_plan

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "0")
        if paging_param == "0":
            self.pagination_class = None
        return super(RelaySubdomainViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        user = request.user
        self.allow_relay_premium()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        subdomain = validated_data.get("subdomain")

        if user.relay_subdomains.filter(is_deleted=False).exists() is True:
            raise ValidationError({"non_field_errors": [gen_error("8001")]})
        if RelaySubdomain.objects.filter(subdomain=subdomain).exists():
            raise ValidationError(detail={"subdomain": ["This subdomain is used. Try another subdomain"]})

        try:
            new_relay_subdomain = user.relay_subdomains.model.create_atomic(user_id=user.user_id, subdomain=subdomain)
        except MaxRelaySubdomainReachedException:
            raise ValidationError({"non_field_errors": [gen_error("8001")]})
        # Send job to AWS SQS to create new subdomain
        if os.getenv("PROD_ENV") == "prod":
            action_msg = {'action': 'create', 'domain': f"{new_relay_subdomain.subdomain}.{new_relay_subdomain.domain_id}"}
            create_msg = {'Type': 'DomainIdentity', 'Message': json.dumps(action_msg)}
            sqs_service.send_message(message_body=json.dumps(create_msg))

        return Response(status=200, data={"id": new_relay_subdomain.id, "subdomain": new_relay_subdomain.subdomain})

    def retrieve(self, request, *args, **kwargs):
        subdomain_obj = self.get_object()
        relay_addresses = subdomain_obj.relay_addresses.all()
        num_spam = relay_addresses.aggregate(Sum('num_spam')).get("num_spam__sum") or 0
        num_forwarded = relay_addresses.aggregate(Sum('num_forwarded')).get("num_forwarded__sum") or 0
        data = {
            "id": subdomain_obj.id,
            "subdomain": subdomain_obj.subdomain,
            "created_time": subdomain_obj.created_time,
            "num_alias": relay_addresses.count(),
            "num_spam": num_spam,
            "num_forwarded": num_forwarded,
        }
        return Response(status=200, data=data)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        self.allow_relay_premium()
        subdomain_obj = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        subdomain = validated_data.get("subdomain")

        if RelaySubdomain.objects.exclude(user=user, is_deleted=False).filter(subdomain=subdomain).exists():
            raise ValidationError(detail={"subdomain": ["This subdomain is used. Try another subdomain"]})

        old_subdomain = subdomain_obj.subdomain
        if subdomain != old_subdomain:
            # Delete all relay addresses of this subdomain
            relay_addresses = subdomain_obj.relay_addresses.all()
            for relay_address in relay_addresses:
                relay_address.delete_permanently()

            # Create deletion SQS job
            if os.getenv("PROD_ENV") == "prod":
                action_delete_msg = {'action': 'delete', 'domain': f"{old_subdomain}.{subdomain_obj.domain_id}"}
                delete_msg = {'Type': 'DomainIdentity', 'Message': json.dumps(action_delete_msg)}
                sqs_service.send_message(message_body=json.dumps(delete_msg))
            # Update object in the database
            subdomain_obj.subdomain = subdomain
            subdomain_obj.save()
            # Save subdomain object as deleted
            user.relay_subdomains.model.create(user=user, subdomain=old_subdomain, is_deleted=True)
            # Send creation job to SQS
            if os.getenv("PROD_ENV") == "prod":
                action_create_msg = {'action': 'create', 'domain': f"{subdomain}.{subdomain_obj.domain_id}"}
                create_msg = {'Type': 'DomainIdentity', 'Message': json.dumps(action_create_msg)}
                sqs_service.send_message(message_body=json.dumps(create_msg))

        return Response(status=200, data={"id": subdomain_obj.id})

    def destroy(self, request, *args, **kwargs):
        self.allow_relay_premium()
        subdomain_obj = self.get_object()

        # Delete all relay addresses of this subdomain
        relay_addresses = subdomain_obj.relay_addresses.all()
        for relay_address in relay_addresses:
            relay_address.delete_permanently()

        # Create deletion SQS job
        if os.getenv("PROD_ENV") == "prod":
            action_delete_msg = {'action': 'delete', 'domain': f"{subdomain_obj.subdomain}.{subdomain_obj.domain_id}"}
            delete_msg = {'Type': 'DomainIdentity', 'Message': json.dumps(action_delete_msg)}
            sqs_service.send_message(message_body=json.dumps(delete_msg))

        subdomain_obj.soft_delete()
        return Response(status=204)

    @action(methods=["get", "put"], detail=False)
    def use_subdomain(self, request, *args, **kwargs):
        user = self.request.user

        if request.method == "GET":
            return Response(status=200, data={"use_relay_subdomain": user.use_relay_subdomain})

        elif request.method == "PUT":
            self.allow_relay_premium()
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            use_relay_subdomain = validated_data.get("use_relay_subdomain")
            user.use_relay_subdomain = use_relay_subdomain
            user.save()
            return Response(status=200, data={"use_relay_subdomain": user.use_relay_subdomain})
