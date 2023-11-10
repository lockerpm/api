from rest_framework import serializers

from locker_server.shared.constants.enterprise_members import ENTERPRISE_LIST_ROLE, E_MEMBER_ROLE_MEMBER, \
    E_MEMBER_STATUS_CONFIRMED, E_MEMBER_STATUS_INVITED
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


class DetailMemberSerializer(serializers.Serializer):
    def to_representation(self, instance):
        list_group_member_func = self.context["list_group_member_func"]
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
        if callable(list_group_member_func):
            data["groups"] = list_group_member_func(enterprise_member_id=instance.enterprise_member_id)
        else:
            data["groups"] = []
        if instance.status != E_MEMBER_STATUS_INVITED:
            data["security_score"] = instance.user.master_password_score if instance.user else None
        else:
            data["security_score"] = None
            data["access_time"] = None
        data.update(get_detail_user_info(instance))
        return data


class CreateMemberSerializer(serializers.Serializer):
    is_default = serializers.BooleanField()
    role = serializers.ChoiceField(choices=ENTERPRISE_LIST_ROLE)
    user_id = serializers.CharField()


class ShortDetailMemberSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.enterprise_member_id,
            "role": instance.role.name,
            "email": instance.email,
            "status": instance.status,
        }
        data.update(get_detail_user_info(instance))
        return data


class DetailActiveMemberSerializer(DetailMemberSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["login_block_until"] = instance.user.login_block_until if instance.user else None
        return data


class UpdateMemberSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=ENTERPRISE_LIST_ROLE, default=E_MEMBER_ROLE_MEMBER, required=False
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


class UserInvitationSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.enterprise_member_id,
            "access_time": instance.access_time,
            "role": instance.role.name,
            "status": instance.status
        }
        data["enterprise"] = {
            "id": instance.enterprise.enterprise_id,
            "name": instance.enterprise.name
        }
        if instance.domain is not None:
            data["domain"] = {
                "id": instance.domain.domain_id,
                "domain": instance.domain.domain,
                "auto_approve": instance.domain.auto_approve
            }
        else:
            data["domain"] = None
        return data


class UpdateUserInvitationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["confirmed", "reject"])


class SearchMemberGroupSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=255)


class EnterpriseGroupSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.enterprise_group_id,
            "name": instance.name,
            "creation_date": instance.creation_date,
            "revision_date": instance.revision_date,
        }
        return data
