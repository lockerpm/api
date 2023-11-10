import requests


class Carrier:
    """
    This class represent an email sender
    """

    def __init__(self, **kwargs):
        self.carrier = self.init_carrier(**kwargs)

    def init_carrier(self, **kwargs):
        raise NotImplementedError

    def send(self, sender, recipient):
        raise NotImplementedError

    def build_attachments(self, a_file):
        raise NotImplementedError

    def hook(self, recipient, message_id):
        try:
            if recipient.meta['use_hook']:
                payload = [
                    {
                        "job_id": recipient.meta['job_id'],
                        "sg_message_id": message_id
                    }
                ]
                requests.post(recipient.meta['hook_url'], json=payload)
        except requests.exceptions.RequestException:
            pass


class CarrierInvalidAuthentication(Exception):
    """
    The carrier authentication is invalid
    """