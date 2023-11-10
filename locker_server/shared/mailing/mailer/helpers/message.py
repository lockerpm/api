import json
import html
from os.path import dirname, realpath, join
from jinja2 import Template

from locker_server.shared.log.cylog import CyLog
from locker_server.shared.mailing.mailer.helpers.recipient import Recipient


TEMPLATE_DIR = join(dirname(dirname(dirname(realpath(__file__)))), 'templates')


class Message:
    def __init__(self, raw):
        self._valid = True
        try:
            self.raw = raw['message']
        except TypeError:
            self._valid = False
            CyLog.error(**{"message": f"[!] The message is not a valid JSON.\n{raw}"})

    @property
    def send_from(self):
        return self.raw.get('from')

    @property
    def cc(self):
        return self.raw.get('cc')

    @property
    def bcc(self):
        return self.raw.get('bcc')

    @property
    def service(self):
        try:
            return self.raw.get('service').lower()
        except AttributeError:
            return None

    @property
    def valid(self):
        if not self._valid:
            return False
        if not isinstance(self.raw['destinations'], list):
            CyLog.error(**{"message": f"[!] Destinations are not emails.\n{self.raw}"})
            return False
        # if self.service not in CONFIG['services']:
        #     logger.error(f"[!] The given service is not valid.\n{self.raw}")
        #     return False
        return True

    @property
    def template(self):
        return join(TEMPLATE_DIR, self.service)

    @property
    def subjects(self):
        return json.load(open(join(self.template, "subjects.json"), encoding="utf-8"))

    @property
    def job(self):
        return self.raw['job'].strip().lower()

    @property
    def data(self):
        return self.raw.get('data')

    @property
    def attachments(self):
        return self.raw.get('attachments')

    @property
    def allow_html(self):
        return self.raw.get('allow_html') if self.raw.get('allow_html') is not None else []

    def build_content(self, data, language):
        """
        Get data and language of each recipient to generate the final content
        """
        # Escape data for security
        for i in data:
            if isinstance(data[i], str) and i not in self.allow_html:
                data[i] = html.escape(data[i])
        main_content = Template(
            open(join(self.template, language, f"{self.job}.html"), encoding="utf-8").read()).render(data)

        # Handle email with no master
        no_master = self.subjects[self.job].get('no_master')
        if no_master:
            return main_content

        # Handle email with different master
        custom_master = self.subjects[self.job].get('custom_master')

        master_file = custom_master if custom_master is not None else 'master'
        html_content = Template(
            open(join(self.template, language, f"{master_file}.html"), encoding="utf-8").read()).render(
            cs_content_holder=main_content)
        return html_content

    def build_metadata(self, destination):
        """
        Add meta to destination
        """
        crm_tracking = self.subjects[self.job].get('crm_tracking')
        meta = destination.get('meta')
        if meta is None:
            if crm_tracking:
                meta = {
                    'job_id': f'service__{self.service}__{self.job}'
                }
            else:
                meta = dict()
        return meta

    def build_recipient(self, destination):
        language = destination['language'].strip().lower()
        user_data = destination['data'] if 'data' in destination else self.data
        attachments = destination['attachments'] if 'attachments' in destination else self.attachments
        user_data['user_fullname'] = destination['name']
        user_data['user_email'] = destination['email']

        content = self.build_content(data=user_data, language=language)
        meta = self.build_metadata(destination=destination)
        recipient = Recipient(
            name=destination['name'],
            address=destination['email'],
            subject=html.unescape(Template(self.subjects[self.job][language]).render(user_data)),
            content=content,
            attachments=attachments,
            meta=meta
        )
        return recipient

    @property
    def recipients(self):
        """
        :return: A list of Recipient
        """
        result = list()
        if not self.valid:
            return result
        for destination in self.raw['destinations']:
            recipient = self.build_recipient(destination=destination)
            result.append(recipient)
        return result
