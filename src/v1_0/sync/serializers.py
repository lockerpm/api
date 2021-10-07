from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from core.settings import CORE_CONFIG
from core.utils.data_helpers import convert_readable_date
from shared.constants.ciphers import *
from cystack_models.models.users.users import User
from cystack_models.models.ciphers.ciphers import Cipher


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


class SyncCipherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cipher
        fields = '__all__'

    def to_representation(self, instance):
        user = self.context["user"]
        data = instance.get_data()
        cipher_detail = data.copy()
        cipher_detail.pop("name", None)
        cipher_detail.pop("notes", None)

        login = cipher_detail if instance.type == CIPHER_TYPE_LOGIN else None
        secure_note = cipher_detail if instance.type == CIPHER_TYPE_NOTE else None
        card = cipher_detail if instance.type == CIPHER_TYPE_CARD else None
        identity = cipher_detail if instance.type == CIPHER_TYPE_IDENTITY else None
        folder_id = instance.get_folders().get(user.user_id)
        favorite = instance.get_favorites().get(user.user_id, False)
        data = {
            "object": "cipherDetails",
            "attachments": None,
            "card": card,
            "collection_ids": list(instance.collections_ciphers.values_list('collection_id', flat=True)),
            "data": data,
            "deleted_date": instance.deleted_date,
            "edit": True,
            "favorite": favorite,
            "fields": None,
            "folder_id": folder_id,
            "id": instance.id,
            "identity": identity,
            "login": login,
            "name": data.get("name"),
            "notes": data.get("notes"),
            "organization_id": instance.team_id,
            "organization_use_totp": True if login else False,
            "password_history": None,
            "reprompt": instance.reprompt,
            "revision_date": convert_readable_date(instance.revision_date),
            "secure_note": secure_note,
            "type": instance.type,
            "view_password": True
        }
        return data
