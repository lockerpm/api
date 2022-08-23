from django.db import models

from shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from shared.utils.app import now, random_n_digit


class Enterprise(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=128, default="My Enterprise")
    description = models.CharField(max_length=255, blank=True, default="")
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    locked = models.BooleanField(default=False)
    enterprise_name = models.CharField(max_length=128, blank=True, default="")
    enterprise_address1 = models.CharField(max_length=255, blank=True, default="")
    enterprise_address2 = models.CharField(max_length=255, blank=True, default="")
    enterprise_phone = models.CharField(max_length=128, blank=True, default="")
    enterprise_country = models.CharField(max_length=128, blank=True, default="")
    enterprise_postal_code = models.CharField(max_length=16, blank=True, default="")
    # is_trial_applied = models.BooleanField(default=False)

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

    def lock_enterprise(self, lock: bool):
        self.locked = lock
        self.save()

    def get_activated_members_count(self):
        return self.enterprise_members.filter(
            status=E_MEMBER_STATUS_CONFIRMED, is_activated=True
        ).count()
