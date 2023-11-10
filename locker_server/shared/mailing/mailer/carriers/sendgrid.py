import time
import base64

import requests
import sendgrid
from sendgrid.helpers.mail import *
from urllib.error import URLError
from python_http_client import BadRequestsError

from locker_server.shared.log.cylog import CyLog
from locker_server.shared.mailing.mailer.carriers.carrier import Carrier, CarrierInvalidAuthentication


class SendGrid(Carrier):
    """
    Use Sendgrid as a carrier
    """

    def init_carrier(self, **kwargs):
        api_key = kwargs.get("api_key")
        if not api_key:
            raise CarrierInvalidAuthentication
        carrier = sendgrid.SendGridAPIClient(api_key=api_key)
        return carrier

    def send(self, sender, recipient, cc=None, bcc=None):
        _from_email = Email(email=sender.address, name=sender.name)
        _mail = Mail(
            from_email=_from_email, subject=recipient.subject, to_emails=recipient.address,
            html_content=recipient.content
        )

        # Handle reply-to
        if sender.reply_address is not None:
            if sender.address != sender.reply_address:
                _mail.reply_to = Email(sender.reply_address, sender.reply_name)

        # Handle attachments
        if recipient.attachments is not None and isinstance(recipient.attachments, list):
            for a in recipient.attachments:
                built_attachment = self.build_attachments(a)
                _mail.add_attachment(built_attachment)

        # Handle meta
        for key in recipient.meta:
            _mail.add_custom_arg(CustomArg(key, recipient.meta[key]))

        # Handle cc and bcc
        if cc and isinstance(cc, list):
            cc = set(cc)
            for item in cc:
                if item != recipient.address:
                    _mail.personalizations[0].add_cc(Email(item))
        if bcc and isinstance(bcc, list):
            bcc = set(bcc)
            for item in bcc:
                if item != recipient.address:
                    _mail.personalizations[0].add_bcc(Email(item))

        try_count = 0
        while True:
            try_count += 1
            if try_count >= 10:
                CyLog.error(**{
                    "message": '[!] Tried sending mail by sendgrid more than 10 times but still getting error'
                })
            try:
                res = self.carrier.client.mail.send.post(request_body=_mail.get())
                if res.status_code < 200 or res.status_code >= 300:
                    CyLog.error(**{"message": "MailSender: Can't send email to %s. %s" % (recipient.address, res.body)})

                    return None
                else:
                    return res.headers['X-Message-Id']
            except URLError as e:
                # Handle Temporary failure in name resolution
                CyLog.info(**{"message": str(e)})
                time.sleep(60)
            except BadRequestsError as e:
                if e.body:
                    CyLog.error(**{"message": "SendGrid: Can't send email to %s. %s" % (recipient.address, e.body)})
                raise e

    def build_attachments(self, a_file):
        _attachment = Attachment()
        _attachment.file_content = base64.b64encode(requests.get(a_file['url']).content).decode()
        _attachment.file_name = a_file['name']
        return _attachment
