from rest_framework import serializers

from cystack_models.models.enterprises.groups.groups import EnterpriseGroup


class EnterpriseGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseGroup
        fields = ('id', 'creation_date', 'revision_date', 'name')
        read_only_fields = ('id', 'creation_date', 'revision_date')

    def to_representation(self, instance):
        data = super(EnterpriseGroupSerializer, self).to_representation(instance)
        data["number_members"] = instance.groups_members.count()
        data["created_by"] = instance.created_by_id
        return data


class DetailEnterpriseGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseGroup
        fields = ('id', 'creation_date', 'revision_date', 'name')
        read_only_fields = ('id', 'creation_date', 'revision_date')

    def to_representation(self, instance):
        data = super(DetailEnterpriseGroupSerializer, self).to_representation(instance)
        groups_member_ids = list(
            instance.groups_members.all().order_by('member_id').values_list('member_id', flat=True)
        )
        instance = EnterpriseGroup.objects.get()
        members = instance.enterprise.enterprise_members.filter(
            id__in=groups_member_ids
        ).select_related('user').select_related('role')
        data["members"] = [{
            "user_id": member.user_id,
            "email": member.email,
            "status": member.status,
            "role": member.role.name,
            "domain_id": member.domain_id,
            "is_activated": member.is_activated,
            "public_key": member.user.public_key if member.user else None
        } for member in members]
        return data


class UpdateMemberGroupSerializer(serializers.Serializer):
    members = serializers.ListField(child=serializers.CharField(), allow_empty=True)
