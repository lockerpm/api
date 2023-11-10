from django.db import models


class AbstractRelayDomainORM(models.Model):
    id = models.CharField(primary_key=True, max_length=64)

    class Meta:
        abstract = True

    @classmethod
    def create(cls, id: str):
        return cls.objects.create(id=id)
