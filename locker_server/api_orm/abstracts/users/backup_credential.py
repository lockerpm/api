import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.account import DEFAULT_KDF_ITERATIONS


class AbstractBackupCredentialORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    master_password = models.CharField(max_length=300, null=True)
    master_password_hint = models.CharField(max_length=128, blank=True, null=True, default="")
    key = models.TextField(null=True)
    public_key = models.TextField(null=True)
    private_key = models.TextField(null=True)
    creation_date = models.FloatField()
    kdf = models.IntegerField(default=0)
    kdf_iterations = models.IntegerField(default=DEFAULT_KDF_ITERATIONS)
    # Passwordless config
    fd_credential_id = models.CharField(max_length=255, null=True)
    fd_random = models.CharField(max_length=128, null=True)

    user = models.ForeignKey(locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE,
                             related_name="user_backup_credentials")

    class Meta:
        abstract = True

    @classmethod
    def create(cls, device, **data):
        raise NotImplementedError

    def check_master_password(self, raw_password):
        # The account is not activated
        if not self.master_password:
            return False
        return check_password(raw_password, self.master_password)
