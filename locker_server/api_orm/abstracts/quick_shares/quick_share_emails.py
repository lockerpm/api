import random
import string
import uuid

from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.utils.app import now


class AbstractQuickShareEmailORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    creation_date = models.FloatField()
    email = models.EmailField(max_length=255)
    code = models.CharField(max_length=32, null=True)
    code_expired_time = models.FloatField(null=True)
    max_access_count = models.PositiveIntegerField(null=True)
    access_count = models.PositiveIntegerField(default=0)
    quick_share = models.ForeignKey(
        locker_server_settings.LS_QUICK_SHARE_MODEL, on_delete=models.CASCADE, related_name="quick_share_emails"
    )

    class Meta:
        abstract = True
        unique_together = ('quick_share', 'email')

    @classmethod
    def create_multiple(cls, quick_share, emails_data):
        raise NotImplementedError

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
