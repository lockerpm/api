import ast
import secrets
import uuid

import jwt
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from cystack_models.models.ciphers.ciphers import Cipher
from shared.constants.token import TOKEN_TYPE_QUICK_SHARE_ACCESS
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
    each_email_access_count = models.PositiveIntegerField(null=True)
    max_access_count = models.PositiveIntegerField(null=True)
    access_count = models.PositiveIntegerField(default=0)
    expiration_date = models.FloatField(null=True)
    disabled = models.FloatField(default=False)
    is_public = models.BooleanField(default=True)
    require_otp = models.BooleanField(default=True)

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
            each_email_access_count=data.get("each_email_access_count"),
            max_access_count=data.get("max_access_count"),
            expiration_date=data.get("expiration_date"),
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

    def check_valid_access(self, email: str, code: str = None, token: str = None):
        if self.disabled is True:
            return False
        if self.is_public is False:
            try:
                quick_share_email = self.quick_share_emails.get(email=email)
            except ObjectDoesNotExist:
                return False
            if quick_share_email.max_access_count and \
                    quick_share_email.access_count >= quick_share_email.max_access_count:
                return False
            if not code and not token:
                return False
            if code and quick_share_email.code != code or quick_share_email.code_expired_time < now():
                return False
            if token and self.validate_public_access_token(email=quick_share_email.email, token=token) is False:
                return False
        if self.max_access_count and self.access_count >= self.max_access_count:
            return False
        if self.expiration_date and self.expiration_date < now():
            return False
        return True

    def generate_public_access_token(self, email):
        expired_time = now() + 30 * 86400
        payload = {
            "email": email,
            "created_time": now(),
            "expired_time": expired_time,
            "access_id": self.access_id,
            "token_type": TOKEN_TYPE_QUICK_SHARE_ACCESS
        }
        token_value = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return token_value, expired_time

    @staticmethod
    def validate_public_access_token(email, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get("token_type") != TOKEN_TYPE_QUICK_SHARE_ACCESS:
                return False
            if payload.get("email") != email:
                return False
            if payload.get("expired_time") < now():
                return False
            return True
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidAlgorithmError):
            return False
