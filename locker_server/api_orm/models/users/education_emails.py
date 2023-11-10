import jwt

from django.conf import settings
from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.token import TOKEN_EXPIRED_TIME_EDUCATION_CLAIM, TOKEN_TYPE_EDUCATION_CLAIM
from locker_server.shared.utils.app import now


class EducationEmailORM(models.Model):
    id = models.AutoField(primary_key=True)
    created_time = models.FloatField()
    email = models.EmailField(max_length=255, db_index=True)
    education_type = models.CharField(max_length=64, default="student")
    university = models.CharField(max_length=255, blank=True)
    verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=512, null=True)
    promo_code = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="education_emails"
    )

    class Meta:
        db_table = 'cs_education_email'
        unique_together = ('user', 'email')

    @classmethod
    def retrieve_or_create(cls, user_id, **data):
        email = data.get("email")
        verified = data.get("verified", False)
        education_type = data.get("education_type", "student")
        verification_token = None
        if verified is False:
            verification_token = cls.gen_verification_token(
                user_id=user_id, education_email=email, education_type=education_type
            )
        education_email, is_created = cls.objects.get_or_create(
            email=email, user_id=user_id, defaults={
                "user_id": user_id,
                "email": email,
                "created_time": now(),
                "verified": verified,
                "verification_token": verification_token,
                "education_type": education_type,
                "university": data.get("university"),
                "promo_code": data.get("promo_code")
            }
        )
        return education_email

    @classmethod
    def update_or_create(cls, user_id, **data):
        email = data.get("email")
        verified = data.get("verified", False)
        education_type = data.get("education_type", "student")
        verification_token = None
        if verified is False:
            verification_token = cls.gen_verification_token(
                user_id=user_id, education_email=email, education_type=education_type
            )
        education_email, is_created = cls.objects.update_or_create(
            email=email, user_id=user_id, defaults={
                "user_id": user_id,
                "email": email,
                "created_time": now(),
                "verified": verified,
                "verification_token": verification_token,
                "education_type": education_type,
                "university": data.get("university"),
                "promo_code": data.get("promo_code")
            }
        )
        return education_email

    @classmethod
    def gen_verification_token(cls, user_id, education_email, education_type):
        payload = {
            "scope": settings.SCOPE_PWD_MANAGER,
            "created_time": now(),
            "expired_time": now() + TOKEN_EXPIRED_TIME_EDUCATION_CLAIM,
            "user_id": user_id,
            "education_email": education_email,
            "education_type": education_type,
            "token_type": TOKEN_TYPE_EDUCATION_CLAIM
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return token
