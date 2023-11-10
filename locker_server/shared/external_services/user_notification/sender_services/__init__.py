class SenderService:
    def __init__(self, job, config):
        self._job = job
        self._config = config

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def job(self):
        return self._job

    @property
    def config(self):
        return self._config

    def send(self, **kwargs):
        raise NotImplementedError

