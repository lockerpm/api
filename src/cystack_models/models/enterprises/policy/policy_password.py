from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from cystack_models.models.enterprises.policy.policy import EnterprisePolicy


class PolicyPassword(models.Model):
    policy = models.OneToOneField(
        EnterprisePolicy, to_field='id', primary_key=True, related_name="policy_password_requirement",
        on_delete=models.CASCADE
    )
    min_length = models.IntegerField(
        null=True, default=None, validators=[MinValueValidator(1), MaxValueValidator(128)]
    )
    require_lower_case = models.BooleanField(default=False)
    require_upper_case = models.BooleanField(default=False)
    require_special_character = models.BooleanField(default=False)
    require_digit = models.BooleanField(default=False)

    class Meta:
        db_table = 'e_policy_password'

    @classmethod
    def create(cls, policy, **kwargs):
        new_policy_password = cls(
            policy=policy,
            min_length=kwargs.get("min_length"),
            require_lower_case=kwargs.get("require_lower_case", False),
            require_upper_case=kwargs.get("require_upper_case", False),
            require_special_character=kwargs.get("require_special_character", False),
            require_digit=kwargs.get("require_digit", False)
        )
        new_policy_password.save()
        return new_policy_password
