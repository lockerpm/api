import os
import sys

from locker_server.cron.utils.django_config import django_config

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

# Init django for the cron tasks
args = sys.argv
try:
    db_name = args[1]
except (IndexError, KeyError):
    db_name = 'default'

django_config()
