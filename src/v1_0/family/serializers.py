from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from core.settings import CORE_CONFIG
from shared.constants.members import *
from cystack_models.models.user_plans.pm_user_plan_family import PMUserPlanFamily
from v1_0.payments.serializers import FamilyMemberSerializer


class UserPlanFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = PMUserPlanFamily
        fields = ('id', 'created_time', 'user_id', 'email')
        read_only_fields = ('id', 'created_time', 'user_id', 'email')

    def to_representation(self, instance):
        return super(UserPlanFamilySerializer, self).to_representation(instance)


class CreateUserPlanFamilySeriaizer(serializers.Serializer):
    family_members = FamilyMemberSerializer(many=True, required=True)

    def validate(self, data):
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        family_members = data.get("family_members")
        for family_member in family_members:
            user_id = family_member.get("user_id")
            email = family_member.get("email")
            if user_id:
                try:
                    user = user_repository.get_by_id(user_id=user_id)
                    if not user.activated:
                        continue
                except ObjectDoesNotExist:
                    continue
                current_plan = user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
                if current_plan.get_plan_obj().is_family_plan or current_plan.get_plan_obj().is_team_plan:
                    raise serializers.ValidationError(detail={
                        "family_members": ["The user {} is in other family plan".format(email)]
                    })

        return data
