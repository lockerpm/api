from server_config.settings.dev import *


DEBUG = False
if not SERVER_ORIGIN:
    ALLOWED_HOSTS = [
        "localhost", "127.0.0.1"
    ]
else:
    ALLOWED_HOSTS = [
        SERVER_ORIGIN
    ]


# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsPostCsrfMiddleware',
    'locker_server.shared.middlewares.error_response_middleware.ErrorResponseMiddleware',
]


# --------------- 3rd Lib ----------------------- #
# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY


# --------------- CORS Settings ----------------------- #
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = []
web_origins = WEB_ORIGIN.split(',')
for web_origin in web_origins:
    web_origin = web_origin.strip()
    CORS_ALLOWED_ORIGINS += [
        f"http://{web_origin}",
        f"https://{web_origin}",
    ]

if DEV_WEB_ORIGIN:
    dev_web_origins = DEV_WEB_ORIGIN.split(',')
    for dev_web_origin in dev_web_origins:
        dev_web_origin = dev_web_origin.strip()
        CORS_ALLOWED_ORIGINS += [
            f"http://{dev_web_origin}",
            f"https://{dev_web_origin}",
        ]
