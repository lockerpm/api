import threading
import traceback

from django.db import connection

from shared.log.cylog import CyLog


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
            CyLog.error(**{"message": f"{func.__name__} error: {tb}"})
        finally:
            connection.close()
    return wrap



class ILockerBackground:
    def __init__(self, background=True, **kwargs):
        self.background = background

    def run(self, func_name: str, **kwargs):
        # Get self-function by function name
        func = getattr(self, func_name)
        if not func:
            raise Exception("Func name {} does not exist in this background".format(func_name))
        if not callable(func):
            raise Exception("Func name {} is not callable".format(func_name))
        # Run background or not this function
        if self.background:
            BackgroundThread(task=func, **kwargs)
        else:
            return func(**kwargs)

    @staticmethod
    def log_error(func_name: str = "", meta="", tb=None):
        if not tb:
            tb = traceback.format_exc()
        CyLog.error(**{"message": "[BACKGROUND] Function {} {} error: {}".format(func_name, meta, tb)})
