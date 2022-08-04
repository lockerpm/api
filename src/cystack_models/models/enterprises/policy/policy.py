from django.db import models
from django.forms import model_to_dict

from cystack_models.models.enterprises.enterprises import Enterprise
from shared.constants.policy import *


class EnterprisePolicy(models.Model):
    enterprise = models.ForeignKey(
        Enterprise, on_delete=models.CASCADE, related_name="policies"
    )
    enabled = models.BooleanField(default=False)
    policy_type = models.CharField(max_length=128)

    class Meta:
        db_table = 'e_policy'
        unique_together = ('enterprise', 'policy_type')

    @classmethod
    def create(cls, enterprise: Enterprise, policy_type: str, **kwargs):
        """
        Create policies for the enterprise
        :param enterprise: (obj) The Enterprise
        :param policy_type: (str) Policy type
        :param kwargs: (dict) Policy data
        :return:
        """
        new_policy = cls(enterprise=enterprise, policy_type=policy_type)
        new_policy.save()
        new_policy.create_detail(policy_type, **kwargs)

        return new_policy

    def create_detail(self, policy_type: str, **kwargs):
        if policy_type == POLICY_TYPE_PASSWORD_REQUIREMENT:
            from cystack_models.models.enterprises.policy.policy_password import PolicyPassword
            PolicyPassword.create(self, **kwargs)
        elif policy_type == POLICY_TYPE_MASTER_PASSWORD_REQUIREMENT:
            from cystack_models.models.enterprises.policy.policy_master_password import PolicyMasterPassword
            PolicyMasterPassword.create(self, **kwargs)
        elif policy_type == POLICY_TYPE_BLOCK_FAILED_LOGIN:
            from cystack_models.models.enterprises.policy.policy_failed_login import PolicyFailedLogin
            PolicyFailedLogin.create(self, **kwargs)
        elif policy_type == POLICY_TYPE_PASSWORDLESS:
            from cystack_models.models.enterprises.policy.policy_passwordless import PolicyPasswordless
            PolicyPasswordless.create(self, **kwargs)

    def get_config_obj(self):
        policy_type = self.policy_type
        if policy_type == POLICY_TYPE_PASSWORD_REQUIREMENT:
            return self.policy_password_requirement
        elif policy_type == POLICY_TYPE_MASTER_PASSWORD_REQUIREMENT:
            return self.policy_master_password_requirement
        elif policy_type == POLICY_TYPE_BLOCK_FAILED_LOGIN:
            return self.policy_failed_login
        elif policy_type == POLICY_TYPE_PASSWORDLESS:
            return self.policy_passwordless

    def get_config_json(self):
        config_obj = self.get_config_obj()
        config_json = model_to_dict(
            config_obj, fields=[field.name for field in config_obj._meta.fields if field.name != 'policy']
        )
        return config_json
