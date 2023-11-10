import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from locker_server.shared.error_responses.error import refer_error, gen_error
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.utils.app import now

WS_PWD_SYNC_GROUP_NAME = "pwd_sync_{}"


class AppGeneralWebsocketConsumer(AsyncWebsocketConsumer):
    events = {}

    async def connect(self):
        await super(AppGeneralWebsocketConsumer, self).connect()

    async def disconnect(self, code):
        await super(AppGeneralWebsocketConsumer, self).disconnect(code)

    async def receive(self, text_data=None, bytes_data=None):
        await super(AppGeneralWebsocketConsumer, self).receive(text_data, bytes_data)

    async def error(self, event=None, code=None, error_data=None):
        CyLog.error(**{"message": "Websocket Error: Event {} - Code: {} - Error data: {}".format(
            event, code, error_data
        )})
        await self.close()

    def is_auth(self):
        """
        Check user is authenticated>
        :return:
        """
        try:
            user = self.scope["user"]
            token = self.scope["token"]
            if isinstance(user, AnonymousUser) or (token is None):
                return None
            expired_time = token.expired_time
            if expired_time < now():
                return None
        except (KeyError, ValueError):
            return None
        except Exception as e:
            print("IS AUTH: ", e.__str__())
            return None
        return user

    @staticmethod
    def to_json(text_data):
        try:
            data = json.loads(text_data)
            return data
        except Exception as e:
            CyLog.error(**{"message": "JSON converter was error: {} \n Text data: {}".format(e, text_data)})
            return {"error": {"code": "0008", "message": "Unknown Error"}}

    @staticmethod
    def send_error(text_data, error_code=None):
        text_data["error"] = dict() if error_code is None else refer_error(gen_error(error_code))
        return text_data
