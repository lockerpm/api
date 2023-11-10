import threading
import traceback

from django.db import connection

from locker_server.shared.log.cylog import CyLog


class BackgroundThread:
    def __init__(self, task, interval=1, **kwargs):
        self.task = task
        self.interval = interval

        self.thread = threading.Thread(target=self.task, kwargs=kwargs)
        self.thread.daemon = True
        self.thread.start()


def background_exception_wrapper(func):
    def wrap(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            tb = traceback.format_exc()
            CyLog.error(**{"message": f"[!] Background func {func.__name__} error: {tb}\n"
                                      f"The arguments: {args} - {kwargs}"})
        finally:
            connection.close()
    return wrap
