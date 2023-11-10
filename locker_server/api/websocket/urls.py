from django.urls import re_path

from locker_server.api.websocket.sync import pwd_sync_consumer

websocket_urlpatterns = []


# -------------------------- Password Manager Sync ------------------------------- #
websocket_urlpatterns += [
    re_path(r'^ws/cystack_platform/pm/sync$', pwd_sync_consumer.PwdSyncConsumer.as_asgi()),
]
