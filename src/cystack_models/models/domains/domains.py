from django.db import models

from cystack_models.models.teams.teams import Team
from shared.utils.app import now


class Domain(models.Model):
    id = models.AutoField(primary_key=True)
    created_time = models.FloatField()
    updated_time = models.FloatField(null=True)
    domain = models.CharField(max_length=128)
    root_domain = models.CharField(max_length=128)
    verification = models.BooleanField(default=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="domains")

    class Meta:
        db_table = 'cs_domains'

    @classmethod
    def create(cls, team: Team, domain: str, root_domain: str, verification: bool = False):
        new_domain = cls(
            team=team, domain=domain, root_domain=root_domain, verification=verification,
            created_time=now(), updated_time=now()
        )
        new_domain.save()

        # Create domain ownerships
        new_domain.domain_ownership.model.create(new_domain)

        return new_domain

    def set_verified(self):
        self.verification = True
        self.updated_time = now()
        self.save()

    def get_verifications(self):
        results = []
        ownerships = self.domain_ownership.select_related('ownership')
        for ownership in ownerships:
            results.append({
                "ownership_id": ownership.ownership_id,
                "ownership_description": ownership.ownership.description,
                "key": ownership.key,
                "value": ownership.value,

            })
        return results
