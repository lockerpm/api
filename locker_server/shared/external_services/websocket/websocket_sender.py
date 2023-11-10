from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer


class WebSocketSender:
    @classmethod
    def send_message(cls, group_name, message):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name, {
                'type': 'event.sync',
                'data': message
            }
        )
