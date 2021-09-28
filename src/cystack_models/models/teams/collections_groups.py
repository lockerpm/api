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
