DEFAULT_KDF_ITERATIONS = 100000

ACCOUNT_TYPE_PERSONAL = "personal"
ACCOUNT_TYPE_ENTERPRISE = "enterprise"


LOGIN_METHOD_PASSWORD = "password"
LOGIN_METHOD_PASSWORDLESS = "passwordless"


# -------------------- Onboarding process --------------------- #
ONBOARDING_CATEGORY_TO_DASHBOARD = "vault_to_dashboard"
ONBOARDING_CATEGORY_ENTERPRISE = "enterprise_onboarding"
ONBOARDING_CATEGORY_ENTERPRISE_SKIP = "enterprise_onboarding_skip"
ONBOARDING_CATEGORY_WELCOME = "welcome"
ONBOARDING_CATEGORY_TUTORIAL = "tutorial"
DEFAULT_ONBOARDING_PROCESS = {
    ONBOARDING_CATEGORY_TO_DASHBOARD: False,
    ONBOARDING_CATEGORY_WELCOME: False,
    ONBOARDING_CATEGORY_TUTORIAL: False,
    ONBOARDING_CATEGORY_ENTERPRISE: [],
    ONBOARDING_CATEGORY_ENTERPRISE_SKIP: False,
}
