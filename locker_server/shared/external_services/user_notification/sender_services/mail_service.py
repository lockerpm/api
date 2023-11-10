from django.db.models import F

from locker_server.shared.external_services.user_notification.sender_services import SenderService
from locker_server.shared.mailing.mailer import send_email


def get_destinations(user_ids):
    from locker_server.api_orm.models.wrapper import get_user_model

    _UserORM = get_user_model()

    users = _UserORM.objects.filter(user_id__in=user_ids).exclude().annotate(
        name=F('full_name')
    ).values('email', 'name', 'language')
    return list(users)


def get_cc(user_ids):
    from locker_server.api_orm.models.wrapper import get_user_model
    _UserORM = get_user_model()

    if all(isinstance(item, str) for item in user_ids):
        return user_ids
    users = _UserORM.objects.filter(id__in=user_ids).exclude().values_list('username', flat=True)
    return list(users)


class MailService(SenderService):
    def send(self, **kwargs):
        # Get destinations
        if "destinations" not in kwargs:
            destinations = get_destinations(kwargs.get("user_ids") or [])
        else:
            destinations = kwargs.get("destinations", [])
        # Normalize the mail data in kwargs
        detail_data = self.normalize_data(**kwargs)
        # Normalize mail message
        mail_data = self._config["sender"]["mail"]
        mail_data["message"]["destinations"] = destinations
        mail_data["message"]["data"] = detail_data
        if "cc" in detail_data:
            mail_data["message"]["cc"] = get_cc(detail_data.get("cc", []))

        # Sending mail message
        org_mail_config = self._config["config"]["mail"]
        send_email(mail_data, org_mail_config)

    @staticmethod
    def normalize_data(**kwargs):
        return kwargs
