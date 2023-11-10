from locker_server.shared.mailing.mailer.carriers.sendgrid import SendGrid
from locker_server.shared.mailing.mailer.carriers.smtp import SMTP


def get_carrier(carrier_type: str, **kwargs):
    carrier = None
    if carrier_type == 'sendgrid':
        carrier = SendGrid(**kwargs)
    elif carrier_type == 'smtp':
        carrier = SMTP(**kwargs)
    return carrier
