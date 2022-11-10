import ast
import json
import uuid

from django.db import models

from shared.utils.app import now


class Event(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    type = models.CharField(max_length=16)
    acting_user_id = models.IntegerField(null=True)
    user_id = models.IntegerField(null=True)
    cipher_id = models.CharField(max_length=128, null=True)
    collection_id = models.CharField(max_length=128, null=True)
    creation_date = models.FloatField()
    device_type = models.IntegerField(null=True)
    group_id = models.CharField(max_length=128, null=True)
    ip_address = models.CharField(max_length=128, null=True, blank=True, default="")
    team_id = models.CharField(max_length=128, null=True)
    team_member_id = models.CharField(max_length=128, null=True)
    policy_id = models.CharField(max_length=128, null=True)
    provider_id = models.CharField(max_length=128, null=True)
    team_provider_id = models.CharField(max_length=128, null=True)
    user_provider_id = models.CharField(max_length=128, null=True)
    metadata = models.TextField(max_length=512, null=True, blank=True, default=None)

    class Meta:
        db_table = 'cs_events'

    @classmethod
    def create(cls, **data):
        new_event = cls(
            type=data["type"],
            acting_user_id=data.get("acting_user_id", data.get("user_id")),
            user_id=data.get("user_id"),
            cipher_id=data.get("cipher_id"),
            collection_id=data.get("collection_id"),
            creation_date=data.get("creation_date", now()),
            device_type=data.get("device_type"),
            group_id=data.get("group_id"),
            ip_address=data.get("ip_address"),
            team_id=data.get("team_id"),
            team_member_id=data.get("team_member_id"),
            policy_id=data.get("policy_id"),
            provider_id=data.get("provider_id"),
            team_provider_id=data.get("team_provider_id"),
            user_provider_id=data.get("user_provider_id")
        )
        new_event.save()
        return new_event

    @classmethod
    def create_multiple_by_team_ids(cls, team_ids: list, **data):
        events = []
        for team_id in team_ids:
            events.append(cls(
                type=data["type"],
                acting_user_id=data.get("acting_user_id"),
                user_id=data.get("user_id"),
                cipher_id=data.get("cipher_id"),
                collection_id=data.get("collection_id"),
                creation_date=data.get("creation_date", now()),
                device_type=data.get("device_type"),
                group_id=data.get("group_id"),
                ip_address=data.get("ip_address"),
                team_id=team_id,
                team_member_id=data.get("team_member_id"),
                policy_id=data.get("policy_id"),
                provider_id=data.get("provider_id"),
                team_provider_id=data.get("team_provider_id"),
                user_provider_id=data.get("user_provider_id"),
                metadata=data.get("metadata")
            ))
        cls.objects.bulk_create(events, ignore_conflicts=True)

    @classmethod
    def create_multiple_by_enterprise_members(cls, enterprise_members_data):
        events = []
        for data in enterprise_members_data:
            events.append(cls(
                type=data["type"],
                acting_user_id=data.get("acting_user_id"),
                user_id=data.get("user_id"),
                cipher_id=data.get("cipher_id"),
                collection_id=data.get("collection_id"),
                creation_date=data.get("creation_date", now()),
                device_type=data.get("device_type"),
                group_id=data.get("group_id"),
                ip_address=data.get("ip_address"),
                team_id=data.get("team_id"),
                team_member_id=data.get("team_member_id"),
                policy_id=data.get("policy_id"),
                provider_id=data.get("provider_id"),
                team_provider_id=data.get("team_provider_id"),
                user_provider_id=data.get("user_provider_id"),
                metadata=data.get("metadata")
            ))
        cls.objects.bulk_create(events, ignore_conflicts=True)

    @classmethod
    def create_multiple_by_ciphers(cls, ciphers, **data):
        events = []
        for cipher in ciphers:
            events.append(cls(
                type=data["type"],
                acting_user_id=data.get("acting_user_id"),
                user_id=data.get("user_id"),
                cipher_id=cipher.id,
                collection_id=data.get("collection_id"),
                creation_date=data.get("creation_date", now()),
                device_type=data.get("device_type"),
                group_id=data.get("group_id"),
                ip_address=data.get("ip_address"),
                team_id=cipher.team_id,
                team_member_id=data.get("team_member_id"),
                policy_id=data.get("policy_id"),
                provider_id=data.get("provider_id"),
                team_provider_id=data.get("team_provider_id"),
                user_provider_id=data.get("user_provider_id")
            ))
        cls.objects.bulk_create(events, ignore_conflicts=True)

    def get_metadata(self):
        if not self.metadata:
            return {}
        return ast.literal_eval(str(self.metadata))

    def get_normalizer_metadata(self):
        metadata = self.get_metadata()
        normalizer_metadata = {}
        for k, v in metadata.items():
            normalizer_metadata[k] = v.replace("_", " ").title() if isinstance(v, str) else v
        return normalizer_metadata
