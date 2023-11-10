import json
import os

from locker_server.shared.background.i_background import BackgroundThread, background_exception_wrapper
from locker_server.shared.utils.factory import factory

NOTIFICATION_ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

SENDING_SERVICE_MAIL = "mail_service"
SENDING_SERVICE_WEB_NOTIFICATION = "notification_service"

DEFAULT_SENDING_SERVICES = [SENDING_SERVICE_MAIL]


class NotificationSender:
    def __init__(self, job, organization_id=None, scope="pwdmanager", services=None, background=True):
        self._job = job
        self._scope = scope
        self._services = services or DEFAULT_SENDING_SERVICES
        self._organization_id = organization_id
        self._config = json.load(open(self._get_config_file(), encoding='utf-8'))
        self._background = background

    def _get_config_file(self):
        file_name = f"{self._job}.json"
        return os.path.join(NOTIFICATION_ROOT_PATH, "jobs", self._scope, file_name)

    @staticmethod
    def _get_mail_config():
        from locker_server.containers.containers import mail_configuration_service
        return mail_configuration_service.get_mail_configuration()

    @background_exception_wrapper
    def real_send(self, **kwargs):
        for service in self._services:
            module_name = 'locker_server.shared.external_services.user_notification.sender_services.' + service
            if service == SENDING_SERVICE_MAIL:
                mail_config = self._get_mail_config()
                if not mail_config:
                    continue
                self._config.update({
                    "config": {"mail": mail_config.to_json()}
                })
            sender_service_cls = factory(module_name, self._job, self._config)
            if not sender_service_cls:
                continue

            # Using sender service to send notification
            sender_service_cls.send(**kwargs)

    def send(self, **kwargs):
        if self._background:
            BackgroundThread(task=self.real_send, **kwargs)
        else:
            self.real_send(**kwargs)
