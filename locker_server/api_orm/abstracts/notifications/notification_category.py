from django.db import models


class AbstractNotificationCategoryORM(models.Model):
    id = models.CharField(primary_key=True,  max_length=128)
    name = models.CharField(max_length=128)
    name_vi = models.CharField(max_length=128, blank=True)
    notification = models.BooleanField(default=True)
    mail = models.BooleanField(default=True)
    order_number = models.IntegerField()

    class Meta:
        abstract = True
