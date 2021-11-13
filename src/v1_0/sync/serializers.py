from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from core.settings import CORE_CONFIG
from core.utils.data_helpers import convert_readable_date
from shared.constants.ciphers import *
from shared.constants.members import *
from cystack_models.models.users.users import User
from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.ciphers.folders import Folder
from cystack_models.models.teams.collections import Collection


class SyncProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def to_representation(self, instance):
        team_members = instance.team_members.filter(status=PM_MEMBER_STATUS_CONFIRMED, team__key__isnull=False)
        constant_team_data = {
            "object": "profileOrganization",
            "has_public_and_private_keys": True,
            "identifier": None,
            "maxCollections": 32767,
            "maxStorageGb": None,
            "permissions": {
                "access_business_portal": False,
                "access_event_logs": False,
                "access_import_export": False,
                "access_reports": False,
                "manage_all_collections": False,
                "manage_assigned_collections": False,
                "manage_groups": False,
                "manage_policies": False,
                "manage_reset_password": False,
                "manage_sso": False,
                "manage_users": False
            },
            "provider_id": None,
            "provider_name": None,
            "reset_password_enrolled": False,
            "seats": 32767,
            "self_host": True,
            "sso_bound": False,
            "use_2fa": True,
            "use_api": True,
            "use_business_portal": True,
            "use_directory": True,
            "use_events": True,
            "use_groups": True,
            "use_policies": True,
            "use_reset_password": True,
            "use_sso": True,
            "use_totp": True,
            "user_id": instance.internal_id,
            "users_get_premium": True,
        }
        organizations = []
        for team_member in team_members:
            team_member_data = constant_team_data.copy()
            team_member_data.update({
                "enabled": True if not team_member.team.locked else False,
                "id": team_member.team_id,
                "key": team_member.key,
                "name": team_member.team.name,
                "status": MAP_MEMBER_STATUS_TO_INT.get(team_member.status),
                "type": MAP_MEMBER_TYPE_BW.get(team_member.role_id),
            })
            organizations.append(team_member_data)
        data = {
            "object": "profile",
            "culture": "en-US",
            "id": instance.internal_id,
            "email": "",
            "name": "",
            "key": instance.key,
            "private_key": instance.private_key,
            "master_password_hint": instance.master_password_hint,
            "organizations": organizations,

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
        secure_note = cipher_detail if instance.type in [CIPHER_TYPE_NOTE, CIPHER_TYPE_TOTP] else None
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
            "view_password": instance.view_password
        }
        return data


class SyncFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ('id', 'name', 'revision_date')

    def to_representation(self, instance):
        data = {
            "object": "folder",
            "id": instance.id,
            "name": instance.name,
            "revision_date": convert_readable_date(instance.revision_date)
        }
        return data


class SyncCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = '__all__'

    def to_representation(self, instance):
        user = self.context["user"]
        team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
        role = team_repository.get_role_notify(team=instance.team, user=user).get("role")
        data = {
            "object": "collectionDetails",
            "id": instance.id,
            "name": instance.name,
            "organization_id": instance.team_id,
            "hide_passwords": False,
            "read_only": True if role == MEMBER_ROLE_MEMBER else False,
            "external_id": None,

        }
        return data
