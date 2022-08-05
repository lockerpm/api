from django.db import models
from django.core.validators import MinValueValidator

from cystack_models.models.enterprises.policy.policy import EnterprisePolicy


class PolicyFailedLogin(models.Model):
    policy = models.OneToOneField(
        EnterprisePolicy, to_field='id', primary_key=True, related_name="policy_failed_login", on_delete=models.CASCADE
    )
    failed_login_attempts = models.IntegerField(null=True, default=None, validators=[MinValueValidator(1)])
    failed_login_duration = models.IntegerField(default=600, validators=[MinValueValidator(1)])     # 10 minutes
    failed_login_block_time = models.IntegerField(default=900, validators=[MinValueValidator(1)])   # Block 15 minutes
    failed_login_owner_email = models.BooleanField(default=False)

    class Meta:
        db_table = 'e_policy_failed_login'

    @classmethod
    def create(cls, policy, **kwargs):
        new_policy_failed_login = cls(
            policy=policy,
            failed_login_attempts=kwargs.get("failed_login_attempts", 1),
            failed_login_duration=kwargs.get("failed_login_duration", 1),
            failed_login_block_time=kwargs.get("failed_login_block_time", 1),
            failed_login_owner_email=kwargs.get("failed_login_owner_email", False),
        )
        new_policy_failed_login.save()
        return new_policy_failed_login
