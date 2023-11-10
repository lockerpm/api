"""
This module is largely inspired by django-rest-framework settings

Settings for the LockerServer are all namespaced in the LOCKER_SERVER_SETTINGS setting.
For example your project's `settings.py` file might look like this:

LOCKER_SERVER_SETTINGS = {

}

"""
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from django.test.signals import setting_changed

USER_SETTINGS = getattr(settings, "LOCKER_SERVER_SETTINGS", None)

LS_RELEASE_MODEL = getattr(settings, "LS_RELEASE_MODEL", "api_orm.ReleaseORM")

# --------- User Models -------------- #
LS_USER_MODEL = getattr(settings, "LS_USER_MODEL", "api_orm.UserORM")
LS_DEVICE_MODEL = getattr(settings, "LS_DEVICE_MODEL", "api_orm.DeviceORM")
LS_DEVICE_ACCESS_TOKEN_MODEL = getattr(settings, "LS_DEVICE_ACCESS_TOKEN_MODEL", "api_orm.DeviceAccessTokenORM")
LS_BACKUP_CREDENTIAL_MODEL = getattr(settings, "LS_BACKUP_CREDENTIAL_MODEL", "api_orm.BackupCredentialORM")

# ---------- Plan Type - Payment Models ---------- #
LS_PLAN_TYPE_MODEL = getattr(settings, "LS_PLAN_TYPE_MODEL", "api_orm.PlanTypeORM")
LS_PLAN_MODEL = getattr(settings, "LS_PLAN_MODEL", "api_orm.PMPlanORM")
LS_PROMO_CODE_TYPE_MODEL = getattr(settings, "LS_PROMO_CODE_TYPE_MODEL", "api_orm.PromoCodeTypeORM")
LS_PROMO_CODE_MODEL = getattr(settings, "LS_PROMO_CODE_MODEL", "api_orm.PromoCodeORM")
LS_PAYMENT_MODEL = getattr(settings, "LS_PAYMENT_MODEL", "api_orm.PaymentORM")
LS_USER_PLAN_MODEL = getattr(settings, "LS_USER_PLAN_MODEL", "api_orm.PMUserPlanORM")

# -------- Notification Models ------- #
LS_NOTIFICATION_CATEGORY_MODEL = getattr(settings, "LS_NOTIFICATION_CATEGORY_MODEL", "api_orm.NotificationCategoryORM")
LS_NOTIFICATION_SETTING_MODEL = getattr(settings, "LS_NOTIFICATION_SETTING_MODEL", "api_orm.NotificationSettingORM")
LS_NOTIFICATION_MODEL = getattr(settings, "LS_NOTIFICATION_MODEL", "api_orm.NotificationORM")
# -------- Emergency Access Models ------ #
LS_EMERGENCY_ACCESS_MODEL = getattr(settings, "LS_EMERGENCY_ACCESS_MODEL", "api_orm.EmergencyAccessORM")

# --------- Event Models ----------- #
LS_EVENT_MODEL = getattr(settings, "LS_EVENT_MODEL", "api_orm.EventORM")

# -------- Reward Models ----------- #
LS_MISSION_MODEL = getattr(settings, "LS_MISSION_MODEL", "api_orm.MissionORM")
LS_USER_REWARD_MISSION_MODEL = getattr(settings, "LS_USER_REWARD_MISSION_MODEL", "api_orm.UserRewardMissionORM")

# -------- Relay Models ------------ #
LS_RELAY_REPLY_MODEL = getattr(settings, "LS_RELAY_REPLY_MODEL", "api_orm.ReplyORM")
LS_RELAY_DOMAIN_MODEL = getattr(settings, "LS_RELAY_DOMAIN_MODEL", "api_orm.RelayDomainORM")
LS_RELAY_SUBDOMAIN_MODEL = getattr(settings, "LS_RELAY_SUBDOMAIN_MODEL", "api_orm.RelaySubdomainORM")
LS_RELAY_DELETED_ADDRESS_MODEL = getattr(settings, "LS_RELAY_DELETED_ADDRESS_MODEL", "api_orm.DeletedRelayAddressORM")
LS_RELAY_ADDRESS_MODEL = getattr(settings, "LS_RELAY_ADDRESS_MODEL", "api_orm.RelayAddressORM")

