from rest_framework import serializers

from cystack_models.models.teams.collections import Collection


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ('id', 'name', 'creation_date', 'revision_date', 'is_default')
        read_only_fields = ('id', 'creation_date', 'revision_date', 'is_default')

    def to_representation(self, instance):
        data = super(CollectionSerializer, self).to_representation(instance)
        return data


