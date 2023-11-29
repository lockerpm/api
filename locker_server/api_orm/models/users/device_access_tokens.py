import jwt

from django.conf import settings

from locker_server.api_orm.abstracts.users.device_access_tokens import AbstractDeviceAccessTokenORM
from locker_server.shared.constants.device_type import *
from locker_server.shared.utils.app import now


class DeviceAccessTokenORM(AbstractDeviceAccessTokenORM):
    class Meta(AbstractDeviceAccessTokenORM.Meta):
        swappable = 'LS_DEVICE_ACCESS_TOKEN_MODEL'
        db_table = 'cs_device_access_tokens'

    @classmethod
    def create(cls, device, **data):
        access_token = data.get("access_token")
        expired_time = data.get("expired_time")
        sso_token_id = data.get("sso_token_id")
        credential_key = data.get("credential_key")
        if not expired_time:
            expired_time = now() + data.get("expires_in", cls.get_token_duration(device.client_id))
        grant_type = data.get("grant_type", "refresh_token")
        new_token = cls(
            access_token=access_token, expired_time=expired_time, grant_type=grant_type,
            device=device, sso_token_id=sso_token_id
        )
        new_token.save()
        # Generate jwt access token
        new_token.access_token = new_token._gen_access_token_value(
            expired_time=expired_time,
            credential_key=credential_key
        )
        new_token.save()
        # Delete all expired token
        cls.objects.filter(device__user=device.user, expired_time__lt=now()).delete()
        return new_token

    @classmethod
    def get_token_duration(cls, client_id):
        if client_id in [CLIENT_ID_MOBILE, CLIENT_ID_BROWSER, CLIENT_ID_DESKTOP]:
            return 30 * 86400
        return 4 * 3600

    def _gen_access_token_value(self, expired_time, credential_key):
        created_time = now()
        payload = {
            "nbf": created_time,
            "exp": expired_time,
            "iss": "https://locker.io",
            "client_id": self.device.client_id,
            "sub": self.device.user.internal_id,
            "auth_time": created_time,
            "idp": "cystack",
            "email_verified": self.device.user.activated,
            "scope": ["api", "offline_access"],
            "jti": self.id,
            "device": self.device.device_identifier,
            "orgowner": "",
            "iat": created_time,
            "amr": ["Application"],
            "credential_key": credential_key
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return token