# -------- Vault Models ------------- #
LS_TEAM_MODEL = getattr(settings, "LS_TEAM_MODEL", "api_orm.TeamORM")
LS_CIPHER_MODEL = getattr(settings, "LS_CIPHER_MODEL", "api_orm.CipherORM")
LS_FOLDER_MODEL = getattr(settings, "LS_FOLDER_MODEL", "api_orm.FolderORM")
LS_MEMBER_ROLE_MODEL = getattr(settings, "LS_MEMBER_ROLE_MODEL", "api_orm.MemberRoleORM")
LS_TEAM_MEMBER_MODEL = getattr(settings, "LS_TEAM_MEMBER_MODEL", "api_orm.TeamMemberORM")
LS_COLLECTION_MODEL = getattr(settings, "LS_COLLECTION_MODEL", "api_orm.CollectionORM")
LS_COLLECTION_CIPHER_MODEL = getattr(settings, "LS_COLLECTION_CIPHER_MODEL", "api_orm.CollectionCipherORM")
LS_COLLECTION_MEMBER_MODEL = getattr(settings, "LS_COLLECTION_MEMBER_MODEL", "api_orm.CollectionMemberORM")
LS_GROUP_MODEL = getattr(settings, "LS_GROUP_MODEL", "api_orm.GroupORM")
LS_GROUP_MEMBER_MODEL = getattr(settings, "LS_GROUP_MEMBER_MODEL", "api_orm.GroupMemberORM")

# ------- Enterprise Models --------- #
LS_ENTERPRISE_MODEL = getattr(settings, "LS_ENTERPRISE_MODEL", "api_orm.EnterpriseORM")
LS_ENTERPRISE_DOMAIN_MODEL = getattr(settings, "LS_ENTERPRISE_DOMAIN_MODEL", "api_orm.DomainORM")
LS_ENTERPRISE_MEMBER_ROLE_MODEL = getattr(
    settings, "LS_ENTERPRISE_MEMBER_ROLE_MODEL", "api_orm.EnterpriseMemberRoleORM"
)
LS_ENTERPRISE_MEMBER_MODEL = getattr(settings, "LS_ENTERPRISE_MEMBER_MODEL", "api_orm.EnterpriseMemberORM")
LS_ENTERPRISE_GROUP_MODEL = getattr(settings, "LS_ENTERPRISE_GROUP_MODEL", "api_orm.EnterpriseGroupORM")
LS_ENTERPRISE_GROUP_MEMBER_MODEL = getattr(
    settings, "LS_ENTERPRISE_GROUP_MEMBER_MODEL", "api_orm.EnterpriseGroupMemberORM"
)
LS_ENTERPRISE_POLICY_MODEL = getattr(settings, "LS_ENTERPRISE_POLICY_MODEL", "api_orm.EnterprisePolicyORM")

# ------- Quick Share Models --------- #
LS_QUICK_SHARE_MODEL = getattr(settings, "LS_QUICK_SHARE_MODEL", "api_orm.QuickShareORM")
LS_QUICK_SHARE_EMAIL_MODEL = getattr(settings, "LS_QUICK_SHARE_EMAIL_MODEL", "api_orm.QuickShareEmailORM")

# ------- Affiliate Models ---------- #
LS_AFFILIATE_SUBMISSION_MODEL = getattr(settings, "LS_AFFILIATE_SUBMISSION_MODEL", "api_orm.AffiliateSubmissionORM")

