from rest_framework import serializers

from locker_server.api.v1_0.sync.serializers import SyncFolderSerializer


class FolderSerializer(serializers.Serializer):
    name = serializers.CharField()


class DetailFolderSerializer(SyncFolderSerializer):
    def to_representation(self, instance):
        return super(DetailFolderSerializer, self).to_representation(instance)
