from server_config.settings.dev import *


DEBUG = False
ALLOWED_HOSTS = ["locker-api.staging.cystack.org", "cystack-locker-api", "api.locker.io", "cystack-locker-api.locker"]

# Web url
LOCKER_WEB_URL = "https://locker.io"

# Gateway API
GATEWAY_API = "https://api.cystack.net"
MICRO_SERVICE_USER_AUTH = os.getenv("MICRO_SERVICE_USER_AUTH")


# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsPostCsrfMiddleware',
    'shared.middlewares.error_response_middleware.ErrorResponseMiddleware',
]


# --------------- 3rd Lib ----------------------- #
# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY
