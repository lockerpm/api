import json
from json import JSONDecodeError

from locker_server.shared.constants.missions import REWARD_TYPE_PROMO_CODE


class Mission(object):
    def __init__(self, mission_id: str, title: str = None, description_en: str = "", description_vi: str = "",
                 created_time: float = None, mission_type: str = None, order_index: int = None, available: bool = True,
                 extra_requirements=None, reward_type: str = REWARD_TYPE_PROMO_CODE, reward_value: float = 0):
        self._mission_id = mission_id
        self._title = title
        self._description_en = description_en
        self._description_vi = description_vi
        self._created_time = created_time
        self._mission_type = mission_type
        self._order_index = order_index
        self._available = available
        self._extra_requirements = extra_requirements
        self._reward_type = reward_type
        self._reward_value = reward_value

    @property
    def mission_id(self):
        return self._mission_id

    @property
    def title(self):
        return self._title

    @property
    def description_en(self):
        return self._description_en

    @property
    def description_vi(self):
        return self._description_vi

    @property
    def created_time(self):
        return self._created_time

    @property
    def mission_type(self):
        return self._mission_type

    @property
    def order_index(self):
        return self._order_index

    @property
    def available(self):
        return self._available

    @property
    def extra_requirements(self):
        return self._extra_requirements

    @property
    def reward_type(self):
        return self._reward_type

    @property
    def reward_value(self):
        return self._reward_value

    def get_extra_requirements(self):
        if not self.extra_requirements:
            return {}
        try:
            return json.loads(str(self.extra_requirements))
        except JSONDecodeError:
            return self.extra_requirements
