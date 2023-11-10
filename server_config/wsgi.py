"""
WSGI config for server_config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application


valid_env = ['prod', 'env', 'staging']
env = os.getenv("PROD_ENV")
if env not in valid_env:
    env = 'dev'


setting = "server_config.settings.%s" % env
os.environ.setdefault('DJANGO_SETTINGS_MODULE', setting)
application = get_wsgi_application()