# -------- Factor2 Models ----------- #
LS_FACTOR2_METHOD_MODEL = getattr(settings, "LS_FACTOR2_METHOD_MODEL", "api_orm.Factor2MethodORM")

# -------- Configuration Models ----------- #
LS_SSO_CONFIGURATION_MODEL = getattr(settings, "LS_SSO_CONFIGURATION_MODEL", "api_orm.SSOConfigurationORM")

DEFAULT_PLAN = getattr(settings, "DEFAULT_PLAN", "pm_free")
DEFAULT_PLAN_TIME = getattr(settings, "DEFAULT_PLAN_TIME", 3 * 365 * 86400)

DEFAULTS = {
    "LS_RELEASE_MODEL": LS_RELEASE_MODEL,

    "LS_USER_MODEL": LS_USER_MODEL,
    "LS_DEVICE_MODEL": LS_DEVICE_MODEL,
    "LS_DEVICE_ACCESS_TOKEN_MODEL": LS_DEVICE_ACCESS_TOKEN_MODEL,
    "LS_BACKUP_CREDENTIAL_MODEL": LS_BACKUP_CREDENTIAL_MODEL,

    "LS_PLAN_TYPE_MODEL": LS_PLAN_TYPE_MODEL,
    "LS_PLAN_MODEL": LS_PLAN_MODEL,
    "LS_PROMO_CODE_TYPE_MODEL": LS_PROMO_CODE_TYPE_MODEL,
    "LS_PROMO_CODE_MODEL": LS_PROMO_CODE_MODEL,
    "LS_PAYMENT_MODEL": LS_PAYMENT_MODEL,
    "LS_USER_PLAN_MODEL": LS_USER_PLAN_MODEL,

    "LS_NOTIFICATION_CATEGORY_MODEL": LS_NOTIFICATION_CATEGORY_MODEL,
    'LS_NOTIFICATION_SETTING_MODEL': LS_NOTIFICATION_SETTING_MODEL,
    'LS_NOTIFICATION_MODEL': LS_NOTIFICATION_MODEL,

    "LS_EMERGENCY_ACCESS_MODEL": LS_EMERGENCY_ACCESS_MODEL,

    "LS_EVENT_MODEL": LS_EVENT_MODEL,

    "LS_MISSION_MODEL": LS_MISSION_MODEL,
    "LS_USER_REWARD_MISSION_MODEL": LS_USER_REWARD_MISSION_MODEL,

    "LS_RELAY_REPLY_MODEL": LS_RELAY_REPLY_MODEL,
    "LS_RELAY_DOMAIN_MODEL": LS_RELAY_DOMAIN_MODEL,
    "LS_RELAY_SUBDOMAIN_MODEL": LS_RELAY_SUBDOMAIN_MODEL,
    "LS_RELAY_DELETED_ADDRESS_MODEL": LS_RELAY_DELETED_ADDRESS_MODEL,
    "LS_RELAY_ADDRESS_MODEL": LS_RELAY_ADDRESS_MODEL,

    "LS_TEAM_MODEL": LS_TEAM_MODEL,
    "LS_CIPHER_MODEL": LS_CIPHER_MODEL,
    "LS_FOLDER_MODEL": LS_FOLDER_MODEL,
    "LS_MEMBER_ROLE_MODEL": LS_MEMBER_ROLE_MODEL,
    "LS_TEAM_MEMBER_MODEL": LS_TEAM_MEMBER_MODEL,
    "LS_COLLECTION_MODEL": LS_COLLECTION_MODEL,
    "LS_COLLECTION_CIPHER_MODEL": LS_COLLECTION_CIPHER_MODEL,
    "LS_COLLECTION_MEMBER_MODEL": LS_COLLECTION_MEMBER_MODEL,
    "LS_GROUP_MODEL": LS_GROUP_MODEL,
    "LS_GROUP_MEMBER_MODEL": LS_GROUP_MEMBER_MODEL,

    "LS_ENTERPRISE_MODEL": LS_ENTERPRISE_MODEL,
    "LS_ENTERPRISE_DOMAIN_MODEL": LS_ENTERPRISE_DOMAIN_MODEL,
    "LS_ENTERPRISE_MEMBER_ROLE_MODEL": LS_ENTERPRISE_MEMBER_ROLE_MODEL,
    "LS_ENTERPRISE_MEMBER_MODEL": LS_ENTERPRISE_MEMBER_MODEL,
    "LS_ENTERPRISE_GROUP_MODEL": LS_ENTERPRISE_GROUP_MODEL,
    "LS_ENTERPRISE_GROUP_MEMBER_MODEL": LS_ENTERPRISE_GROUP_MEMBER_MODEL,
    "LS_ENTERPRISE_POLICY_MODEL": LS_ENTERPRISE_POLICY_MODEL,

    "LS_QUICK_SHARE_MODEL": LS_QUICK_SHARE_MODEL,
    "LS_QUICK_SHARE_EMAIL_MODEL": LS_QUICK_SHARE_EMAIL_MODEL,

    "LS_AFFILIATE_SUBMISSION_MODEL": LS_AFFILIATE_SUBMISSION_MODEL,

    "LS_FACTOR2_METHOD_MODEL": LS_FACTOR2_METHOD_MODEL,

    "LS_SSO_CONFIGURATION_MODEL": LS_SSO_CONFIGURATION_MODEL,

    "API_REPOSITORY_CLASS": "locker_server.containers.defaults.repository.RepositoryFactory",
    "API_SERVICE_CLASS": "locker_server.containers.defaults.service.ServiceFactory",
    "MODEL_PARSER_CLASS": "locker_server.api_orm.model_parsers.model_parsers.ModelParser",

    "GEOIP_PATH": os.path.join(settings.BASE_DIR, 'locker_server', 'shared', 'geoip2'),
    "MAXMIND_API_KEY": None,
    "INIT_MAXMIND_DB": "1",
    "DEFAULT_PLAN": DEFAULT_PLAN,
    "DEFAULT_PLAN_TIME": DEFAULT_PLAN_TIME,
}

