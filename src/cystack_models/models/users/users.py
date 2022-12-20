import ast
import uuid
import requests

from django.conf import settings
from django.db import models
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import check_password, is_password_usable, make_password

from shared.constants.account import DEFAULT_KDF_ITERATIONS, LOGIN_METHOD_PASSWORD, LOGIN_METHOD_PASSWORDLESS, \
    DEFAULT_ONBOARDING_PROCESS
from shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from shared.constants.policy import POLICY_TYPE_PASSWORDLESS
from shared.external_request.requester import requester, RequesterError


class User(models.Model):
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
    timeout = models.IntegerField(default=15)
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

    # On boarding process
    onboarding_process = models.TextField(max_length=512, blank=True, default=DEFAULT_ONBOARDING_PROCESS)

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
            self.save(update_fields=["master_password"])
        return check_password(raw_password, self.master_password, setter)

    @classmethod
    def search_from_cystack_id(cls, **filter_params):
        q_param = filter_params.get("q")
        utm_source_param = filter_params.get("utm_source")
        headers = {'Authorization': settings.MICRO_SERVICE_USER_AUTH}
        url = "{}/micro_services/users?".format(settings.GATEWAY_API)
        if q_param:
            url += "&q={}".format(q_param)
        if utm_source_param:
            url += "&utm_source={}".format(utm_source_param)
        try:
            res = requester(method="GET", url=url, headers=headers)
        except RequesterError:
            return {}
        if res.status_code == 200:
            return res.json()
        return {}

    def get_from_cystack_id(self):
        """
        Request to API Gateway to get user information
        :return:
        """
        url = "{}/micro_services/users/{}".format(settings.GATEWAY_API, self.user_id)
        headers = {'Authorization': settings.MICRO_SERVICE_USER_AUTH}
        res = requester(method="GET", url=url, headers=headers)
        if res.status_code == 200:
            return res.json()
        return {}

    def is_active_enterprise_member(self):
        return self.enterprise_members.filter(
            status=E_MEMBER_STATUS_CONFIRMED, is_activated=True, enterprise__locked=False
        ).exists()

    @property
    def require_passwordless(self):
        return self.login_method == LOGIN_METHOD_PASSWORDLESS or self.enterprise_require_passwordless

    @property
    def enterprise_require_passwordless(self):
        e_member = self.enterprise_members.filter(status=E_MEMBER_STATUS_CONFIRMED, enterprise__locked=False).first()
        e_passwordless_policy = False
        if e_member:
            enterprise = e_member.enterprise
            policy = enterprise.policies.filter(policy_type=POLICY_TYPE_PASSWORDLESS, enabled=True).first()
            if policy:
                e_passwordless_policy = policy.policy_passwordless.only_allow_passwordless
        return e_passwordless_policy

    def get_onboarding_process(self):
        if not self.onboarding_process:
            return DEFAULT_ONBOARDING_PROCESS
        return ast.literal_eval(str(self.onboarding_process))
