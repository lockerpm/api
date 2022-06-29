from rest_framework import serializers

from cystack_models.models.domains.domains import Domain


class ListDomainSerializer(serializers.Serializer):
    class Meta:
        model = Domain
        fields = ('id', 'created_time', 'updated_time', 'address', 'verification')
