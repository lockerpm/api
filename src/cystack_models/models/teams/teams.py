import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from shared.utils.app import random_n_digit, now


class Team(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    name = models.CharField(max_length=128, blank=True, default="My Team")
    description = models.CharField(max_length=255, blank=True, default="")
    creation_date = models.FloatField(null=True)
    revision_date = models.FloatField(null=True)
    locked = models.BooleanField(default=False)
    business_name = models.CharField(max_length=128, blank=True, default="")
    key = models.CharField(max_length=512, null=True)
    default_collection_name = models.CharField(max_length=512, null=True)
    public_key = models.TextField(null=True)
    private_key = models.TextField(null=True)
    personal_share = models.BooleanField(default=False)

    class Meta:
        db_table = 'cs_teams'

    @classmethod
    def create(cls, **data):
        name = data.get("name")
        description = data.get("description", "")
        creation_date = data.get("creation_date", now())
        personal_share = data.get("personal_share", False)
        team_id = data.get("id")
        if not team_id:
            # Create new team object
            while True:
                team_id = random_n_digit(n=6)
                if cls.objects.filter(id=team_id).exists() is False:
                    break
        new_team = cls(
            id=team_id, name=name, description=description, creation_date=creation_date, personal_share=personal_share
        )
        new_team.save()

        # Create team members here
        members = data.get("members", [])
        new_team.team_members.model.create_multiple(new_team, *members)

        return new_team

    def lock_pm_team(self, lock):
        self.locked = lock
        self.save()

    def get_member_obj(self, user):
        try:
            return self.team_members.get(user=user)
        except ObjectDoesNotExist:
            return None
