import traceback
import os
import stripe
import logging.config
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


try:
    MICRO_SERVICE_SCOPE = "pwdmanager"

    SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
    DEBUG = True
    ALLOWED_HOSTS = ["*"]
    WSGI_APPLICATION = 'server_config.wsgi.application'

    # Scope apps
    SCOPE_PWD_MANAGER = "pwdmanager"
    # Web url
    LOCKER_WEB_URL = "https://demo.cystack.net:3011"
    # Gateway api
    GATEWAY_API = "http://127.0.0.1:8000"
    MICRO_SERVICE_USER_AUTH = os.getenv("MICRO_SERVICE_USER_AUTH")

    # Test enterprise domain
    TEST_DOMAINS = ["dev.cystack.org"]

    # Cache DB
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv("CACHE_REDIS_LOCATION"),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                # 'SOCKET_CONNECT_TIMEOUT': 360,
                # 'SOCKET_TIMEOUT': 360,
                'IGNORE_EXCEPTIONS': True
            }
        }
    }
    DJANGO_REDIS_IGNORE_EXCEPTIONS = True

    # Database
    DATABASES = {
        'default': {
            'ENGINE': "django.db.backends.mysql",
            'NAME':  os.getenv("MYSQL_DATABASE"),
            'USER':  os.getenv("MYSQL_USERNAME"),
            'PASSWORD': os.getenv("MYSQL_PASSWORD"),
            'HOST': os.getenv("MYSQL_HOST"),
            'PORT':  os.getenv("MYSQL_PORT"),
            'CONN_MAX_AGE': 120,
            'OPTIONS': {
                'init_command': "ALTER DATABASE `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; "
                                "SET block_encryption_mode = 'aes-256-cbc'" % (os.getenv("MYSQL_DATABASE")),
                'charset': 'utf8mb4',  # <--- Use this
                'isolation_level': 'read committed'
            }
        },
        # 'locker_tenant_3xu9cp': {
        #     'ENGINE': "django.db.backends.mysql",
        #     'NAME': os.getenv("MYSQL_DATABASE_TENANT"),
        #     'USER': os.getenv("MYSQL_USERNAME_TENANT"),
        #     'PASSWORD': os.getenv("MYSQL_PASSWORD_TENANT"),
        #     'HOST': os.getenv("MYSQL_HOST_TENANT"),
        #     'PORT': os.getenv("MYSQL_PORT_TENANT"),
        #     'CONN_MAX_AGE': 120,
        #     'OPTIONS': {
        #         'init_command': "ALTER DATABASE `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; "
        #                         "SET block_encryption_mode = 'aes-256-cbc'" % (os.getenv("MYSQL_DATABASE_TENANT")),
        #         'charset': 'utf8mb4',  # <--- Use this
        #         'isolation_level': 'read committed'
        #     }
        # },
        'locker_statistics_db': {
            'ENGINE': "django.db.backends.mysql",
            'NAME': os.getenv("MYSQL_STATISTIC_DATABASE"),
            'USER': os.getenv("MYSQL_STATISTIC_USERNAME"),
            'PASSWORD': os.getenv("MYSQL_STATISTIC_PASSWORD"),
            'HOST': os.getenv("MYSQL_STATISTIC_HOST"),
            'PORT': os.getenv("MYSQL_STATISTIC_PORT"),
            'CONN_MAX_AGE': 120,
            'OPTIONS': {
                'init_command': "ALTER DATABASE `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; "
                                "SET block_encryption_mode = 'aes-256-cbc'" % (os.getenv("MYSQL_STATISTIC_DATABASE")),
                'charset': 'utf8mb4',  # <--- Use this
                'isolation_level': 'read committed'
            }
        }
    }
    DATABASE_ROUTERS = [
        "shared.db_router.locker_statistics_db_router.LockerStatisticsDBRouter",
        # "shared.db_router.tenant_db_router.TenantDBRouter",
    ]

    # Auto field configuration
    DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

    # -------------- 3rd Lib ------------------------ #
    # Token auth slack (Logging)
    SLACK_WEBHOOK_API_LOG = os.getenv("SLACK_WEBHOOK_API_LOG")
    SLACK_WEBHOOK_CRON_LOG = os.getenv("SLACK_WEBHOOK_CRON_LOG")
    SLACK_WEBHOOK_NEW_USERS = os.getenv("SLACK_WEBHOOK_NEW_USERS")

    # Google sheet
    GOOGLE_SHEET_FEEDBACK_URL = os.getenv("GOOGLE_SHEET_FEEDBACK_URL")
    GOOGLE_SHEET_FEEDBACK_SERVICE_ACCOUNT = os.getenv("GOOGLE_SHEET_FEEDBACK_SERVICE_ACCOUNT")

    # Token haveIBeenPwned
    HIBP_API_KEY = os.getenv("HIBP_API_KEY")

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    stripe.api_key = STRIPE_SECRET_KEY

    # Fcm
    FCM_CRED_SERVICE_ACCOUNT = os.getenv("FCM_CRED_SERVICE_ACCOUNT")

    # Relay RabbitMQ
    RELAY_QUEUE = os.getenv("RELAY_QUEUE")
    RELAY_QUEUE_URL = os.getenv("RELAY_QUEUE_URL")
    MAIL_WEBHOOK_TOKEN = os.getenv("MAIL_WEBHOOK_TOKEN")

    # Management command
    MANAGEMENT_COMMAND_TOKEN = os.getenv("MANAGEMENT_COMMAND_TOKEN")

    # CloudFlare access
    CF_ACCESS_CLIENT_ID = os.getenv("CF_ACCESS_CLIENT_ID")
    CF_ACCESS_CLIENT_SECRET = os.getenv("CF_ACCESS_CLIENT_SECRET")

    # AWS SQS
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_SQS_REGION_NAME = os.getenv("AWS_SQS_REGION_NAME")
    AWS_SQS_URL = os.getenv("AWS_SQS_URL")

    # AWS S3
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
    AWS_S3_ACCESS_KEY = os.getenv("AWS_S3_ACCESS_KEY")
    AWS_S3_SECRET_KEY = os.getenv("AWS_S3_SECRET_KEY")

    # Application definition
    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.staticfiles',
        'corsheaders',
        'rest_framework',
        'django_rq',
        'cystack_models',
        'v1_0',
        'micro_services',
        'relay',
        'locker_statistic',
        # 'api',
    ]

    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.AllowAllUsersModelBackend'
    ]

    # Middleware
    MIDDLEWARE = [
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'corsheaders.middleware.CorsPostCsrfMiddleware',
        # 'shared.middlewares.tenant_db_middleware.TenantDBMiddleware',
        'shared.middlewares.error_response_middleware.ErrorResponseMiddleware',
        'shared.middlewares.queries_debug_middleware.QueriesDebugMiddleware',
    ]

    ROOT_URLCONF = 'server_config.urls'

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'shared.authentications.locker_auth.LockerTokenAuthentication'
        ],
        'DEFAULT_PERMISSION_CLASSES': (
            'shared.permissions.app.AppBasePermission',
        ),
        'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
        'EXCEPTION_HANDLER': 'shared.exception_handler.custom_exception_handler',
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 10,
        # 'DEFAULT_THROTTLE_CLASSES': (
        #     'api.throttling.user_throttle.UserThrottle'
        # ),
        # 'DEFAULT_THROTTLE_RATES': {
        #     'anonymous': '60/min',
        #     'user_authenticated': '600/min',
        # }
    }

    # Redis queue
    RQ_QUEUES = {
        'default': {
            'USE_REDIS_CACHE': 'default',
        },
    }

    # CORS Config
    CORS_ORIGIN_ALLOW_ALL = False
    CORS_ORIGIN_REGEX_WHITELIST = [
        r"^https://\w+\.cystack\.com$",
        r"^https://\w+\.cystack\.net$",
        r"^https://\w+\.cystack\.org$",
        r"^https://demo\.cystack\.net:\d+$",
        r"^http://\w+\.platform\.cystack\.com$",
        r"^http://\w+\.platform\.cystack\.net$",
        r"^http://\w+\.platform\.cystack\.org$",
        r"http://\w+\.staging\.cystack\.org$"
    ]
    CORS_ALLOW_CREDENTIALS = True
    CORS_EXPOSE_HEADERS = (
        'location',
        'Location',
        'device-id',
        'Device-Id',
        'device-expired-time',
        'Device-Expired-Time'
    )
    CORS_ALLOW_HEADERS = (
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
        'device-id',
        'device-expired-time',
        'locker-client-agent',
        'locker-client-ip',
        'locker-client-device-id'
    )
    CORS_ALLOW_METHODS = (
        'GET',
        'POST',
        'PUT',
        'DELETE',
        'OPTIONS'
    )

    # Internationalization
    LANGUAGE_CODE = 'en-us'
    TIME_ZONE = 'UTC'
    USE_I18N = True
    USE_L10N = True
    USE_TZ = True

    # Static files (CSS, JavaScript, Images)
    STATIC_URL = '/static/'

except Exception as e:
    from shared.log.config import logging_config
    logging.config.dictConfig(logging_config)
    logger = logging.getLogger('slack_service')
    tb = traceback.format_exc()
    logger.critical(tb)