# List of settings that cannot be empty
MANDATORY = (

)

# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    "API_REPOSITORY_CLASS",
    "API_SERVICE_CLASS",
    "MODEL_PARSER_CLASS",
)


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, str):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        msg = "Could not import %r for setting %r. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class LockerServerSettings:
    def __init__(self, user_settings=None, defaults=None, import_strings=None, mandatory=None):
        self._user_settings = user_settings or {}
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self.mandatory = mandatory or ()
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "LOCKER_SERVER_SETTINGS", {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid LockerServer setting: %s" % attr)
        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if val and attr in self.import_strings:
            val = perform_import(val, attr)

        # Overriding special settings
        if attr == "_SCOPES":
            val = list(self.SCOPES.keys())
        if attr == "_DEFAULT_SCOPES":
            if "__all__" in self.DEFAULT_SCOPES:
                # If DEFAULT_SCOPES is set to ["__all__"] the whole set of scopes is returned
                val = list(self._SCOPES)
            else:
                # Otherwise we return a subset (that can be void) of SCOPES
                val = []
                for scope in self.DEFAULT_SCOPES:
                    if scope in self._SCOPES:
                        val.append(scope)
                    else:
                        raise ImproperlyConfigured("Defined DEFAULT_SCOPES not present in SCOPES")

        self.validate_setting(attr, val)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def validate_setting(self, attr, val):
        if not val and attr in self.mandatory:
            raise AttributeError("LockerServer setting: %s is mandatory" % attr)

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


locker_server_settings = LockerServerSettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS, MANDATORY)


def reload_locker_server_settings(*args, **kwargs):
    setting = kwargs["setting"]
    if setting == "LOCKER_SERVER_SETTINGS":
        locker_server_settings.reload()


setting_changed.connect(reload_locker_server_settings)
