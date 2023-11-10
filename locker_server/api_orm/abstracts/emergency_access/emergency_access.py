import uuid

from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.emergency_access import EMERGENCY_ACCESS_STATUS_INVITED
from locker_server.shared.utils.app import now


class AbstractEmergencyAccessORM(models.Model):
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
    grantee = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="emergency_grantees", null=True
    )
    grantor = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="emergency_grantors"
    )

    class Meta:
        abstract = True

    @classmethod
    def create(cls, grantor, access_type: str, wait_time_days: int = 7,
               grantee=None, email: str = None, key_encrypted: str = None):
        raise NotImplementedError
