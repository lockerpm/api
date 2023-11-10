import ast
import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from locker_server.shared.constants.account import *


class AbstractUserORM(models.Model):
    user_id = models.IntegerField(primary_key=True)
    internal_id = models.CharField(max_length=64, null=True, default=uuid.uuid4)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    first_login = models.FloatField(null=True)
    activated = models.BooleanField(default=False)
    activated_date = models.FloatField(null=True)
    delete_account_date = models.FloatField(null=True)
    account_revision_date = models.FloatField(null=True)
    master_password = models.CharField(max_length=300, null=True)
    master_password_hint = models.CharField(max_length=128, blank=True, null=True, default="")
    master_password_score = models.FloatField(default=0)
    security_stamp = models.CharField(max_length=50, null=True)
    key = models.TextField(null=True)
    public_key = models.TextField(null=True)
    private_key = models.TextField(null=True)
    kdf = models.IntegerField(default=0)
    kdf_iterations = models.IntegerField(default=DEFAULT_KDF_ITERATIONS)
    api_key = models.CharField(max_length=32, null=True)
    timeout = models.IntegerField(default=20160)
    timeout_action = models.CharField(default="lock", max_length=16)
    is_leaked = models.BooleanField(default=False)
    use_relay_subdomain = models.BooleanField(default=False)

    # Login policy
    last_request_login = models.FloatField(null=True, default=None)
    login_failed_attempts = models.IntegerField(default=0)
    login_block_until = models.FloatField(null=True, default=None)

    # Passwordless config
    login_method = models.CharField(max_length=32, default=LOGIN_METHOD_PASSWORD)
    fd_credential_id = models.CharField(max_length=255, null=True)
    fd_random = models.CharField(max_length=128, null=True)

    # Onboarding process
    onboarding_process = models.TextField(max_length=512, blank=True, default=DEFAULT_ONBOARDING_PROCESS)
    saas_source = models.CharField(max_length=32, null=True, default=None)

    # Stores the raw password if set_password() is called so that it can
    # be passed to password_changed() after the model is saved.
    _password = None

    class Meta:
        abstract = True

    @classmethod
    def retrieve_or_create(cls, **kwargs):
        raise NotImplementedError

    def get_from_cystack_id(self):
        raise NotImplementedError

    def set_master_password(self, raw_password):
        self.master_password = make_password(raw_password)
        self._password = raw_password

    def check_master_password(self, raw_password):
        """
        Return a bool of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw):
            self.set_master_password(raw)
            # Password hash upgrades shouldn't be considered password changes.
            self._password = None
            self.save(update_fields=["master_password"])
        # The account is not activated
        if not self.master_password:
            return False
        return check_password(raw_password, self.master_password, setter)

    def get_onboarding_process(self):
        if not self.onboarding_process:
            return DEFAULT_ONBOARDING_PROCESS
        return ast.literal_eval(str(self.onboarding_process))

