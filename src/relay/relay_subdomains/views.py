from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied

from cystack_models.models.relay.relay_addresses import RelayAddress
from cystack_models.models.relay.deleted_relay_addresses import DeletedRelayAddress
from cystack_models.models.relay.relay_subdomains import RelaySubdomain
from relay.apps import RelayViewSet
from shared.constants.relay_address import MAX_FREE_RElAY_DOMAIN
from shared.error_responses.error import gen_error
from shared.permissions.relay_permissions.relay_address_permission import RelayAddressPermission
from shared.utils.app import now
from .serializers import SubdomainSerializer, UpdateSubdomainSerializer


class RelaySubdomainViewSet(RelayViewSet):
    permission_classes = (RelayAddressPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9]+'

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = SubdomainSerializer
        elif self.action in ["create", "update"]:
            self.serializer_class = UpdateSubdomainSerializer
        return super(RelaySubdomainViewSet, self).get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        relay_subdomains = user.relay_subdomains.all().order_by('created_time')
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
        if plan_obj.allow_relay_premium() is False:
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

        if user.relay_subdomains.exists() is True:
            raise ValidationError({"non_field_errors": [gen_error("8001")]})
        if RelaySubdomain.objects.filter(subdomain=subdomain).exists():
            raise ValidationError(detail={"subdomain": ["This subdomain is used. Try another subdomain"]})

        new_relay_subdomain = user.relay_subdomains.model.create(user=user, subdomain=subdomain)

        # TODO: Send job to AWS SQS

        return Response(status=200, data={"id": new_relay_subdomain.id, "subdomain": new_relay_subdomain.subdomain})

    def update(self, request, *args, **kwargs):
        user = self.request.user
        self.allow_relay_premium()
        subdomain_obj = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        subdomain = validated_data.get("subdomain")

        if RelaySubdomain.objects.exclude(user=user).filter(subdomain=subdomain).exists():
            raise ValidationError(detail={"subdomain": ["This subdomain is used. Try another subdomain"]})

        if subdomain != subdomain_obj.subdomain:
            # Delete all relay addresses of this subdomain
            relay_addresses = subdomain_obj.relay_addresses.all()
            for relay_address in relay_addresses:
                relay_address.delete_permanently()

            # TODO: Create deletion SQS job

            subdomain_obj.subdomain = subdomain
            subdomain_obj.save()

            # TODO: Send creation job to SQS

        return Response(status=200, data={"id": subdomain_obj.id})

    def destroy(self, request, *args, **kwargs):
        self.allow_relay_premium()
        subdomain_obj = self.get_object()

        # Delete all relay addresses of this subdomain
        relay_addresses = subdomain_obj.relay_addresses.all()
        for relay_address in relay_addresses:
            relay_address.delete_permanently()

        # TODO: Create deletion SQS job

        subdomain_obj.soft_delete()
        return Response(status=204)
