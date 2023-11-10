from locker_server.api_orm.abstracts.emergency_access.emergency_access import AbstractEmergencyAccessORM
from locker_server.shared.utils.app import now


class EmergencyAccessORM(AbstractEmergencyAccessORM):
    class Meta(AbstractEmergencyAccessORM.Meta):
        swappable = 'LS_EMERGENCY_ACCESS_MODEL'
        db_table = 'cs_emergency_access'

    @classmethod
    def create(cls, grantor_id, emergency_access_type: str, wait_time_days: int = 7,
               grantee_id=None, email: str = None, key_encrypted: str = None):
        new_emergency_access = cls(
            grantor_id=grantor_id, type=emergency_access_type, wait_time_days=wait_time_days,
            key_encrypted=key_encrypted,
            grantee_id=grantee_id, email=email,
            creation_date=now(), revision_date=now()
        )
        new_emergency_access.save()
        return new_emergency_access
