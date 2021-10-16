from cron.controllers.core import CronTask


def start():
    cron_task = CronTask()
    cron_task.start()
