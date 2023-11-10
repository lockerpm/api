import json
import traceback
import logging.config

from locker_server.shared.general_websocket_consumer import AppGeneralWebsocketConsumer, WS_PWD_SYNC_GROUP_NAME


class PwdSyncConsumer(AppGeneralWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(PwdSyncConsumer, self).__init__(*args, **kwargs)
        self.user = None
        self.group_name = ""

    async def connect(self):
        """
        Client (web client) connects to websocket server
        :return:
        """
        try:
            user = self.is_auth()
            if not user:
                return await self.close()
            else:
                self.user = user
                self.group_name = WS_PWD_SYNC_GROUP_NAME.format(user.user_id)
                # Join this group
                await self.channel_layer.group_add(
                    self.group_name,
                    self.channel_name
                )
                await self.accept()
        except Exception:
            from locker_server.shared.log.config import logging_config
            logging.config.dictConfig(logging_config)
            logger = logging.getLogger('customer_service')
            tb = traceback.format_exc()
            logger.critical("Connect PWDSyncConsumer Errors:\n{}".format(tb))

    async def disconnect(self, code):
        """
        Clients disconnect to WS server
        :param code:
        :return:
        """
        # Leave this group
        try:
            if self.group_name:
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
            else:
                await super().disconnect(code)
        except Exception:
            from locker_server.shared.log.config import logging_config
            logging.config.dictConfig(logging_config)
            logger = logging.getLogger('customer_service')
            tb = traceback.format_exc()
            logger.critical(
                "Disconnect PWDSyncConsumer Errors: {} - {}\n{}".format(self.group_name, self.channel_name, tb)
            )
            await super().disconnect(code)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receiving message from client
        :param text_data:
        :param bytes_data:
        :return:
        """
        await super(PwdSyncConsumer, self).receive(text_data, bytes_data)

    async def event_sync(self, event):
        event_data = event["data"]
        event_data_event = event_data["event"]
        event_data_type = event_data.get("type", "")
        if event_data_type.startswith("member"):
            event_data_event = "members"
        elif event_data_type.startswith("emergency"):
            event_data_event = "emergency_access"
        elif event_data_type.startswith("quick_share"):
            event_data_event = "quick_share"
        content = {
            "event": event_data_event,
            "type": event_data_type,
            "data": event_data.get("data", {})
        }
        await self.send(text_data=json.dumps(content))
