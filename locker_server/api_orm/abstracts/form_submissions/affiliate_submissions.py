from django.db import models


class AbstractAffiliateSubmissionORM(models.Model):
    id = models.AutoField(primary_key=True)
    created_time = models.FloatField()
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=128)
    phone = models.CharField(max_length=128)
    company = models.CharField(max_length=128, blank=True, null=True, default="")
    country = models.CharField(max_length=128, null=True, default=None)
    status = models.CharField(max_length=64, default="submitted")

    class Meta:
        abstract = True
