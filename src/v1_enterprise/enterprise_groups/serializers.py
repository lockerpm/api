from rest_framework import serializers

from cystack_models.models.enterprises.groups.groups import EnterpriseGroup


class EnterpriseGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseGroup
        fields = ('id', 'creation_date', 'revision_date', 'name')
        read_only_fields = ('id', 'creation_date', 'revision_date')

    def to_representation(self, instance):
        data = super(EnterpriseGroupSerializer, self).to_representation(instance)
        return data
