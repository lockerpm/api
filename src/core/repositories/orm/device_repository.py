from typing import Optional, List

import jwt

from django.conf import settings

from core.repositories import IDeviceRepository

from shared.utils.app import now
from cystack_models.models.users.users import User
from cystack_models.models.users.devices import Device
from cystack_models.models.users.device_access_tokens import DeviceAccessToken


class DeviceRepository(IDeviceRepository):
    def fetch_device_access_token(self, device: Device, renewal: bool = False,
                                  sso_token_id: str = None) -> DeviceAccessToken:
        """
        Get access token from existed device
        :param device: (obj) Device object
        :param renewal: (bool) If this value is True => Generate new access token
        :param sso_token_id: (str) CyStack SSO Token id
        :return:
        """
        valid_access_token = DeviceAccessToken.objects.filter(
            device=device, expired_time__gte=now()
        ).order_by('-expired_time').first()
        if not valid_access_token or renewal is True:
            # Generate new access token
            valid_access_token = DeviceAccessToken.create(device=device, **{
                "access_token": self._gen_access_token_value(device=device),
                "grant_type": "refresh_token",
                "expires_in": 3600,
                "sso_token_id": sso_token_id
            })
        return valid_access_token

    def _gen_access_token_value(self, device: Device):
        created_time = now()
        expired_time = created_time + 3600
        payload = {
            "nbf": created_time,
            "exp": expired_time,
            "iss": "https://locker.io",
            "client_id": device.client_id,
            "sub": device.user.internal_id,
            "auth_time": created_time,
            "idp": "cystack",
            "email_verified": device.user.activated,
            "scope": ["api", "offline_access"],
            "jti": device.id,
            "device": device.device_identifier,
            "orgowner": "",
            "iat": created_time,
            "amr": ["Application"]
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256').decode('utf-8')
        return token

    def fetch_user_access_token(self, user: User, sso_token_id: str = None) -> Optional[DeviceAccessToken]:
        access_token = DeviceAccessToken.objects.filter(
            device__user=user, sso_token_id=sso_token_id
        ).order_by('-expired_time').first()
        return access_token

    def get_device_by_identifier(self, user: User, device_identifier: str) -> Optional[Device]:
        try:
            device = Device.objects.get(user=user, device_identifier=device_identifier)
            return device
        except Device.DoesNotExist:
            return None

    def get_device_user(self, user: User):
        """
        Get list devices of the user
        :param user:
        :return:
        """
        return user.user_devices.all().order_by('-created_time')

    def get_devices_access_token(self, devices: List[Device]):
        """
        Get list access tokens from the list devices
        :param devices:
        :return:
        """
        return DeviceAccessToken.objects.filter(device__in=devices).order_by('-expired_time')

    def remove_devices_access_token(self, devices: List[Device]):
        """
        remove list access tokens from the list devices
        :param devices:
        :return:
        """
        return DeviceAccessToken.objects.filter(device__in=devices).delete()

    def update_fcm_id(self, device: Device, fcm_id: str = None):
        device.fcm_id = fcm_id
        device.save()
        return device
