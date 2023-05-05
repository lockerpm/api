import json
from json import JSONDecodeError

from django.db import models

from shared.constants.missions import REWARD_TYPE_PROMO_CODE
from shared.utils.app import now


class Mission(models.Model):
    id = models.CharField(primary_key=True, max_length=128)
    title = models.CharField(max_length=128)
    description_en = models.CharField(max_length=255, blank=True, default="")
    description_vi = models.CharField(max_length=255, blank=True, default="")
    created_time = models.IntegerField()
    mission_type = models.CharField(max_length=64)
    order_index = models.IntegerField()
    available = models.BooleanField(default=True)
    extra_requirements = models.CharField(max_length=255, blank=True, null=True, default=None)
    reward_type = models.CharField(max_length=64, default=REWARD_TYPE_PROMO_CODE)
    reward_value = models.FloatField(default=0)

    class Meta:
        db_table = 'cs_missions'
        ordering = ['-order_index']

    @classmethod
    def create(cls, **data):
        new_mission = cls(
            id=data.get("id"),
            title=data.get("title"),
            description_en=data.get("description_en"),
            description_vi=data.get("description_vi"),
            created_time=data.get("created_time") or now(),
            mission_type=data.get("mission_type"),
            order_index=data.get("order_index"),
            extra_requirements=data.get("extra_requirements")
        )
        new_mission.save()
        return new_mission

    def get_extra_requirements(self):
        if not self.extra_requirements:
            return {}
        try:
            return json.loads(str(self.extra_requirements))
        except JSONDecodeError:
            return self.extra_requirements
