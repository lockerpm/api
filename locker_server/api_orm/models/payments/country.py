from django.db import models


class CountryORM(models.Model):
    country_code = models.CharField(primary_key=True, max_length=2)
    country_name = models.CharField(max_length=128)
    country_phone_code = models.CharField(max_length=10, default=None)

    class Meta:
        db_table = 'cs_countries'
