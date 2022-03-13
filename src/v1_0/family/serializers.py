from rest_framework import serializers

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
        family_members = data.get("family_members")

        return data
