from rest_framework import serializers

from cystack_models.models.relay.relay_addresses import RelayAddress


class RelayAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelayAddress
        fields = ('id', 'address', 'enabled', 'description', 'created_time', 'updated_time',
                  'num_forwarded', 'num_blocked', 'num_replied', 'num_spam')
        read_only_fields = (
            'id', 'address', 'enabled', 'created_time', 'updated_time',
            'num_forwarded', 'num_blocked', 'num_replied', 'num_spam'
        )

    def to_representation(self, instance):
        data = super(RelayAddressSerializer, self).to_representation(instance)
        data["domain"] = instance.domain_id
        data["full_address"] = instance.full_address
        return data


class UpdateRelayAddressSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=64, min_length=6)
    description = serializers.CharField(allow_blank=True, required=False)
