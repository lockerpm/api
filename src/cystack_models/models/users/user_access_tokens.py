from django.db import models

from shared.utils.app import now
from cystack_models.models.users.user_refresh_tokens import UserRefreshToken


class UserAccessToken(models.Model):
    access_token = models.TextField()
    expired_time = models.FloatField()
    grant_type = models.CharField(max_length=128, blank=True, null=True, default="")
    refresh_token = models.ForeignKey(UserRefreshToken, on_delete=models.CASCADE, related_name="access_tokens")

    class Meta:
        db_table = 'cs_user_access_tokens'

    @classmethod
    def create(cls, refresh_token: UserRefreshToken,  **data):
        access_token = data.get("access_token")
        expired_time = data.get("expired_time")
        if not expired_time:
            expired_time = now() + data.get("expires_in", 3600)
        grant_type = data.get("grant_type", "refresh_token")
        new_token = cls(
            access_token=access_token, expired_time=expired_time, grant_type=grant_type,
            refresh_token=refresh_token
        )
        new_token.save()
        # Delete all expired token
        cls.objects.filter(expired_time__lt=now()).delete()
        return new_token
