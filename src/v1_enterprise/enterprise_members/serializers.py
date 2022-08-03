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
    role = serializers.ChoiceField(
        choices=[E_MEMBER_ROLE_ADMIN, E_MEMBER_ROLE_MEMBER], default=E_MEMBER_ROLE_MEMBER, required=False
    )
    status = serializers.ChoiceField(choices=[E_MEMBER_STATUS_CONFIRMED], required=False)

    def validate(self, data):
        role = data.get("role")
        status = data.get("status")
        if status is None and role is None:
            raise serializers.ValidationError(detail={"role": ["The role or status is required"]})
        return data


class UserInvitationSerializeR(serializers.Serializer):
    class Meta:
        model = EnterpriseMember
        fields = ('id', 'access_time', 'role')
        read_only_fields = ('id', 'access_time', 'role')

    def to_representation(self, instance):
        data = super(UserInvitationSerializeR, self).to_representation(instance)
        data["status"] = instance.status
        data["enterprise"] = {
            "id": instance.enterprise_id,
            "name": instance.enterprise.name
        }
        data["role"] = instance.role_id
        if instance.domain is not None:
            data["domain"] = {
                "id": instance.domain.id,
                "domain": instance.domain.domain,
                "auto_approve": instance.domain.auto_approve
            }
        else:
            data["domain"] = None
        return data
