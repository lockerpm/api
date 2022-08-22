from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from cystack_models.models.enterprises.enterprises import Enterprise
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

        if view_action == "retrieve":
            data["enterprise_name"] = instance.enterprise_name
            data["enterprise_address"] = instance.enterprise_address
            data["enterprise_phone"] = instance.enterprise_phone
            data["primary_admin"] = instance.enterprise_members.get(is_primary=True).user_id
        return data


class UpdateEnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = ('id', 'name', 'description', 'created_time', 'updated_time', )
        read_only_fields = ('id', 'created_time', 'updated_time', )

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.updated_time = now()
        instance.save()
        return instance

