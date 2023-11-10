import urllib.parse as urlparse
import logging.config
import traceback
import jwt

from django.core.exceptions import ObjectDoesNotExist
from django.db import close_old_connections
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async

from locker_server.containers.containers import auth_service
from locker_server.core.exceptions.device_access_token_exception import DeviceAccessTokenDoesNotExistException
from locker_server.shared.utils.app import now


@database_sync_to_async
def get_access_token_sync_to_async(jti):
    try:
        device_access_token = auth_service.get_device_access_token_by_id(device_access_token_id=jti)
        return device_access_token
    except DeviceAccessTokenDoesNotExistException:
        return None


@database_sync_to_async
def check_device_access_token(device_access_token, payload):
    device_identifier = payload.get("device")
    client_id = payload.get("client_id")
    user_internal_id = payload.get("sub")
    device = device_access_token.device
    if device.device_identifier != device_identifier or device.client_id != client_id or \
            device.user.internal_id != user_internal_id:
        return None
    return device.user, device_access_token


class WSTokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, *args, **kwargs):
        # Close old database connections to prevent usage of timed out connections
        close_old_connections()

        authorization = await self._check_token(scope=scope)
        if authorization is None:
            scope['user'] = AnonymousUser()
            scope['token'] = None
            scope['token_expired_time'] = 0
        else:
            user = authorization[0]
            token_obj = authorization[1]
            scope['user'] = user
            scope['token'] = token_obj
            scope['token_expired_time'] = 0
        return await self.inner(scope, *args, **kwargs)

    @staticmethod
    def _get_token(scope):
        query_params = scope["query_string"].decode('utf8')
        tokens = urlparse.parse_qs(query_params).get("token")
        if not tokens:
            return None
        return tokens[0]

    async def _check_token(self, scope):
        token_value = self._get_token(scope)
        if token_value is None:
            return None
        try:
            payload = jwt.decode(token_value, settings.SECRET_KEY, algorithms=['HS256'])
            scopes = payload.get("scope", [])
            if "api" not in scopes:
                return None
            expired_time = payload.get("exp")
            if expired_time < now():
                return None
            # Get token from database
            device_access_token = await get_access_token_sync_to_async(payload.get("jti"))
            if not device_access_token:
                return None
            return await check_device_access_token(device_access_token, payload)

        except (jwt.InvalidSignatureError, jwt.DecodeError, ObjectDoesNotExist, jwt.InvalidAlgorithmError):
            return None
        except Exception:
            from locker_server.shared.log.config import logging_config
            logging.config.dictConfig(logging_config)
            logger = logging.getLogger('stdout_service')
            tb = traceback.format_exc()
            logger.critical(tb)
            return None
        finally:
            close_old_connections()


WSTokenAuthMiddlewareStack = lambda inner: WSTokenAuthMiddleware(AuthMiddlewareStack(inner))
