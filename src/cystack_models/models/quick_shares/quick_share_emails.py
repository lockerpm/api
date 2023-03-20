import string
import uuid
import random

from django.db import models

from cystack_models.models.quick_shares.quick_shares import QuickShare
from shared.utils.app import now


class QuickShareEmail(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    creation_date = models.FloatField()
    email = models.EmailField(max_length=255)
    code = models.CharField(max_length=32, null=True)
    code_expired_time = models.FloatField(null=True)
    max_access_count = models.PositiveIntegerField(null=True)
    access_count = models.PositiveIntegerField(default=0)
    quick_share = models.ForeignKey(QuickShare, on_delete=models.CASCADE, related_name="quick_share_emails")

    class Meta:
        db_table = 'cs_quick_share_emails'
        unique_together = ('quick_share', 'email')

    @classmethod
    def create_multiple(cls, quick_share, emails_data):
        quick_share_emails_obj = []
        for email_data in emails_data:
            quick_share_emails_obj.append(
                cls(
                    quick_share=quick_share,
                    email=email_data.get("email"),
                    code=email_data.get("code"),
                    code_expired_time=email_data.get("code_expired_time"),
                    creation_date=email_data.get("creation_date", now()),
                    max_access_count=email_data.get("max_access_count"),
                    access_count=email_data.get("access_count", 0)
                )
            )
        cls.objects.bulk_create(quick_share_emails_obj, ignore_conflicts=True, batch_size=50)

    def clear_code(self):
        self.code = None
        self.code_expired_time = None
        self.save()

    def set_random_code(self):
        code = ''.join([random.choice(string.digits) for _ in range(6)])
        self.code = code
        # The code will be expired after 10 minutes
        self.code_expired_time = now() + 600
        self.save()

    def check_access(self) -> bool:
        if not self.max_access_count:
            return True
        return True if self.access_count < self.max_access_count else False
