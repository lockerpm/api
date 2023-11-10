from django.db import models


class AbstractPlanTypeORM(models.Model):
    name = models.CharField(max_length=128, primary_key=True)

    class Meta:
        abstract = True
