from django.db import models


class PromoCodeType(models.Model):
    name = models.CharField(primary_key=True, max_length=100)
    description = models.CharField(max_length=200)

    class Meta:
        db_table = 'cs_promo_code_types'
