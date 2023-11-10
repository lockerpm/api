import ast

from locker_server.shared.constants.event import LOG_TYPES


class Event(object):
    def __init__(self, event_id: str, event_type: str = None, acting_user_id: int = None, user_id: int = None,
                 cipher_id: str = None, collection_id: str = None, creation_date: float = None, device_type: int = None,
                 group_id: str = None, ip_address: str = None, team_id: str = None, team_member_id: str = None,
                 provider_id: str = None, policy_id: str = None, team_provider_id: str = None,
                 user_provider_id: str = None, metadata: str = None):
        self._event_id = event_id
        self._event_type = event_type
        self._acting_user_id = acting_user_id
        self._user_id = user_id
        self._cipher_id = cipher_id
        self._collection_id = collection_id
        self._creation_date = creation_date
        self._device_type = device_type
        self._group_id = group_id
        self._ip_address = ip_address
        self._team_id = team_id
        self._team_member_id = team_member_id
        self._policy_id = policy_id
        self._provider_id = provider_id
        self._team_provider_id = team_provider_id
        self._user_provider_id = user_provider_id
        self._metadata = metadata

    @property
    def event_id(self):
        return self._event_id

    @property
    def event_type(self):
        return self._event_type

    @property
    def acting_user_id(self):
        return self._acting_user_id

    @property
    def user_id(self):
        return self._user_id

    @property
    def cipher_id(self):
        return self._cipher_id

    @property
    def collection_id(self):
        return self._collection_id

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def device_type(self):
        return self._device_type

    @property
    def group_id(self):
        return self._group_id

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def team_id(self):
        return self._team_id

    @property
    def team_member_id(self):
        return self._team_member_id

    @property
    def policy_id(self):
        return self._policy_id

    @property
    def provider_id(self):
        return self._provider_id

    @property
    def team_provider_id(self):
        return self._team_provider_id

    @property
    def user_provider_id(self):
        return self._user_provider_id

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, new_metadata):
        self._metadata = new_metadata

    def get_metadata(self):
        if not self.metadata:
            return {}
        return ast.literal_eval(str(self.metadata))

    def get_description(self, use_html=True):
        metadata = self.get_metadata()
        log_type = int(self.event_type)
        if use_html:
            description = {
                "vi": LOG_TYPES.get(log_type, {}).get("vi", ""),
                "en": LOG_TYPES.get(log_type, {}).get("en", ""),
            }
        else:
            description = {
                "vi": LOG_TYPES.get(log_type, {}).get("vi_non_html", "") or LOG_TYPES.get(log_type, {}).get("vi", ""),
                "en": LOG_TYPES.get(log_type, {}).get("en_non_html", "") or LOG_TYPES.get(log_type, {}).get("en", ""),
            }
        final_description = description.copy()
        normalizer_metadata = self.get_normalizer_metadata(metadata)
        final_description["vi"] = description["vi"].format(**normalizer_metadata)
        final_description["en"] = description["en"].format(**normalizer_metadata)

        return final_description

    @staticmethod
    def get_normalizer_metadata(metadata):
        normalizer_metadata = {}
        for k, v in metadata.items():
            normalizer_metadata[k] = v.replace("_", " ") if isinstance(v, str) else v
        return normalizer_metadata

    def get_activity_log_data(self):
        return {
            "id": self.event_id,
            "type": self.event_type,
            "creation_date": self.creation_date,
            "acting_user": {
                "id": self.acting_user_id,
            },
            "user": {
                "id": self.user_id,
            },
            "ip_address": self.ip_address,
            "cipher_id": self.cipher_id,
            "collection_id": self.collection_id,
            "device_type": self.device_type,
            "group_id": self.group_id,
            "enterprise_id": self.team_id,
            "enterprise_member_id": self.team_member_id,
            "metadata": self.get_metadata(),
        }
