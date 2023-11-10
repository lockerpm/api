"""
Routing file of channel layer (Web Socket)
"""

from channels.routing import ProtocolTypeRouter, URLRouter
# from django.core.asgi import get_asgi_application

from locker_server.shared.middlewares.token_ws_auth_middleware import WSTokenAuthMiddlewareStack
from locker_server.api.websocket import urls as v1_websocket_urls


websocket_urls = []
websocket_urls += v1_websocket_urls.websocket_urlpatterns


application = ProtocolTypeRouter({
    # "http": get_asgi_application(),
    "websocket": WSTokenAuthMiddlewareStack(
        URLRouter(
            websocket_urls
        )
    ),
})
