from rest_framework import serializers

from shared.constants.transactions import DURATION_MONTHLY, DURATION_YEARLY, DURATION_HALF_YEARLY
from cystack_models.models.user_plans.pm_plans import PMPlan


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
            "max_device": instance.max_device,
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
