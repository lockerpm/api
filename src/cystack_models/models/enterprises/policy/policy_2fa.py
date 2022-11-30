from django.db import models

from cystack_models.models.enterprises.policy.policy import EnterprisePolicy


class Policy2FA(models.Model):
    policy = models.OneToOneField(
        EnterprisePolicy, to_field='id', primary_key=True, related_name="policy_2fa", on_delete=models.CASCADE
    )
    only_admin = models.BooleanField(default=True)

    class Meta:
        db_table = 'e_policy_2fa'

    @classmethod
    def create(cls, policy, **kwargs):
        new_policy_2fa = Policy2FA(
            policy=policy,
            only_admin=kwargs.get("only_admin", True)
        )
        new_policy_2fa.save()
        return new_policy_2fa
