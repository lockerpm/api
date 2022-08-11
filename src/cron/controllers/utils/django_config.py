import os
import dotenv
from pathlib import Path
import django
import traceback

from cron.controllers.utils.logger import logger


def django_config():
    try:
        valid_env = ['prod', 'env', 'staging']
        env = os.getenv("PROD_ENV")
        if env not in valid_env:
            env = 'prod'
        if env == "dev":
            dotenv.read_dotenv(os.path.join(Path(__file__).resolve().parent.parent.parent.parent, '.env'))
        setting = "server_config.settings.%s" % env
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", setting)

        django.setup()
    except:
        tb = traceback.format_exc()
        logger.error(tb)
