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
        data["domain"] = {
            "id": instance.domain_id,
            "domain": instance.domain.domain
        } if instance.domain else None
        return data


class ShortDetailMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseMember
        fields = ('id', 'user_id', 'email', 'status')
        read_only_fields = ('id', 'user_id', 'email', 'status')

    def to_representation(self, instance):
        data = super(ShortDetailMemberSerializer, self).to_representation(instance)
        data["role"] = instance.role.name
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


class EnabledMemberSerializer(serializers.Serializer):
    activated = serializers.BooleanField()


class UserInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseMember
        fields = ('id', 'access_time', 'role', 'status')
        read_only_fields = ('id', 'access_time', 'role', 'status')

    def to_representation(self, instance):
        data = super(UserInvitationSerializer, self).to_representation(instance)
        data["enterprise"] = {
            "id": instance.enterprise_id,
            "name": instance.enterprise.name
        }
        data["owner"] = instance.enterprise.enterprise_members.get(is_primary=True).user_id
        if instance.domain is not None:
            data["domain"] = {
                "id": instance.domain.id,
                "domain": instance.domain.domain,
                "auto_approve": instance.domain.auto_approve
            }
        else:
            data["domain"] = None
        return data
