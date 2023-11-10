from django.db import models

from locker_server.settings import locker_server_settings


class AbstractUserScoreORM(models.Model):
    user = models.OneToOneField(
        locker_server_settings.LS_USER_MODEL, to_field='user_id',
        primary_key=True, related_name="user_score", on_delete=models.CASCADE
    )
    cipher0 = models.FloatField(default=0)
    cipher1 = models.FloatField(default=0)
    cipher2 = models.FloatField(default=0)
    cipher3 = models.FloatField(default=0)
    cipher4 = models.FloatField(default=0)
    cipher5 = models.FloatField(default=0)
    cipher6 = models.FloatField(default=0)
    cipher7 = models.FloatField(default=0)

    class Meta:
        abstract = True

    @classmethod
    def create(cls, user):
        raise NotImplementedError
