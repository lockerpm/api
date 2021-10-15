from django.db import models


class PlanType(models.Model):
    name = models.CharField(max_length=128, primary_key=True)

    class Meta:
        db_table = 'cs_plan_types'
