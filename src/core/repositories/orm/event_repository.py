import django_rq

from django.db.models import QuerySet

from core.repositories import IEventRepository
from cystack_models.models.events.events import Event
from cystack_models.models.users.users import User
from shared.constants.event import LOG_TYPES


class EventRepository(IEventRepository):
    def get_multiple_by_team_id(self, team_id: str):
        return Event.objects.filter(team_id=team_id).order_by('-creation_date')

    def save_new_event(self, **data) -> Event:
        return Event.create(**data)

    def save_new_event_by_multiple_teams(self, team_ids: list, **data):
        return Event.create_multiple_by_team_ids(team_ids, **data)

    def save_new_event_by_ciphers(self, ciphers, **data):
        return Event.create_multiple_by_ciphers(ciphers, **data)

    def normalize_enterprise_activity(self, activity_logs: QuerySet[Event]):
        # TODO: Send job to redis queue
        # django_rq.enqueue(self.export_enterprise_activity, activity_logs)
        return

    def export_enterprise_activity(self, activity_logs):
        user_ids = activity_logs.exclude(user_id__isnull=True).values_list('user_id', flat=True)
        acting_user_ids = activity_logs.exclude(acting_user_id__isnull=True).values_list('acting_user_id', flat=True)
        query_user_ids = list(set(list(user_ids) + list(acting_user_ids)))
        users_data = User.get_infor_by_user_ids(user_ids=query_user_ids)
        users_data_dict = dict()
        for user_data in users_data:
            users_data_dict[user_data.get("id")] = user_data

        logs = []
        for activity_log in activity_logs:
            acting_user_id = activity_log.acting_user_id
            user_id = activity_log.user_id
            acting_user_data = users_data_dict.get(acting_user_id)
            user_data = users_data_dict.get(user_id)
            log = self.__get_activity_log_data(activity_log)
            log["acting_user"] = {
                "name": acting_user_data.get("full_name"),
                "email": acting_user_data.get("email"),
                "username": acting_user_data.get("username"),
                "avatar": acting_user_data.get("avatar"),
            } if acting_user_data else {"name": "System", "email": None, "username": "System", "avatar": None}
            log["user"] = {
                "name": user_data.get("full_name"),
                "email": user_data.get("email"),
                "username": user_data.get("username"),
                "avatar": user_data.get("avatar"),
            } if user_data else None
            metadata = log.get("metadata", {})
            metadata.update({"user_email": user_data.get("email") if user_data else "Former user"})
            log["description"] = self.__get_description(log.get("type"), metadata)
            log.pop("metadata", None)
            logs.append(log)
        return logs

    @staticmethod
    def __get_activity_log_data(activity_log: Event):
        return {
            "id": activity_log.id,
            "type": activity_log.type,
            "creation_date": activity_log.creation_date,
            "acting_user": {
                "id": activity_log.acting_user_id,
            },
            "user": {
                "id": activity_log.user_id,
            },
            "ip_address": activity_log.ip_address,
            "cipher_id": activity_log.cipher_id,
            "collection_id": activity_log.collection_id,
            "device_type": activity_log.device_type,
            "group_id": activity_log.group_id,
            "enterprise_id": activity_log.team_id,
            "enterprise_member_id": activity_log.team_member_id,
            "metadata": activity_log.get_metadata(),
        }

    def __get_description(self, log_type, metadata):
        log_type = int(log_type)
        description = LOG_TYPES.get(log_type, {"vi": "", "en": ""})
        final_description = description.copy()

        normalizer_metadata = self.__get_normalizer_metadata(metadata)
        final_description["vi"] = description["vi"].format(**normalizer_metadata)
        final_description["en"] = description["en"].format(**normalizer_metadata)

        return final_description

    @staticmethod
    def __get_normalizer_metadata(metadata):
        normalizer_metadata = {}
        for k, v in metadata.items():
            normalizer_metadata[k] = v.replace("_", " ") if isinstance(v, str) else v
        return normalizer_metadata
