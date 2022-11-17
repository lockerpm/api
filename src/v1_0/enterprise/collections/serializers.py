from rest_framework import serializers

from cystack_models.models.teams.collections import Collection
from v1_0.sync.serializers import SyncCollectionSerializer


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ('id', 'name', 'creation_date', 'revision_date', 'is_default')
        read_only_fields = ('id', 'creation_date', 'revision_date', 'is_default')

    def to_representation(self, instance):
        data = super(CollectionSerializer, self).to_representation(instance)
        # action = self.context["view"].action
        # if action == "retrieve":
        #     data["group_ids"] = list(instance.collections_groups.values_list('group_id', flat=True))

        return data
    

class DetailCollectionSerializer(SyncCollectionSerializer):
    def to_representation(self, instance):
        return super(DetailCollectionSerializer, self).to_representation(instance)


class UpdateCollectionSerializer(serializers.Serializer):
    name = serializers.CharField()
    groups = serializers.ListField(
        child=serializers.CharField(max_length=128), allow_empty=True, required=False, allow_null=True
    )


class UpdateUserCollectionSerializer(serializers.Serializer):
    members = serializers.ListField(
        child=serializers.CharField(max_length=128), allow_empty=True
    )