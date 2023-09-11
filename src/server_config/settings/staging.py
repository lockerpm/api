from server_config.settings.dev import *


DEBUG = False
ALLOWED_HOSTS = ["locker-api.staging.cystack.org", "staging-api.locker.io", "cystack-locker-api.locker-staging"]


# Cache DB
CACHE_REDIS_LOCATION = os.getenv("CACHE_REDIS_STAGING_LOCATION")
CACHE_OPTIONS = {
    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    'IGNORE_EXCEPTIONS': True
}
if CACHE_REDIS_LOCATION and CACHE_REDIS_LOCATION.startswith("rediss://"):
    CACHE_OPTIONS.update({
        'CONNECTION_POOL_KWARGS': {'ssl_cert_reqs': None},
    })
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': CACHE_REDIS_LOCATION,
        'OPTIONS': CACHE_OPTIONS
    }
}

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
            'init_command': "ALTER DATABASE `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; "
                            "SET block_encryption_mode = 'aes-256-cbc'" % (os.getenv("MYSQL_STAGING_DATABASE")),
            'charset': 'utf8mb4',  # <--- Use this
            'isolation_level': 'read committed'
        }
    },
}
DATABASE_ROUTERS = []


LOCKER_WEB_URL = "https://staging.locker.io"
LOCKER_ID_WEB_URL = os.getenv("LOCKER_ID_WEB_URL", "https://id-staging.locker.io")

GATEWAY_API = "https://api.cystack.org"
MICRO_SERVICE_USER_AUTH = os.getenv("MICRO_SERVICE_USER_AUTH")


# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_STAGING_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY


# Redis queue
RQ_QUEUES = {
    'default': {
        'USE_REDIS_CACHE': 'default',
    },
}
