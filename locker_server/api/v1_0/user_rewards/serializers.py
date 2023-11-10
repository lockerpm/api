import json

from rest_framework import serializers


class ListUserRewardMissionSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "status": instance.status,
            "is_claimed": instance.is_claimed,
            "completed_time": instance.completed_time,
        }
        if instance.mission:
            mission = instance.mission
            extra_requirements = mission.get_extra_requirements()
            data.update({
                "mission": {
                    "id": "",
                    "title": "",
                    "created_time": "",
                    "mission_type": "",
                    "description": {
                        "en": mission.description_en,
                        "vi": mission.description_vi
                    },
                    "extra_requirements": extra_requirements
                }
            })
        answer = instance.get_answer()
        data.update({
            "answer": answer
        })
        return data


class UserRewardCheckCompletedSerializer(serializers.Serializer):
    user_identifier = serializers.CharField(max_length=255, allow_null=True)


class UserExtensionInstallCheckCompletedSerializer(serializers.Serializer):
    user_identifier = serializers.CharField(max_length=255)
    browser = serializers.CharField(max_length=128)


class ListRewardPromoCodeSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.promo_code_id,
            "created_time": instance.created_time,
            "expired_time": instance.expired_time,
            "code": instance.code,
            "valid": instance.valid,
            "value": instance.value,
            "description": {
                "vi": instance.description_vi,
                "en": instance.description_en
            },
            "type": instance.promo_code_type.name
        }
        return data
