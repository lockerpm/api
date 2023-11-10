import traceback

from locker_server.shared.background.i_background import BackgroundThread
from locker_server.shared.log.cylog import CyLog


class LockerBackground:
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
