from server_config.settings.dev import *


DEBUG = False
ALLOWED_HOSTS = []


# Cache DB
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv("CACHE_REDIS_STAGING_LOCATION"),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True
        }
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


# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_STAGING_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY


# Redis queue
RQ_QUEUES = {
    'default': {
        'USE_REDIS_CACHE': 'default',
    },
}
