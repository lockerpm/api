from django.db import models


class MailProviderORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=128)
    order_index = models.IntegerField(db_index=True)
    available = models.BooleanField(default=False)

    class Meta:
        db_table = 'cs_mail_providers'
