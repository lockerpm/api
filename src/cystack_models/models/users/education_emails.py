from django.db import models

from cystack_models.models.users.users import User
from shared.utils.app import now


class EducationEmail(models.Model):
    id = models.AutoField(primary_key=True)
    created_time = models.FloatField()
    email = models.EmailField(max_length=255, db_index=True)
    university = models.CharField(max_length=255, blank=True)
    verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=255)
    promo_code = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="education_emails")

    class Meta:
        db_table = 'cs_education_email'
        unique_together = ('user', 'email')

    @classmethod
    def retrieve_or_create(cls, user_id, **data):
        email = data.get("email")
        education_email, is_created = cls.objects.get_or_create(
            email=email, user_id=user_id, defaults={
                "user_id": user_id,
                "email": email,
                "created_time": now(),
                "verified": data.get("verified", False),
                "university": data.get("university"),
                "promo_code": data.get("promo_code")
            }
        )
        return education_email
