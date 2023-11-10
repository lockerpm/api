from rest_framework import serializers

from locker_server.api.v1_0.payments.serializers import FamilyMemberSerializer
from locker_server.shared.utils.avatar import get_avatar


class UserPlanFamilySerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = {
            "id": instance.pm_user_plan_family_id,
            "created_time": instance.created_time,
            "email": instance.email
        }
        if instance.user:
            data.update({
                "full_name": instance.user.full_name,
                "username": instance.user.username,
                "avatar": instance.user.get_avatar(),
                "email": instance.user.email
            })
        else:
            data.update({
                "avatar": get_avatar(email=data.get("email"))
            })
        return data


class CreateUserPlanFamilySerializer(serializers.Serializer):
    family_members = serializers.ListSerializer(
        child=serializers.EmailField(), allow_empty=False
    )

    def validate(self, data):
        emails = data.get("family_members", [])
        current_user = self.context["request"].user
        if current_user.email in emails:
            emails.remove(current_user.email)
        data["family_members"] = emails
        return data
