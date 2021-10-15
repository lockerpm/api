from django.db import models

from cystack_models.models.teams.collections import Collection
from cystack_models.models.teams.groups import Group


class CollectionGroup(models.Model):
    read_only = models.BooleanField(default=False)
    hide_passwords = models.BooleanField(default=False)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="collections_groups")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="collections_groups")

    class Meta:
        db_table = 'cs_collections_groups'
        unique_together = ('collection', 'group', )

    @classmethod
    def create_multiple(cls, collection: Collection, *groups):
        collection_groups = []
        for group in groups:
            collection_groups.append(
                cls(
                    collection=collection,
                    group_id=group.get("id"),
                    hide_passwords=group.get("hide_passwords", False),
                    read_only=group.get("read_only", False)
                )
            )
        cls.objects.bulk_create(collection_groups, ignore_conflicts=True)

    @classmethod
    def create_multiple_by_group(cls, group: Group, *collections):
        collection_groups = []
        for collection in collections:
            collection_groups.append(
                cls(
                    group=group,
                    collection_id=collection.get("id"),
                    hide_passwords=collection.get("hide_passwords", False),
                    read_only=collection.get("read_only", False)
                )
            )
        cls.objects.bulk_create(collection_groups, ignore_conflicts=True)
