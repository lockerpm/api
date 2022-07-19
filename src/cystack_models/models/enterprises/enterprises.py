from django.db import models

from shared.utils.app import now, random_n_digit


class Enterprise(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=128, default="My Enterprise")
    description = models.CharField(max_length=255, blank=True, default="")
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    locked = models.BooleanField(default=False)
    # key = models.CharField(max_length=512, null=True)
    # default_collection_name = models.CharField(max_length=512, null=True)
    # public_key = models.TextField(null=True)
    # private_key = models.TextField(null=True)

    class Meta:
        db_table = 'e_enterprises'

    @classmethod
    def create(cls, **data):
        name = data.get("name")
        description = data.get("description", "")
        creation_date = data.get("creation_date", now())
        enterprise_id = data.get("id")
        if not enterprise_id:
            # Create new team id
            while True:
                enterprise_id = random_n_digit(n=6)
                if cls.objects.filter(id=enterprise_id).exists() is False:
                    break
        new_enterprise = cls(
            id=enterprise_id, name=name, description=description, creation_date=creation_date
        )
        new_enterprise.save()

        # Create team members
        members = data.get("members", [])
        new_enterprise.enterprise_members.model.create_multiple(new_enterprise, *members)

        return new_enterprise
