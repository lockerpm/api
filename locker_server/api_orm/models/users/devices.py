from locker_server.api_orm.abstracts.users.devices import AbstractDeviceORM


class DeviceORM(AbstractDeviceORM):
    class Meta(AbstractDeviceORM.Meta):
        swappable = 'LS_DEVICE_MODEL'
        db_table = 'cs_devices'
