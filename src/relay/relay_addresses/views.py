from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied

from cystack_models.models.relay.relay_addresses import RelayAddress
from cystack_models.models.relay.deleted_relay_addresses import DeletedRelayAddress
from relay.apps import RelayViewSet
from relay.relay_addresses.serializers import RelayAddressSerializer, UpdateRelayAddressSerializer
from shared.constants.relay_address import MAX_FREE_RElAY_DOMAIN
from shared.error_responses.error import gen_error
from shared.permissions.relay_permissions.relay_address_permission import RelayAddressPermission
from shared.utils.app import now


class RelayAddressViewSet(RelayViewSet):
    permission_classes = (RelayAddressPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9]+'
    serializer_class = RelayAddressSerializer

    def get_serializer_class(self):
        if self.action == "update":
            self.serializer_class = UpdateRelayAddressSerializer
        return super(RelayAddressViewSet, self).get_serializer_class()

    @staticmethod
    def get_relay_address_obj(email: str):
        address = email.split("@")[0]
        domain = email.split("@")[1]
        relay_address = RelayAddress.objects.get(address=address, domain=domain)
        return relay_address

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
        # Check the limit of addresses
        if user.relay_addresses.all().count() >= MAX_FREE_RElAY_DOMAIN:
            raise ValidationError({"non_field_errors": [gen_error("8000")]})
        new_relay_address = RelayAddress.create(user=user, **validated_data)
        return Response(status=201, data=self.get_serializer(new_relay_address).data)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        relay_address = self.get_object()
        # Only allow update the first address
        oldest_relay_address = user.relay_addresses.all().order_by('created_time').first()
        if not oldest_relay_address or oldest_relay_address.id != relay_address.id:
            raise PermissionDenied
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        address = validated_data.get("address") or relay_address.address
        description = validated_data.get("description", relay_address.description)

        if address != relay_address.address:
            if RelayAddress.objects.filter(address=address).exists() is True:
                raise ValidationError(detail={"address": ["This relay address exists"]})
            if RelayAddress.valid_address(address=address, domain=relay_address.domain_id) is False:
                raise ValidationError(detail={"address": [
                    "This relay address is not valid (has black words, blocked words, etc...)"
                ]})
            relay_address.address = address
        relay_address.description = description
        relay_address.updated_time = now()
        relay_address.save()
        return Response(status=200, data={"id": relay_address.id})

    def destroy(self, request, *args, **kwargs):
        relay_address = self.get_object()
        # Create deleted address
        deleted_address = DeletedRelayAddress.objects.create(
            address_hash=RelayAddress.hash_address(relay_address.address, relay_address.domain_id),
            num_forwarded=relay_address.num_forwarded,
            num_blocked=relay_address.num_blocked,
            num_replied=relay_address.num_replied,
            num_spam=relay_address.num_spam,
        )
        deleted_address.save()
        # Remove relay address
        relay_address.delete()
        return Response(status=204)
