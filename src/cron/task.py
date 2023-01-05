import traceback

from cron.utils.logger import Logger
from shared.utils.app import now


class Task:
    def __init__(self):
        self.logger = Logger()

    @property
    def name(self):
        return self.__class__.__name__

    def register_job(self):
        raise NotImplementedError

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        raise NotImplementedError

    def real_run(self, *args):
        raise NotImplementedError

    def run(self):
        run_time = now(return_float=True)
        try:
            self.logger.info(f"[+] Start task {self.name}")
            result = self.real_run()
            self.logger.info(f"[+] Task {self.name} DONE")
            if result:
                self.log_job_execution(run_time)
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error()
            self.log_job_execution(run_time=run_time, exception=e.__str__(), tb=tb)

    def scheduling(self):
        raise NotImplementedError

    def start(self):
        self.scheduling()
