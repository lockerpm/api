from django.db import models

from shared.constants.members import MEMBER_ROLE_MEMBER
from cystack_models.models.members.team_members import TeamMember
from cystack_models.models.teams.collections import Collection


class CollectionMember(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="collections_members")
    member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name="collections_members")
    read_only = models.BooleanField(default=False)
    hide_passwords = models.BooleanField(default=False)

    class Meta:
        db_table = 'cs_collections_members'
        unique_together = ('collection', 'member')

    @classmethod
    def create_multiple(cls, member: TeamMember, *collections):
        collections_member = []
        read_only = True if member.role_id == MEMBER_ROLE_MEMBER else False
        for collection_id in collections:
            collections_member.append(
                cls(collection_id=collection_id, member=member, read_only=read_only, hide_passwords=False)
            )
        cls.objects.bulk_create(collections_member, ignore_conflicts=True)
