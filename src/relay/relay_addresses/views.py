from django.conf import settings
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied

from cystack_models.models.relay.relay_addresses import RelayAddress, MaxRelayAddressReachedException
from relay.apps import RelayViewSet
from relay.relay_addresses.serializers import RelayAddressSerializer, UpdateRelayAddressSerializer
from shared.constants.relay_address import MAX_FREE_RElAY_DOMAIN, DEFAULT_RELAY_DOMAIN
from shared.error_responses.error import gen_error
from shared.permissions.relay_permissions.relay_address_permission import RelayAddressPermission
from shared.utils.app import now


class RelayAddressViewSet(RelayViewSet):
    permission_classes = (RelayAddressPermission,)
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9]+'
    serializer_class = RelayAddressSerializer

    def get_serializer_class(self):
        if self.action == "update":
            self.serializer_class = UpdateRelayAddressSerializer
        return super(RelayAddressViewSet, self).get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        relay_addresses = user.relay_addresses.all().order_by('created_time')
        return relay_addresses

    def get_object(self):
        try:
            relay_address = RelayAddress.objects.get(id=self.kwargs.get("pk"), user=self.request.user)
            self.check_object_permissions(request=self.request, obj=relay_address)
            return relay_address
        except RelayAddress.DoesNotExist:
            raise NotFound

    def get_subdomain(self):
        user = self.request.user
        subdomain = user.relay_subdomains.filter(is_deleted=False, domain_id=DEFAULT_RELAY_DOMAIN).first()
        return subdomain

    def allow_relay_premium(self) -> bool:
        user = self.request.user
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        plan_obj = current_plan.get_plan_obj()
        return plan_obj.allow_relay_premium() or user.is_active_enterprise_member()

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        if paging_param == "0":
            self.pagination_class = None
        return super(RelayAddressViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data or {}
        allow_relay_premium = self.allow_relay_premium()
        # Check the limit of addresses
        validated_data.update({"allow_relay_premium": allow_relay_premium})
        # Check the user uses subdomain or not
        if user.use_relay_subdomain is True and allow_relay_premium is True:
            subdomain = self.get_subdomain()
            validated_data.update({"subdomain": subdomain})
        try:
            new_relay_address = RelayAddress.create_atomic(user_id=user.user_id, **validated_data)
        except MaxRelayAddressReachedException:
            raise ValidationError({"non_field_errors": [gen_error("8000")]})
        return Response(status=201, data=self.get_serializer(new_relay_address).data)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        relay_address = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        address = validated_data.get("address") or relay_address.address
        description = validated_data.get("description", relay_address.description)
        enabled = validated_data.get("enabled", relay_address.enabled)
        block_spam = validated_data.get("block_spam", relay_address.block_spam)

        if address != relay_address.address:
            # Only allow update the first address
            oldest_relay_address = user.relay_addresses.all().order_by('created_time').first()
            if not oldest_relay_address or oldest_relay_address.id != relay_address.id:
                raise PermissionDenied
            if RelayAddress.objects.filter(address=address).exists() is True:
                raise ValidationError(detail={"address": ["This relay address exists"]})
            if RelayAddress.valid_address(address=address, domain=relay_address.domain_id) is False:
                raise ValidationError(detail={"address": [
                    "This relay address is not valid (has black words, blocked words, etc...)"
                ]})
            relay_address.address = address
        if enabled != relay_address.enabled or block_spam != relay_address.block_spam:
            if self.allow_relay_premium():
                relay_address.enabled = enabled
                relay_address.block_spam = block_spam
        relay_address.description = description
        relay_address.updated_time = now()
        relay_address.save()
        return Response(status=200, data={"id": relay_address.id})

    def destroy(self, request, *args, **kwargs):
        relay_address = self.get_object()
        # Create deleted address
        relay_address.delete_permanently()
        return Response(status=204)

    @action(methods=["put"], detail=True)
    def block_spam(self, request, *args, **kwargs):
        relay_address = self.get_object()
        allow_relay_premium = self.allow_relay_premium()
        if allow_relay_premium is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})
        relay_address.block_spam = not relay_address.block_spam
        relay_address.save()
        return Response(status=200, data={"id": relay_address.id, "block_spam": relay_address.block_spam})

    @action(methods=["put"], detail=True)
    def enabled(self, request, *args, **kwargs):
        relay_address = self.get_object()
        relay_address.enabled = not relay_address.enabled
        relay_address.save()
        return Response(status=200, data={"id": relay_address.id, "enabled": relay_address.enabled})
