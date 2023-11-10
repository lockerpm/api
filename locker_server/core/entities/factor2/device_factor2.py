from locker_server.core.entities.factor2.factor2_method import Factor2Method
from locker_server.core.entities.user.device import Device


class DeviceFactor2(object):
    def __init__(self, device_factor2_id: int, expired_time: float, factor2_method: Factor2Method, device: Device):
        self._device_factor2_id = device_factor2_id,
        self._expired_time = expired_time
        self._factor2_method = factor2_method
        self._device = device

    @property
    def device_factor2_id(self):
        return self._device_factor2_id

    @property
    def expired_time(self):
        return self._expired_time

    @property
    def factor2_method(self):
        return self._factor2_method

    @property
    def device(self):
        return self._device
