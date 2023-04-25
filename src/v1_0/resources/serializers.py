from rest_framework import serializers

from shared.constants.transactions import DURATION_MONTHLY, DURATION_YEARLY, DURATION_HALF_YEARLY
from cystack_models.models.user_plans.pm_plans import PMPlan
from cystack_models.models.user_rewards.missions import Mission


class PMPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PMPlan
        fields = '__all__'

    def to_representation(self, instance):
        data = {
            "id": instance.id,
            "name": instance.name,
            "alias": instance.alias,
            "max_number": instance.max_number,
            "price": {
                "usd": instance.get_price_usd(duration=DURATION_MONTHLY),
                "vnd": instance.get_price_vnd(duration=DURATION_MONTHLY),
                "duration": DURATION_MONTHLY,
            },
            "half_yearly_price": {
                "usd": instance.get_price_usd(duration=DURATION_HALF_YEARLY),
                "vnd": instance.get_price_vnd(duration=DURATION_HALF_YEARLY),
                "duration": DURATION_HALF_YEARLY,
            },
            "yearly_price": {
                "usd": instance.get_price_usd(duration=DURATION_YEARLY),
                "vnd": instance.get_price_vnd(duration=DURATION_YEARLY),
                "duration": DURATION_YEARLY,
            }
        }
        return data


class RewardMissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = ('id', 'title', 'created_time', 'mission_type', )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["description"] = {
            "en": instance.description_en,
            "vi": instance.description_vi
        }
        data["extra_requirements"] = instance.get_extra_requirements()
        return data
