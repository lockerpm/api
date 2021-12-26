from django.db import models

from shared.utils.app import now
from cystack_models.models.users.users import User


class UserRefreshToken(models.Model):
    """
    This model manages the devices of the user. The device is represented by a refresh token.
    The RefreshToken object will generate access tokens which are represented for a session.
    - created_time: The device client creation time
    - refresh_token: Random Refresh token string
    - scope: api offline_access (will be useful later)
    - client_id: The client id: browser / web / mobile
    - device_name: The device name
    - device_type: The device type. See more: /shared/constants/device_type.py
    - device_identifier: The device identifier.
    - user: User object of this device
    """
    created_time = models.FloatField()
    refresh_token = models.CharField(max_length=255)
    token_type = models.CharField(max_length=128)
    scope = models.CharField(max_length=255)

    # Device information of the refresh token
    client_id = models.CharField(max_length=128)                    # Ex: browser/web/mobile/desktop
    device_name = models.CharField(max_length=128, null=True)       # Ex: chrome, firefox, iPhone
    device_type = models.CharField(max_length=128, null=True)       # Ex: 9/10/...
    device_identifier = models.CharField(max_length=128)            # Device UUID

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_refresh_tokens")

    class Meta:
        db_table = 'cs_user_refresh_tokens'

    @classmethod
    def create(cls, user: User, **data):
        """
        Create new refresh token
        :param user: (obj) User object
        :param data:
        :return:
        """
        refresh_token = data.get("refresh_token")
        token_type = data.get("token_type")
        scope = data.get("scope")

        client_id = data.get("client_id")
        device_name = data.get("device_name")
        device_type = data.get("device_type")
        device_identifier = data.get("device_identifier")

        # Create new refresh token object
        new_refresh_token = cls(
            refresh_token=refresh_token, token_type=token_type, scope=scope,
            client_id=client_id, device_name=device_name, device_type=device_type, device_identifier=device_identifier,
            user=user, created_time=now(return_float=True)
        )
        new_refresh_token.save()
        # Create access token (optional)
        access_token = data.get("access_token")
        if access_token:
            new_refresh_token.access_tokens.model.create(new_refresh_token, **{
                "access_token": data.get("access_token"),
                "expires_in": data.get("expires_in", 3600),
                "grant_type": data.get("grant_type", ""),
                "sso_token_id": data.get("sso_token_id")
            })
        return new_refresh_token

    @classmethod
    def retrieve_or_create(cls, user: User, **data):
        device_identifier = data.get("device_identifier")
        refresh_token_obj = cls.objects.filter(device_identifier=device_identifier, user=user).first()
        if not refresh_token_obj:
            refresh_token_obj = cls.create(user, **data)
        return refresh_token_obj
