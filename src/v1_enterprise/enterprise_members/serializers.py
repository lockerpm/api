from rest_framework import serializers

from shared.constants.enterprise_members import *
from cystack_models.models.enterprises.members.enterprise_members import EnterpriseMember


class DetailMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseMember
        fields = ('id', 'access_time', 'is_default', 'is_primary', 'user_id', 'role', 'email', 'status')
        read_only_fields = ('id', 'access_time', 'is_primary', 'status')

    def validate(self, data):
        role = data.get("role")
        if role not in [E_MEMBER_ROLE_ADMIN, E_MEMBER_ROLE_MEMBER]:
            raise serializers.ValidationError(detail={"role": ["Role is not valid"]})
        return data

    def to_representation(self, instance):
        data = super(DetailMemberSerializer, self).to_representation(instance)
        data["role"] = instance.role.name
        data["pwd_user_id"] = instance.user.internal_id if instance.user else None
        return data


class UpdateMemberSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[E_MEMBER_ROLE_ADMIN, E_MEMBER_ROLE_MEMBER], default=E_MEMBER_ROLE_MEMBER)
