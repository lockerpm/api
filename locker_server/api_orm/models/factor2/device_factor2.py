from django.db import models

from locker_server.api_orm.models.factor2.factor2_method import Factor2MethodORM
from locker_server.settings import locker_server_settings
from locker_server.shared.constants.factor2 import FA2_EXPIRED_TIME
from locker_server.shared.utils.app import now


class DeviceFactor2ORM(models.Model):
    """
    This model stores device id in user's whitelist FA2 devices
    """

    id = models.AutoField(primary_key=True)
    expired_time = models.FloatField()
    factor2_method = models.ForeignKey(Factor2MethodORM, on_delete=models.CASCADE, related_name="device_factor2")
    device = models.ForeignKey(
        locker_server_settings.LS_DEVICE_MODEL, on_delete=models.CASCADE, related_name="device_factor2"
    )

    class Meta:
        db_table = 'cs_device_factor2'

    @classmethod
    def create(cls, factor2_method, device_id):
        new_device_factor2 = cls(
            device_id=device_id,
            factor2_method=factor2_method,
            expired_time=now() + FA2_EXPIRED_TIME * 86400,
        )
        new_device_factor2.save()
        return new_device_factor2
