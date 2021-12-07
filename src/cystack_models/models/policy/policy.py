from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from cystack_models.models.teams.teams import Team


class Policy(models.Model):
    team = models.OneToOneField(
        Team, to_field='id', primary_key=True, related_name="policy", on_delete=models.CASCADE
    )
    min_password_length = models.IntegerField(
        null=True, default=None, validators=[MinValueValidator(1), MaxValueValidator(128)]
    )
    max_password_length = models.IntegerField(
        null=True, default=None, validators=[MinValueValidator(1), MaxValueValidator(128)]
    )
    password_composition = models.BooleanField(default=False)
    require_lower_case = models.BooleanField(default=False)
    require_upper_case = models.BooleanField(default=False)
    require_special_character = models.BooleanField(default=False)
    require_digit = models.BooleanField(default=False)
    avoid_ambiguous_character = models.BooleanField(default=False)

    ip_allow = models.TextField(blank=True, default="", max_length=512)
    ip_block = models.TextField(blank=True, default="", max_length=512)

    block_mobile = models.BooleanField(default=False)

    failed_login_attempts = models.IntegerField(null=True, default=None, validators=[MinValueValidator(1)])
    failed_login_duration = models.IntegerField(default=600, validators=[MinValueValidator(1)])     # 10 minutes
    failed_login_block_time = models.IntegerField(default=900, validators=[MinValueValidator(1)])   # Block 15 minutes
    failed_login_owner_email = models.BooleanField(default=False)

    class Meta:
        db_table = 'cs_policy'

    @classmethod
    def create(cls, team: Team, **data):
        new_policy = cls(
            team=team,
            min_password_length=data.get("min_password_length"),
            max_password_length=data.get("max_password_length"),
            password_composition=data.get("password_composition", False),
            require_lower_case=data.get("require_lower_case", False),
            require_upper_case=data.get("require_upper_case", False),
            require_special_character=data.get("require_special_character", False),
            require_digit=data.get("require_digit", False),
            avoid_ambiguous_character=data.get("avoid_ambiguous_character", False),

            ip_allow=data.get("ip_allow", ""),
            ip_block=data.get("ip_block", ""),
            block_mobile=data.get("block_mobile", False),

            failed_login_attempts=data.get("failed_login_attempts"),
            failed_login_duration=data.get("failed_login_duration", 600),
            failed_login_block_time=data.get("failed_login_block_time", 900),
            failed_login_owner_email=data.get("failed_login_owner_email", False)
        )
        new_policy.save()
        return new_policy

    def get_list_ip_allow(self):
        if not self.ip_allow:
            return []
        return self.ip_allow.split(",")

    def get_list_ip_block(self):
        if not self.ip_block:
            return []
        return self.ip_block.split(",")
