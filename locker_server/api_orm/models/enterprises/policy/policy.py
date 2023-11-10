from django.forms import model_to_dict

from locker_server.api_orm.abstracts.enterprises.policy.policy import AbstractEnterprisePolicyORM
from locker_server.core.entities.enterprise.policy.policy_2fa import Policy2FA
from locker_server.core.entities.enterprise.policy.policy_failed_login import PolicyFailedLogin
from locker_server.core.entities.enterprise.policy.policy_master_password import PolicyMasterPassword
from locker_server.core.entities.enterprise.policy.policy_passwordless import PolicyPasswordless
from locker_server.shared.constants.policy import *


class EnterprisePolicyORM(AbstractEnterprisePolicyORM):
    class Meta(AbstractEnterprisePolicyORM.Meta):
        swappable = 'LS_ENTERPRISE_POLICY_MODEL'
        db_table = 'e_policy'

    @classmethod
    def create(cls, enterprise, policy_type: str, **kwargs):
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

    @classmethod
    def retrieve_or_create(cls, enterprise, policy_type: str, **kwargs):
        policy, is_created = cls.objects.get_or_create(enterprise=enterprise, policy_type=policy_type, defaults={
            "enterprise": enterprise, "policy_type": policy_type
        })
        if is_created is True:
            policy.create_detail(policy_type, **kwargs)
        return policy

    def create_detail(self, policy_type: str, **kwargs):
        if policy_type == POLICY_TYPE_PASSWORD_REQUIREMENT:
            from locker_server.core.entities.enterprise.policy.policy_password import PolicyPassword
            PolicyPassword.create(self, **kwargs)
        elif policy_type == POLICY_TYPE_MASTER_PASSWORD_REQUIREMENT:
            PolicyMasterPassword.create(self, **kwargs)
        elif policy_type == POLICY_TYPE_BLOCK_FAILED_LOGIN:
            PolicyFailedLogin.create(self, **kwargs)
        elif policy_type == POLICY_TYPE_PASSWORDLESS:
            PolicyPasswordless.create(self, **kwargs)
        elif policy_type == POLICY_TYPE_2FA:
            Policy2FA.create(self, **kwargs)

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
        elif policy_type == POLICY_TYPE_2FA:
            return self.policy_2fa

    def get_config_json(self):
        config_obj = self.get_config_obj()
        config_json = model_to_dict(
            config_obj, fields=[field.name for field in config_obj._meta.fields if field.name != 'policy']
        )
        return config_json
