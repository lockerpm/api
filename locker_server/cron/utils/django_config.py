import os
import dotenv
import traceback
from pathlib import Path

import django

from locker_server.cron.utils.logger import logger
from locker_server.shared.middlewares.tenant_db_middleware import set_current_db_name


def django_config(env_file_path: str = ''):
    try:
        if not env_file_path:
            env_file_path = os.path.join(Path(__file__).resolve().parent.parent.parent.parent, '.env')
        dotenv.read_dotenv(env_file_path)
        valid_env = ['prod', 'env', 'staging']
        env = os.getenv("PROD_ENV")
        if env not in valid_env:
            env = 'dev'
        setting = "server_config.settings.%s" % env
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", setting)
        django.setup()
    except:
        tb = traceback.format_exc()
        logger.error(tb)
