import logging
import os
import socket
import time
import traceback
import requests

from django.conf import settings


NOTIFY_LEVEL_NUM = 100
if os.getenv("PROD_ENV") == "staging":
    MSG_PREFIX = "[locker-sever-cron-staging]"
else:
    MSG_PREFIX = "[locker-sever-cron]"


class SlackHandler(logging.Handler):
    def emit(self, record):
        try:
            record.exc_info = record.exc_text = None
            content = {'text': self.format(record)}
            requests.post(
                url=settings.SLACK_WEBHOOK_CRON_LOG,
                json={
                    "text": "```{}```".format(content['text'])
                },
                timeout=10
            )
        except:
            print("Slack handler failed")


class Logger:
    @staticmethod
    def __init__():
        format_string = '%(asctime)s {hostname} %(levelname)s %(message)s'.format(**{'hostname': socket.gethostname()})
        format_log = logging.Formatter(format_string)
        format_log.converter = time.gmtime

        logging.basicConfig(level=logging.INFO)
        logging.disable(logging.DEBUG)
        for handler in logging.getLogger().handlers:
            logging.getLogger().removeHandler(handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(format_log)
        logging.getLogger().addHandler(stream_handler)

        slack_handler = SlackHandler()
        slack_handler.setFormatter(format_log)
        logging.getLogger().addHandler(slack_handler)

        logging.addLevelName(NOTIFY_LEVEL_NUM, "NOTIFY")

    @staticmethod
    def info(message):
        msg = "{} {}".format(MSG_PREFIX, message)
        logging.info(msg)

    @staticmethod
    def warning(message):
        msg = "{} {}".format(MSG_PREFIX, message)
        logging.warning(msg)

    @staticmethod
    def notify(message):
        msg = "{} {}".format(MSG_PREFIX, message)
        logging.log(NOTIFY_LEVEL_NUM, msg)

    @staticmethod
    def error(trace=None):
        if trace is None:
            tb = traceback.format_exc()
            trace = '{} Something was wrong' if tb is None else tb
        logging.error("{} {}".format(MSG_PREFIX, trace))


logger = Logger()
