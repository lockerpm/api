import logging
import requests

from django.conf import settings


class SlackHandler(logging.Handler):
    def emit(self, record):
        try:
            record.exc_info = record.exc_text = None
            content = {'text': self.format(record)}
            requests.post(
                url=settings.SLACK_WEBHOOK_API_LOG,
                json={"text": "```{}```".format(content['text'])},
                timeout=10
            )
        except Exception:
            print("Slack handler failed")


class SlackNewUserHandler(logging.Handler):
    def emit(self, record):
        try:
            record.exc_info = record.exc_text = None
            slack_attachments = [{
                "fallback": self.format(record),
                "color": "#0476E9",
                "text": record.msg,
            }]
            requests.post(
                url=settings.SLACK_WEBHOOK_NEW_USERS,
                json={
                    "attachments": slack_attachments
                },
                timeout=10
            )
        except:
            print("Slack handler failed")
