import os
import dotenv
import traceback
from pathlib import Path

import django
from cron.utils.logger import logger
from shared.middlewares.tenant_db_middleware import set_current_db_name


def django_config(db_name='default'):
    try:
        valid_env = ['prod', 'env', 'staging']
        env = os.getenv("PROD_ENV")
        if env not in valid_env:
            env = 'dev'
        if env == "dev":
            dotenv.read_dotenv(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))
        setting = "server_config.settings.%s" % env
        # logger.info(f"[+] Start cron by setting {setting}")
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", setting)

        set_current_db_name(db_name)
        django.setup()
    except:
        tb = traceback.format_exc()
        logger.error(tb)
