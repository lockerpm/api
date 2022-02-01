from typing import List


class FCMRequestEntity:
    def __init__(self, collapse_key: str = None, time_to_live: bool = None, delay_while_idle: bool = False,
                 fcm_ids: List[str] = None, data=None, priority: str = None):
        self._collapse_key = collapse_key
        self._time_to_live = time_to_live
        self._delay_while_idle = delay_while_idle
        self._fcm_ids = fcm_ids if fcm_ids else []
        self._data = data
        self._priority = priority

    @property
    def collapse_key(self):
        return self._collapse_key

    @property
    def time_to_live(self):
        return self._time_to_live

    @property
    def delay_while_idle(self):
        return self._delay_while_idle

    @property
    def fcm_ids(self):
        return self._fcm_ids

    @property
    def data(self):
        return self._data

    @property
    def priority(self):
        return self._priority

    def to_json(self):
        return {
            "collapse_key": self.collapse_key,
            "time_to_live": self.time_to_live,
            "delay_while_idle": self.delay_while_idle,
            "fcm_ids": self.fcm_ids,
            "data": self.data,
            "priority": self.priority
        }

    def add_fcm_id(self, fcm_id):
        self._fcm_ids.append(fcm_id)

    def remove_fcm_id(self, fcm_id):
        self._fcm_ids.remove(fcm_id)

    def clear_fcm_ids(self):
        self._fcm_ids = []

    def data_part(self, key, value):
        self._data.update({key: value})
