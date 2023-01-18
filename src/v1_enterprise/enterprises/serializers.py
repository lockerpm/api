from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from core.settings import CORE_CONFIG
from cystack_models.models.payments.country import Country
from cystack_models.models.enterprises.enterprises import Enterprise
from shared.constants.transactions import TRIAL_TEAM_PLAN
from shared.utils.app import now


class ListEnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = ('id', 'name', 'description', 'creation_date', 'revision_date', )
        read_only_fields = ('id', 'creation_date', 'revision_date', )

    def get_role_notify(self, instance):
        user = self.context["request"].user
        try:
            member = instance.enterprise_members.get(user=user)
            return {"role": member.role.name, "is_default": member.is_default}
        except ObjectDoesNotExist:
            return {"role": None, "is_default": None}

    def to_representation(self, instance):
        data = super(ListEnterpriseSerializer, self).to_representation(instance)
        view_action = self.context["view"].action
        role_notify = self.get_role_notify(instance=instance)
        data["locked"] = instance.locked
        data["organization_id"] = instance.id
        data["is_default"] = role_notify.get("is_default")
        data["role"] = role_notify.get("role")

        try:
            primary_admin = instance.get_primary_admin_user()
        except ObjectDoesNotExist:
            primary_admin = None
        if primary_admin:
            user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
            primary_admin_plan = user_repository.get_current_plan(user=primary_admin)
            data["is_trialing"] = False
            if primary_admin_plan.end_period and \
                    primary_admin_plan.end_period - primary_admin_plan.start_period < TRIAL_TEAM_PLAN:
                data["is_trialing"] = True
            data["end_period"] = primary_admin_plan.end_period

        if view_action == "retrieve":
            data["enterprise_name"] = instance.enterprise_name
            data["enterprise_address1"] = instance.enterprise_address1
            data["enterprise_address2"] = instance.enterprise_address2
            data["enterprise_phone"] = instance.enterprise_phone
            data["enterprise_country"] = instance.enterprise_country
            data["enterprise_postal_code"] = instance.enterprise_postal_code
            data["primary_admin"] = primary_admin.user_id if primary_admin else None
        return data


class UpdateEnterpriseSerializer(serializers.ModelSerializer):
    enterprise_name = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_address1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_address2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_phone = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_country = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_postal_code = serializers.CharField(max_length=16, required=False, allow_blank=True)

    class Meta:
        model = Enterprise
        fields = ('id', 'name', 'description', 'creation_date', 'revision_date',
                  'enterprise_name', 'enterprise_address1', 'enterprise_address2', 'enterprise_phone',
                  'enterprise_country', 'enterprise_postal_code')
        read_only_fields = ('id', 'creation_date', 'revision_date', )

    def validate(self, data):
        enterprise_country = data.get("enterprise_country")
        if enterprise_country and Country.objects.filter(country_name=enterprise_country).exists() is False:
            raise serializers.ValidationError(detail={"enterprise_country": ["The country does not exist"]})

        return data

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.enterprise_name = validated_data.get("enterprise_name", instance.enterprise_name)
        instance.enterprise_address1 = validated_data.get("enterprise_address1", instance.enterprise_address1)
        instance.enterprise_address2 = validated_data.get("enterprise_address2", instance.enterprise_address2)
        instance.enterprise_phone = validated_data.get("enterprise_phone", instance.enterprise_phone)
        instance.enterprise_country = validated_data.get("enterprise_country", instance.enterprise_country)
        instance.enterprise_postal_code = validated_data.get("enterprise_postal_code", instance.enterprise_postal_code)
        instance.revision_date = now()
        instance.save()
        return instance

