from django.conf import settings
from rest_framework import serializers

from core.settings import CORE_CONFIG
from shared.constants.transactions import PLAN_TYPE_PM_ENTERPRISE
from shared.utils.app import now
from cystack_models.models.teams.teams import Team


class ListTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'name', 'description', 'creation_date', 'revision_date', )
        read_only_fields = ('id', 'creation_date', 'revision_date',)

    def to_representation(self, instance):
        team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        data = super(ListTeamSerializer, self).to_representation(instance)
        _user = self.context["request"].user
        role_notify = team_repository.get_role_notify(team=instance, user=_user)
        data["locked"] = team_repository.is_locked(team=instance)
        data["organization_id"] = instance.id
        data["id"] = instance.id
        data["is_default"] = role_notify.get("is_default")
        data["role"] = role_notify.get("role")

        # Retrieve current plan of this team
        primary_member = team_repository.get_primary_member(team=instance)
        pm_plan = user_repository.get_current_plan(user=primary_member.user)
        pm_plan_alias = pm_plan.get_plan_type_alias()
        pm_plan_name = pm_plan.get_plan_type_name()
        data["is_business"] = True if pm_plan_alias == PLAN_TYPE_PM_ENTERPRISE else False
        data["plan_name"] = pm_plan_name
        return data


class UpdateTeamPwdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'name', 'description', 'created_time', 'updated_time', )
        read_only_fields = ('id', 'created_time', 'updated_time', )

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.updated_time = now()
        instance.save()
        return instance
