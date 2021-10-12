import uuid

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

    class Meta:
        db_table = 'cs_teams'

    @classmethod
    def create(cls, **data):
        name = data.get("name")
        description = data.get("description", "")
        creation_date = data.get("creation_date", now())
        team_id = data.get("id")
        if not team_id:
            # Create new team object
            while True:
                team_id = random_n_digit(n=6)
                if cls.objects.filter(id=team_id).exists() is False:
                    break
        new_team = cls(
            id=team_id, name=name, description=description, creation_date=creation_date
        )
        new_team.save()

        # Create team members here
        members = data.get("members", [])
        new_team.team_members.model.create_multiple(new_team, *members)

        return new_team

    def lock_pm_team(self, lock):
        self.locked = lock
        self.save()
