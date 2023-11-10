from redis.asyncio.connection import Connection, RedisSSLContext
from typing import Optional


class CustomSSLConnection(Connection):
    def __init__(
            self,
            ssl_context: Optional[str] = None,
            **kwargs,
    ):
        super().__init__(**kwargs)
        self.ssl_context = RedisSSLContext(ssl_context)


class RedisSSLContext:
    __slots__ = (
        "context",
    )

    def __init__(
            self,
            ssl_context,
    ):
        self.context = ssl_context

    def get(self):
        return self.context
