from django.db import models


class AbstractEnterpriseORM(models.Model):
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

    # Init members seats
    init_seats = models.IntegerField(null=True, default=None)
    init_seats_expired_time = models.FloatField(null=True, default=None)

    class Meta:
        abstract = True

    @classmethod
    def create(cls, **data):
        raise NotImplementedError

    def lock_enterprise(self, lock: bool):
        self.locked = lock
        if lock is True:
            self.init_seats = None
            self.init_seats_expired_time = None
        self.save()
