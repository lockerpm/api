from server_config.settings.dev import *


DEBUG = False
ALLOWED_HOSTS = ["locker-api.staging.cystack.org", "staging-api.locker.io", "cystack-locker-api.locker-staging"]


DATABASES = {
    'default': {
        'ENGINE': "django.db.backends.mysql",
        'NAME': os.getenv("MYSQL_STAGING_DATABASE"),
        'USER': os.getenv("MYSQL_STAGING_USERNAME"),
        'PASSWORD': os.getenv("MYSQL_STAGING_PASSWORD"),
        'HOST': os.getenv("MYSQL_STAGING_HOST"),
        'PORT': os.getenv("MYSQL_STAGING_PORT"),
        'CONN_MAX_AGE': 120,
        'OPTIONS': {
            'init_command': "ALTER DATABASE `%s` CHARACTER SET utf8; "
                            "SET block_encryption_mode = 'aes-256-cbc'" % (os.getenv("MYSQL_STAGING_DATABASE")),
            'charset': 'utf8',  # <--- Use this
            'isolation_level': 'read committed'
        }
    },
}


LOCKER_WEB_URL = "https://staging.locker.io"

GATEWAY_API = "https://api.cystack.org"
MICRO_SERVICE_USER_AUTH = os.getenv("MICRO_SERVICE_USER_AUTH")


# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_STAGING_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY
