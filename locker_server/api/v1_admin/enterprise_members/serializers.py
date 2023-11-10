from rest_framework import serializers

from locker_server.shared.constants.enterprise_members import ENTERPRISE_LIST_ROLE, E_MEMBER_ROLE_MEMBER
from locker_server.shared.utils.avatar import get_avatar


def get_detail_user_info(instance):
    if instance.user:
        data = {
            "full_name": instance.user.full_name,
            "avatar": instance.user.get_avatar(),
            "username": instance.user.username,
            "email": instance.user.email
        }
    else:
        data = {"avatar": get_avatar(instance.email)}
    return data


class ListMemberSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = dict()
        data.update({
            "id": instance.enterprise_member_id,
            "access_time": instance.access_time,
            "is_default": instance.is_default,
            "is_primary": instance.is_primary,
            "role": instance.role.name,
            "user_id": instance.user.user_id if instance.user else None,
            "email": instance.email,
            "status": instance.status,
            "is_activated": instance.is_activated,
        })
        data["role"] = instance.role.name
        data["pwd_user_id"] = instance.user.internal_id if instance.user else None
        data["domain"] = {
            "id": instance.domain.domain_id,
            "domain": instance.domain.domain
        } if instance.domain else None
        data.update(get_detail_user_info(instance))
        return data


class DetailMemberSerializer(ListMemberSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


class UpdateMemberSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=ENTERPRISE_LIST_ROLE, default=E_MEMBER_ROLE_MEMBER, required=False
    )
    is_primary = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        role = data.get("role")
        is_primary = data.get("is_primary")
        if role is None and is_primary is None:
            raise serializers.ValidationError(detail={"role": ["The role or is_primary is required"]})
        return data


class EnabledMemberSerializer(serializers.Serializer):
    activated = serializers.BooleanField()
