import logging
import logging.config
import time
import traceback

import django.db.backends.utils
from django.db import OperationalError, connection

original = django.db.backends.utils.CursorWrapper.execute


def execute_wrapper(*args, **kwargs):
    attempts = 0
    while attempts < 3:
        try:
            return original(*args, **kwargs)
        except OperationalError as e:
            code = e.args[0]
            if code != 1213:
                raise e

            tb = traceback.format_exc()
            logger = logging.getLogger('slack_service')
            logger.info("[Locker] DETECTED DEADLOCK: {}".format(e))

            # cursor = connection.cursor()
            # raw_sql = "SHOW ENGINE INNODB STATUS;"
            # cursor.execute(raw_sql)
            # row = cursor.fetchone()
            # log_val = row
            # logger.info("[INNO Locker]: {}".format(log_val))

            if attempts == 2:
                logger.error(tb)
                raise e
            attempts += 1
            time.sleep(0.5)

    # try:
    #     return original(*args, **kwargs)
    # except OperationalError as e:
    #     code = e.args[0]
    #     if code == 1213:
    #         tb = traceback.format_exc()
    #         logger = logging.getLogger('slack_service')
    #         logger.info("DETECTED DEADLOCK: {}".format(tb))
    #     raise e


django.db.backends.utils.CursorWrapper.execute = execute_wrapper
