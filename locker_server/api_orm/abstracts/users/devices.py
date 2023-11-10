import ast

from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.utils.app import now


class AbstractDeviceORM(models.Model):
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
        - fcm_id: The device FCM to send mobile notification
        - last_login: The latest login time of this device
        - os: The os of device
        - browser:
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
    last_login = models.FloatField(null=True)
    os = models.CharField(max_length=255, blank=True, default="")
    browser = models.CharField(max_length=255, blank=True, default="")
    user = models.ForeignKey(locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="user_devices")

    class Meta:
        abstract = True
        unique_together = ('device_identifier', 'user')

    @classmethod
    def create(cls, user, **data):
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
        os = data.get("os") or ""
        browser = data.get("browser") or ""

        # Create new device object
        new_device = cls(
            refresh_token=refresh_token, token_type=token_type, scope=scope,
            client_id=client_id, device_name=device_name, device_type=device_type, device_identifier=device_identifier,
            os=os, browser=browser,
            created_time=now(return_float=True), user=user
        )
        new_device.save()

        return new_device

    @classmethod
    def retrieve_or_create(cls, user_id: int, **data):
        device_identifier = data.get("device_identifier")
        os = data.get("os") or ""
        browser = data.get("browser") or ""
        device_obj, is_created = cls.objects.get_or_create(
            device_identifier=device_identifier, user_id=user_id, defaults={
                "user_id": user_id,
                "refresh_token": data.get("refresh_token"),
                "token_type": data.get("token_type"),
                "scope": data.get("scope"),
                "client_id": data.get("client_id"),
                "device_name": data.get("device_name"),
                "device_type": data.get("device_type"),
                "device_identifier": device_identifier,
                "os": os,
                "browser": browser,
                "created_time": now(return_float=True),
            }
        )
        if is_created is False:
            device_obj.os = os
            device_obj.browser = browser
            device_obj.save()
        return device_obj

    def get_os(self):
        if not self.os:
            return {}
        return ast.literal_eval(str(self.os))

    def get_browser(self):
        if not self.browser:
            return {}
        return ast.literal_eval(str(self.browser))
