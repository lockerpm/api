import json

from locker_server.core.entities.user.user import User


class Notification(object):
    def __init__(self, notification_id: str, type: str, scope: str, publish_time: float, title: str,
                 description: str, metadata: str, read: bool, read_time: float, user: User):
        self._notification_id = notification_id
        self._type = type
        self._scope = scope
        self._publish_time = publish_time
        self._title = title
        self._description = description
        self._metadata = metadata
        self._read = read
        self._read_time = read_time
        self._user = user

    @property
    def notification_id(self):
        return self._notification_id

    @property
    def type(self):
        return self._type

    @property
    def scope(self):
        return self._scope

    @property
    def publish_time(self):
        return self._publish_time

    @property
    def title(self):
        return self._title

    @property
    def description(self):
        return self._description

    @property
    def metadata(self):
        return self._metadata

    @property
    def read(self):
        return self._read

    @property
    def read_time(self):
        return self._read_time

    @property
    def user(self):
        return self._user

    def get_title(self):
        if not self.title:
            return {}
        return json.loads(self.title)

    def get_description(self):
        if not self.description:
            return {}
        return json.loads(self.description)

    def get_metadata(self):
        if not self.metadata:
            return {}
        return json.loads(self.metadata)

    def to_json(self):
        return {
            "id": self.notification_id,
            "type": self.type,
            "scope": self.scope,
            "publish_time": self.publish_time,
            "title": self.get_title(),
            "description": self.get_description(),
            "metadata": self.get_metadata(),
            "read": self.read,
            "read_time": self.read_time
        }
