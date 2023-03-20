import ast
import secrets
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from cystack_models.models.ciphers.ciphers import Cipher
from shared.utils.app import now


class QuickShare(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    cipher = models.ForeignKey(Cipher, on_delete=models.CASCADE, related_name="quick_shares")
    access_id = models.CharField(max_length=128, unique=True)
    creation_date = models.FloatField()
    revision_date = models.FloatField()
    deleted_date = models.FloatField(null=True)

    type = models.IntegerField()
    data = models.TextField(blank=True, null=True)
    key = models.TextField(null=True)
    password = models.CharField(max_length=512, null=True)
    max_access_count = models.PositiveIntegerField(null=True)
    access_count = models.PositiveIntegerField(default=0)
    expired_date = models.FloatField(null=True)
    disabled = models.FloatField(default=False)
    is_public = models.BooleanField(default=True)
    require_otp = models.FloatField(default=True)

    class Meta:
        db_table = 'cs_quick_shares'

    @classmethod
    def create(cls, **data):
        access_id = data.get("access_id") or cls.gen_access_id()
        is_public = data.get("is_public", True)
        quick_share = cls(
            access_id=access_id,
            cipher_id=data.get("cipher_id"),
            creation_date=data.get("creation_date") or now(),
            revision_date=data.get("revision_date") or now(),
            type=data.get("type"),
            data=data.get("data"),
            key=data.get("key"),
            password=data.get("password"),
            max_access_count=data.get("max_access_count"),
            expired_date=data.get("expired_date"),
            disabled=data.get("disabled", False),
            is_public=is_public,
            require_otp=data.get("require_otp", True)
        )
        quick_share.save()
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

    def check_valid_access(self, email: str, code: str):
        if self.disabled is True:
            return False
        if self.is_public is False:
            try:
                quick_share_email = self.quick_share_emails.get(email=email)
                if quick_share_email.code != code or quick_share_email.code_expired_time < now():
                    return False
            except ObjectDoesNotExist:
                return False
        if self.max_access_count and self.access_count >= self.max_access_count:
            return False
        if self.expired_date and self.expired_date < now():
            return False
        return True
