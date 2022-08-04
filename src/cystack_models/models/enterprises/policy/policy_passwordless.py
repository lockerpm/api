from django.db import models

from cystack_models.models.enterprises.policy.policy import EnterprisePolicy


class PolicyPasswordless(models.Model):
    policy = models.OneToOneField(
        EnterprisePolicy, to_field='id', primary_key=True, related_name="policy_passwordless", on_delete=models.CASCADE
    )
    only_allow_passwordless = models.BooleanField(default=False)

    class Meta:
        db_table = 'e_policy_passwordless'

    @classmethod
    def create(cls, policy, **kwargs):
        new_policy_passwordless = PolicyPasswordless(
            policy=policy,
            only_allow_passwordless=kwargs.get("only_allow_passwordless", False)
        )
        new_policy_passwordless.save()
        return new_policy_passwordless
