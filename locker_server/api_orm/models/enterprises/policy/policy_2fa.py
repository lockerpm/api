from django.db import models

from locker_server.settings import locker_server_settings


class Policy2FAORM(models.Model):
    policy = models.OneToOneField(
        locker_server_settings.LS_ENTERPRISE_POLICY_MODEL, to_field='id', primary_key=True,
        related_name="policy_2fa", on_delete=models.CASCADE
    )
    only_admin = models.BooleanField(default=True)

    class Meta:
        db_table = 'e_policy_2fa'

    @classmethod
    def create(cls, policy, **kwargs):
        new_policy_2fa = cls(
            policy=policy,
            only_admin=kwargs.get("only_admin", True)
        )
        new_policy_2fa.save()
        return new_policy_2fa
