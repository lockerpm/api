from rest_framework import serializers

from shared.constants.members import *
from cystack_models.models.members.team_members import TeamMember


class DetailMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ('id', 'access_time', 'is_default', 'is_primary', 'user_id', 'role', 'email', 'status')
        read_only_fields = ('id', 'access_time', 'is_primary', 'status')

    def validate(self, data):
        role = data.get("role")
        if role not in TEAM_LIST_ROLE:
            raise serializers.ValidationError(detail={"role": ["Role is not valid"]})
        return data

    def to_representation(self, instance):
        data = super(DetailMemberSerializer, self).to_representation(instance)
        role = instance.role.name
        data["role"] = role
        if role in [MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER]:
            collection_members = list(instance.collections_members.values('collection_id', 'hide_passwords'))
            data["collections"] = [{
                "id": collection_member.get("collection_id"),
                "hide_passwords": collection_member.get("hide_passwords")
            } for collection_member in collection_members]
        else:
            collection_ids = list(instance.team.collections.values_list('id', flat=True))
            data["collections"] = [{
                "id": collection_id,
                "hide_passwords": False
            } for collection_id in collection_ids]
        data["pwd_user_id"] = instance.user.internal_id if instance.user else None
        return data


class CollectionSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=128)
    hide_passwords = serializers.BooleanField(default=False)


class UpdateMemberSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=TEAM_LIST_ROLE, required=True)
    collections = CollectionSerializer(many=True, allow_null=True)

    def validate(self, data):
        return data


class MemberGroupSerializer(serializers.Serializer):
    group_ids = serializers.ListField(
        child=serializers.CharField(max_length=128), allow_empty=True
    )
