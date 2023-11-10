"""
ASGI config for server_config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

import django
from channels.routing import get_default_application


valid_env = ['prod', 'env', 'staging']
env = os.getenv("ENVIRONMENT")
env = 'dev' if env not in valid_env else env

setting = "server_config.settings.%s" % env
os.environ.setdefault("DJANGO_SETTINGS_MODULE", setting)
django.setup()

application = get_default_application()
