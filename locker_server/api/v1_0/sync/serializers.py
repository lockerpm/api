from rest_framework import serializers

from locker_server.shared.constants.ciphers import *
from locker_server.shared.constants.members import MEMBER_ROLE_MEMBER, MAP_MEMBER_TYPE_BW, MAP_MEMBER_STATUS_TO_INT, \
    PM_MEMBER_STATUS_CONFIRMED
from locker_server.shared.utils.app import convert_readable_date


class SyncOrgDetailSerializer(serializers.Serializer):
    def to_representation(self, instance):
        list_group_member_roles_func = self.context.get("list_group_member_roles_func")

        role_id = instance.role.name
        group_member_roles = list_group_member_roles_func(instance)
        real_role = min([MAP_MEMBER_TYPE_BW.get(r) for r in group_member_roles + [role_id]])
        team_member_data = {
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
            "user_id": instance.user.internal_id,
            "users_get_premium": True,
            "enabled": True if not instance.team.locked else False,
            "id": instance.team.team_id,
            "key": instance.key,
            "name": instance.team.name,
            "status": MAP_MEMBER_STATUS_TO_INT.get(instance.status),
            "type": real_role,
        }
        return team_member_data


class SyncProfileSerializer(serializers.Serializer):
    def to_representation(self, instance):
        list_member_by_user_func = self.context.get("list_member_by_user_func")
        team_members = list_member_by_user_func(
            user_id=instance.user_id, status=PM_MEMBER_STATUS_CONFIRMED, team_key_null=False
        )
        organizations = []
        for team_member in team_members:
            organizations.append(SyncOrgDetailSerializer(
                team_member, many=False,
                context={"list_group_member_roles_func": self.context.get("list_group_member_roles_func")}
            ).data)
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


class SyncCipherSerializer(serializers.Serializer):
    def to_representation(self, instance):
        user = self.context["user"]
        data = instance.data
        cipher_detail = data.copy()
        cipher_detail.pop("name", None)
        cipher_detail.pop("notes", None)
        fields = cipher_detail.get("fields")
        cipher_detail.pop("fields", None)

        login = cipher_detail if instance.cipher_type in [CIPHER_TYPE_LOGIN, CIPHER_TYPE_MASTER_PASSWORD] else None
        secure_note = cipher_detail if instance.cipher_type in [CIPHER_TYPE_NOTE, CIPHER_TYPE_TOTP] else None
        card = cipher_detail if instance.cipher_type == CIPHER_TYPE_CARD else None
        identity = cipher_detail if instance.cipher_type == CIPHER_TYPE_IDENTITY else None
        crypto_account = cipher_detail if instance.cipher_type == CIPHER_TYPE_CRYPTO_ACCOUNT else None
        crypto_wallet = cipher_detail if instance.cipher_type == CIPHER_TYPE_CRYPTO_WALLET else None
        folder_id = instance.folders.get(user.user_id)
        favorite = instance.favorites.get(user.user_id, False)

        data = {
            "object": "cipherDetails",
            "attachments": None,
            "card": card,
            "crypto_account": crypto_account,
            "crypto_wallet": crypto_wallet,
            "collection_ids": instance.collection_ids,
            "data": data,
            "deleted_date": instance.deleted_date,
            "last_use_date": instance.last_use_date,
            "edit": True,
            "favorite": favorite,
            "fields": fields,
            "folder_id": folder_id,
            "id": instance.cipher_id,
            "identity": identity,
            "login": login,
            "name": data.get("name"),
            "notes": data.get("notes"),
            "organization_id": instance.team.team_id if instance.team else None,
            "organization_use_totp": True if login else False,
            "password_history": None,
            "reprompt": instance.reprompt,
            "revision_date": convert_readable_date(instance.revision_date),
            "creation_date": convert_readable_date(instance.creation_date),
            "secure_note": secure_note,
            "type": instance.cipher_type,
            "view_password": instance.view_password,
            "num_use": instance.num_use
        }
        return data


class SyncFolderSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "object": "folder",
            "id": instance.folder_id,
            "name": instance.name,
            "revision_date": convert_readable_date(instance.revision_date),
            "creation_date": convert_readable_date(instance.creation_date),
        }
        return data


class SyncCollectionSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "object": "collectionDetails",
            "id": instance.collection_id,
            "name": instance.name,
            "creation_date": convert_readable_date(instance.creation_date),
            "revision_date": convert_readable_date(instance.revision_date),
            "organization_id": instance.team.team_id,
            "hide_passwords": instance.hide_passwords,
            "external_id": None,
        }
        return data


class SyncEnterprisePolicySerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "object": "policyDetails",
            "enterprise_id": instance.enterprise.enterprise_id,
            "enabled": instance.enabled,
            "policy_type": instance.policy_type,
            "config": instance.config
        }
        return data
