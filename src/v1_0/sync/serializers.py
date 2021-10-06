from rest_framework import serializers

from core.settings import CORE_CONFIG
from cystack_models.models.users.users import User


class SyncProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def to_representation(self, instance):
        data = {
            "object": "profile",
            "culture": "en-US",
            "id": instance.internal_id,
            "email": "",
            "name": "",

            "key": instance.key,
            "private_key": instance.private_key,
            "master_password_hint": instance.master_password_hint,
            "organizations": [],

            "email_verified": True,
            "force_password_reset": False,
            "premium": False,
            "provider_organizations": [],
            "providers": [],
            "security_stamp": "",
            "twoFactorEnabled": False
        }
        return data
