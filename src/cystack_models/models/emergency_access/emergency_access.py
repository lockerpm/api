import uuid

from django.db import models

from shared.utils.app import now
from shared.constants.emergency_access import EMERGENCY_ACCESS_STATUS_INVITED
from cystack_models.models.users.users import User


class EmergencyAccess(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    creation_date = models.IntegerField()
    revision_date = models.IntegerField()
    last_notification_date = models.IntegerField(null=True)
    recovery_initiated_date = models.IntegerField(null=True)
    status = models.CharField(max_length=128, default=EMERGENCY_ACCESS_STATUS_INVITED)
    type = models.CharField(max_length=128)
    wait_time_days = models.PositiveSmallIntegerField(default=7)
    key_encrypted = models.TextField(null=True)
    email = models.CharField(max_length=128, null=True)
    grantee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="emergency_grantees", null=True)
    grantor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="emergency_grantors")

    class Meta:
        db_table = 'cs_emergency_access'

    @classmethod
    def create(cls, grantor: User, access_type: str, wait_time_days: int = 7,
               grantee: User = None, email: str = None, key_encrypted: str = None):
        new_emergency_access = cls(
            grantor=grantor, type=access_type, wait_time_days=wait_time_days,
            key_encrypted=key_encrypted,
            grantee=grantee, email=email,
            creation_date=now(), revision_date=now()
        )
        new_emergency_access.save()
        return new_emergency_access
