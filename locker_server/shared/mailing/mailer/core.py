import traceback

from locker_server.shared.log.cylog import CyLog
from locker_server.shared.mailing.mailer.carriers import get_carrier
from locker_server.shared.mailing.mailer.helpers.message import Message
from locker_server.shared.mailing.mailer.helpers.sender import Sender


def get_service_config(message, service_config):
    """
    :param message: A Message instance
    :param service_config:
    :return: A configuration corresponding to the given message
    """
    # service_config = CONFIG['services'][message.service]
    if message.send_from is not None:
        service_config['sender_name'] = message.send_from['name']
        service_config['sender_email'] = message.send_from['email']
        service_config.pop('reply_to', None)
    return service_config


def send_email(raw, org_mail_config):
    """
    The email is sent actually here
    """
    m = Message(raw)
    if not m.valid:
        return False

    carrier_type = org_mail_config["mail_provider"]
    carrier = get_carrier(carrier_type=carrier_type, **org_mail_config.get("mail_provider_options", {}))

    sender_config = {
        "carrier": carrier_type,
        "sender_email": org_mail_config.get("from_email"),
        "sender_name": org_mail_config.get("from_name"),
        "reply_to": org_mail_config.get("reply_to")
    }
    sender = Sender(raw=get_service_config(m, sender_config))

    for recipient in m.recipients:
        try:
            carrier.send(sender, recipient, m.cc, m.bcc)
        except Exception as e:
            tb = traceback.format_exc()
            CyLog.error(**{
                "message": f"[!] Mail sent failed: {e}\nFROM: {sender.to_string()}\nTO: {recipient.address}\n{tb}"
            })
            return False

    return True
