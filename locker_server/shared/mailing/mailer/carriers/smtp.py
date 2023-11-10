import base64
import smtplib
import requests
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from locker_server.shared.mailing.mailer.carriers.carrier import Carrier


class SMTP(Carrier):
    """
    Use SMTP credential as a carrier
    """

    def init_carrier(self, **kwargs):
        smtp_host = kwargs.get("smtp_host")
        smtp_port = kwargs.get("smtp_port")
        smtp_username = kwargs.get("smtp_username")
        smtp_password = kwargs.get("smtp_password")

        carrier = smtplib.SMTP(smtp_host, smtp_port)
        carrier.ehlo()
        carrier.starttls()
        carrier.ehlo()
        carrier.login(smtp_username, smtp_password)
        return carrier

    def send(self, sender, recipient, cc=None, bcc=None):
        message = MIMEMultipart("alternative")
        message["Subject"] = recipient.subject
        message["From"] = '%s <%s>' % (sender.name, sender.address)
        message["To"] = recipient.address
        content = MIMEText(recipient.content, 'html')
        message.attach(content)

        # Handle reply-to
        if sender.reply_address is not None:
            message['reply-to'] = '%s <%s>' % (sender.reply_name, sender.reply_address)

        # Handle attachments
        if recipient.attachments is not None and isinstance(recipient.attachments, list):
            for a in recipient.attachments:
                attachment = self.build_attachments(a)
                message.attach(attachment)

        # Handle cc and bcc
        if cc and isinstance(cc, list):
            cc = set(cc)
            for item in cc:
                if item != recipient.address:
                    message.add_header('Cc', item)

        if bcc and isinstance(bcc, list):
            bcc = set(bcc)
            for item in bcc:
                if item != recipient.address:
                    message.add_header('Bcc', item)
        try:
            self.carrier.sendmail(sender.address, recipient.address, message.as_string())
        except (UnicodeEncodeError, smtplib.SMTPRecipientsRefused):
            pass

    def build_attachments(self, a_file):
        content = base64.b64encode(requests.get(a_file['url']).content).decode()
        filename = a_file['name']
        attachment = MIMEApplication(content)
        attachment.add_header('Content-Disposition', 'attachment; filename="%s"' % filename)
        return attachment
