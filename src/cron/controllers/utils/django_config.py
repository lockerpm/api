import os
import django
import traceback

from cron.controllers.utils.logger import logger


def django_config():
    try:
        valid_env = ['prod', 'env', 'staging']
        env = os.getenv("PROD_ENV")
        if env not in valid_env:
            env = 'prod'
        setting = "server_config.settings.%s" % env
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", setting)

        django.setup()
    except:
        tb = traceback.format_exc()
        logger.error(tb)
