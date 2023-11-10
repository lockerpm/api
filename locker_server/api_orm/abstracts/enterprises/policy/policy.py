from django.db import models
from django.forms import model_to_dict

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.policy import *


class AbstractEnterprisePolicyORM(models.Model):
    enterprise = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_MODEL, on_delete=models.CASCADE, related_name="policies"
    )
    enabled = models.BooleanField(default=False)
    policy_type = models.CharField(max_length=128)

    class Meta:
        abstract = True
        unique_together = ('enterprise', 'policy_type')


