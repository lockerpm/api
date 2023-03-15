import uuid

from django.db import models

from cystack_models.models.quick_shares.quick_shares import QuickShare
from shared.utils.app import now


class QuickShareEmail(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    creation_date = models.FloatField()
    email = models.EmailField(max_length=255)
    code = models.CharField(max_length=32, null=True)
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
                    creation_date=email_data.get("creation_date", now())
                )
            )
        cls.objects.bulk_create(quick_share_emails_obj, ignore_conflicts=True, batch_size=50)
