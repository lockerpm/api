from django.db import models

from shared.utils.app import now
from cystack_models.models.users.users import User


class Device(models.Model):
    """
    This model manages all devices of the user. Each device has one device_identifier to identity the device.
    The Device object will generate device access tokens which are represented for a session.
    - created_time: The device client creation date
    - refresh_token: Random token string
    - token_type: The type of refresh token
    - scope: api offline_access (will be useful later)
    - client_id: The client id: browser / web / mobile
    - device_name: The device name
    - device_type: The device type: See more: /shared/constants/device_type.py
    - device_identifier: The device identifier
    - user: User object of this device
    """
    created_time = models.FloatField()
    refresh_token = models.CharField(max_length=255)
    token_type = models.CharField(max_length=128)
    scope = models.CharField(max_length=255)

    # Device information
    client_id = models.CharField(max_length=128)
    device_name = models.CharField(max_length=128, null=True)
    device_type = models.IntegerField(null=True)
    device_identifier = models.CharField(max_length=128)

    fcm_id = models.CharField(max_length=255, null=True, blank=True, default=None)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_devices")

    class Meta:
        db_table = 'cs_devices'
        unique_together = ('device_identifier', 'user')

    @classmethod
    def create(cls, user: User, **data):
        """
        Create new device object
        :param user: (obj) User object
        :param data: (dict) Device data
        :return:
        """
        refresh_token = data.get("refresh_token")
        token_type = data.get("token_type")
        scope = data.get("scope")

        client_id = data.get("client_id")
        device_name = data.get("device_name")
        device_type = data.get("device_type")
        device_identifier = data.get("device_identifier")

        # Create new device object
        new_device = cls(
            refresh_token=refresh_token, token_type=token_type, scope=scope,
            client_id=client_id, device_name=device_name, device_type=device_type, device_identifier=device_identifier,
            created_time=now(return_float=True), user=user
        )
        new_device.save()

        return new_device

    @classmethod
    def retrieve_or_create(cls, user, **data):
        device_identifier = data.get("device_identifier")
        device_obj = cls.objects.filter(device_identifier=device_identifier, user=user).first()
        if not device_obj:
            device_obj = cls.create(user, **data)
        return device_obj
