import django.db.backends.utils
from django.db import OperationalError
import time

import logging.config

original = django.db.backends.utils.CursorWrapper.execute


def execute_wrapper(*args, **kwargs):
    attempts = 0
    while attempts < 3:
        try:
            return original(*args, **kwargs)
        except OperationalError as e:
            code = e.args[0]
            if attempts == 2 or code != 1213:
                raise e
            attempts += 1

            from locker_server.shared.log.config import logging_config

            logging.config.dictConfig(logging_config)
            logger = logging.getLogger('slack_service')
            logger.warning("[DATABASE] Deadlock found, try restart query")
            time.sleep(0.2)


django.db.backends.utils.CursorWrapper.execute = execute_wrapper
