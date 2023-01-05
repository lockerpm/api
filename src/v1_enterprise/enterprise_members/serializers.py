from django.db.models import Sum, Case, When, Value, IntegerField
from rest_framework import serializers

from shared.constants.ciphers import CIPHER_TYPE_LOGIN
from shared.constants.enterprise_members import *
from cystack_models.models.enterprises.members.enterprise_members import EnterpriseMember
from cystack_models.models.enterprises.groups.groups import EnterpriseGroup


class DetailMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseMember
        fields = ('id', 'access_time', 'is_default', 'is_primary', 'user_id', 'role', 'email', 'status', 'is_activated')
        read_only_fields = ('id', 'access_time', 'is_primary', 'status', 'is_activated')

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
        data["groups"] = list(instance.groups_members.values_list('group__name', flat=True))
        if instance.status != E_MEMBER_STATUS_INVITED:
            data["security_score"] = instance.user.master_password_score if instance.user else None
        else:
            data["security_score"] = None
            data["access_time"] = None
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


class DetailActiveMemberSerializer(DetailMemberSerializer):
    def to_representation(self, instance):
        data = super(DetailActiveMemberSerializer, self).to_representation(instance)
        data["login_block_until"] = instance.user.login_block_until if instance.user else None
        cipher_overview = {}
        if instance.user and instance.status != E_MEMBER_STATUS_INVITED:
            # Don't get ciphers from trash
            cipher_overview = instance.user.created_ciphers.filter(
                type=CIPHER_TYPE_LOGIN, deleted_date__isnull=True
            ).aggregate(
                cipher0=Sum(
                    Case(When(score=0, then=Value(1)), default=0), output_field=IntegerField()
                ),
                cipher1=Sum(
                    Case(When(score=1, then=Value(1)), default=0), output_field=IntegerField()
                ),
                cipher2=Sum(
                    Case(When(score=2, then=Value(1)), default=0), output_field=IntegerField()
                ),
                cipher3=Sum(
                    Case(When(score=3, then=Value(1)), default=0), output_field=IntegerField()
                ),
                cipher4=Sum(
                    Case(When(score=4, then=Value(1)), default=0), output_field=IntegerField()
                )
            )
        data["cipher_overview"] = cipher_overview
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


class SearchMemberGroupSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=255)
    user_ids = serializers.ListSerializer(
        child=serializers.IntegerField(), allow_null=True, allow_empty=True, required=False
    )


class EnterpriseGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseGroup
        fields = ('id', 'name', 'creation_date', 'revision_date')
        read_only_fields = ('id', 'name', 'creation_date', 'revision_date')
