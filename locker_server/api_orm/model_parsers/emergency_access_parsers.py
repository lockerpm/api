from locker_server.api_orm.model_parsers.wrapper_specific_model_parser import get_specific_model_parser
from locker_server.api_orm.models import *
from locker_server.core.entities.emergency_access.emergency_access import EmergencyAccess


class EmergencyAccessParser:
    @classmethod
    def parse_emergency_access(cls, emergency_access_orm: EmergencyAccessORM) -> EmergencyAccess:
        user_parser = get_specific_model_parser("UserParser")
        return EmergencyAccess(
            emergency_access_id=emergency_access_orm.id,
            creation_date=emergency_access_orm.creation_date,
            revision_date=emergency_access_orm.revision_date,
            last_notification_date=emergency_access_orm.last_notification_date,
            recovery_initiated_date=emergency_access_orm.recovery_initiated_date,
            status=emergency_access_orm.status,
            emergency_access_type=emergency_access_orm.type,
            wait_time_days=emergency_access_orm.wait_time_days,
            key_encrypted=emergency_access_orm.key_encrypted,
            email=emergency_access_orm.email,
            grantee=user_parser.parse_user(user_orm=emergency_access_orm.grantee) if emergency_access_orm.grantee else None,
            grantor=user_parser.parse_user(user_orm=emergency_access_orm.grantor),
        )
