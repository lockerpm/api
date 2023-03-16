import ast
import secrets

from django.db import models

from cystack_models.models.ciphers.ciphers import Cipher
from shared.utils.app import now


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

    @classmethod
    def update_or_create(cls, cipher: Cipher, **data):
        access_id = data.get("access_id") or cls.gen_access_id()
        is_public = data.get("is_public", True)
        quick_share, is_created = cls.objects.update_or_create(
            cipher_id=cipher.id, defaults={
                "access_id": access_id,
                "creation_date": data.get("creation_date", now()),
                "revision_date": data.get("revision_date", now()),
                "data": data.get("data"),
                "key": data.get("key"),
                "password": data.get("password"),
                "max_access_count": data.get("max_access_count"),
                "expired_date": data.get("expired_date"),
                "disabled": data.get("disabled", False),
                "is_public": is_public,
                "require_otp": data.get("require_otp", False)
            }
        )
        # Create quick share emails
        if is_public is False:
            emails_data = data.get("emails") or []
            quick_share.quick_share_emails.model.create_multiple(quick_share, emails_data)
        return quick_share

    @classmethod
    def gen_access_id(cls):
        return str(secrets.token_hex(16)).upper()

    def get_data(self):
        if not self.data:
            return {}
        return ast.literal_eval(str(self.data))


