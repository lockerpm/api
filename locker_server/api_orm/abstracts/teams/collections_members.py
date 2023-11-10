from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.members import MEMBER_ROLE_MEMBER


class AbstractCollectionMemberORM(models.Model):
    collection = models.ForeignKey(
        locker_server_settings.LS_COLLECTION_MODEL, on_delete=models.CASCADE, related_name="collections_members"
    )
    member = models.ForeignKey(
        locker_server_settings.LS_TEAM_MEMBER_MODEL, on_delete=models.CASCADE, related_name="collections_members"
    )
    read_only = models.BooleanField(default=False)
    hide_passwords = models.BooleanField(default=False)

    class Meta:
        abstract = True
        unique_together = ('collection', 'member')

    @classmethod
    def create_multiple(cls, member, *collections):
        collections_member = []
        read_only = True if member.role_id == MEMBER_ROLE_MEMBER else False
        for collection in collections:
            collections_member.append(
                cls(collection_id=collection.get("id"), member=member,
                    read_only=read_only, hide_passwords=collection.get("hide_passwords", False))
            )
        cls.objects.bulk_create(collections_member, ignore_conflicts=True)

    @classmethod
    def create_multiple_by_collection(cls, collection, *members):
        collection_members = []
        for member in members:
            read_only = True if member.get("role") == MEMBER_ROLE_MEMBER else False
            collection_members.append(
                cls(collection=collection, member_id=member.get("id"),
                    read_only=read_only, hide_passwords=member.get("hide_passwords", False))
            )
        cls.objects.bulk_create(collection_members, ignore_conflicts=True)

    @classmethod
    def retrieve_or_create(cls, collection_id, member_id, read_only=False, hide_passwords=False):
        collection_member, is_created = cls.objects.get_or_create(
            collection_id=collection_id, member_id=member_id, defaults={
                "collection_id": collection_id,
                "member_id": member_id,
                "read_only": read_only,
                "hide_passwords": hide_passwords
            }
        )
        return collection_member
