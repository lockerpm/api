import json
from bson import ObjectId

from django.conf import settings
from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.utils.app import now


class NotificationORM(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=ObjectId)
    type = models.CharField(max_length=128)
    scope = models.CharField(max_length=64, default=settings.SCOPE_PWD_MANAGER, db_index=True)
    publish_time = models.FloatField(db_index=True)
    title = models.TextField(max_length=512)
    description = models.TextField(max_length=512, blank=True, null=True, default="")
    metadata = models.TextField(blank=True, null=True, default="")
    read = models.BooleanField(default=False)
    read_time = models.FloatField(null=True)

    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )

    class Meta:
        db_table = 'cs_notifications'

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
            "id": self.id,
            "type": self.type,
            "scope": self.scope,
            "publish_time": self.publish_time,
            "title": self.get_title(),
            "description": self.get_description(),
            "metadata": self.get_metadata(),
            "read": self.read,
            "read_time": self.read_time
        }


    @classmethod
    def create_multiple(cls, user_ids, notification_type, scope=settings.SCOPE_PWD_MANAGER,
                        vi_title="", en_title="", vi_description="", en_description="", metadata=None):
        notification_objs = []
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)
        for user_id in user_ids:
            notification_objs.append(cls(
                user_id=user_id,
                type=notification_type,
                scope=scope,
                publish_time=now(),
                title=json.dumps({"vi": vi_title, "en": en_title}),
                description=json.dumps({"vi": vi_description, "en": en_description}),
                metadata=metadata
            ))
        cls.objects.bulk_create(notification_objs, ignore_conflicts=True, batch_size=50)
