import ast

from django.db import models

from cystack_models.models.ciphers.ciphers import Cipher


class QuickShare(models.Model):
    cipher = models.OneToOneField(
        Cipher, to_field='id', primary_key=True, related_name="quick_share", on_delete=models.CASCADE
    )
    access_id = models.CharField(max_length=128, unique=True)
    creation_date = models.FloatField()
    revision_date = models.FloatField()
    deleted_date = models.FloatField(null=True)

    data = models.TextField(blank=True, null=True)
    key = models.TextField(null=True)
    password = models.CharField(max_length=512, null=True)
    max_access_count = models.PositiveIntegerField(null=True)
    access_count = models.PositiveIntegerField(default=0)
    expired_date = models.FloatField(null=True)
    disabled = models.FloatField(default=False)
    is_public = models.FloatField(default=True)
    require_otp = models.FloatField(default=False)

    class Meta:
        db_table = 'cs_quick_shares'

    def get_data(self):
        if not self.data:
            return {}
        return ast.literal_eval(str(self.data))


