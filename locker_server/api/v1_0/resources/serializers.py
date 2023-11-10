from rest_framework import serializers

from locker_server.shared.constants.transactions import *


class PMPlanSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.plan_id,
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


class RewardMissionSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.mission_id,
            "title": instance.title,
            "created_time": instance.created_time,
            "mission_type": instance.mission_type,
            "description": {
                "en": instance.description_en,
                "vi": instance.description_vi
            },
            "extra_requirements": instance.extra_requirements,

        }
        return data


class ListMailProviderSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.mail_provider_id,
            "name": instance.name,
            "available": instance.available,
        }
        return data