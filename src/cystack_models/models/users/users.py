import uuid

from django.db import models
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import check_password, is_password_usable, make_password

from shared.constants.account import DEFAULT_KDF_ITERATIONS


class User(models.Model):
    user_id = models.IntegerField(primary_key=True)
    internal_id = models.CharField(max_length=64, null=True, default=uuid.uuid4)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    activated = models.BooleanField(default=False)
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
    timeout = models.IntegerField(default=15)
    timeout_action = models.CharField(default="lock", max_length=16)

    # Stores the raw password if set_password() is called so that it can
    # be passed to password_changed() after the model is saved.
    _password = None

    class Meta:
        db_table = 'cs_users'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self._password is not None:
            password_validation.password_changed(self._password, self)
            self._password = None

    def set_master_password(self, raw_password):
        self.master_password = make_password(raw_password)
        self._password = raw_password

    def check_master_password(self, raw_password):
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw):
            self.set_master_password(raw)
            # Password hash upgrades shouldn't be considered password changes.
            self._password = None
            self.save(update_fields=["password"])
        return check_password(raw_password, self.master_password, setter)
