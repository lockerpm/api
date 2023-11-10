from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from django.db.models import F

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_emergency_access_model
from locker_server.api_orm.utils.revision_date import bump_account_revision_date
from locker_server.core.entities.emergency_access.emergency_access import EmergencyAccess
from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.user import User
from locker_server.core.repositories.emergency_access_repository import EmergencyAccessRepository
from locker_server.shared.constants.emergency_access import *
from locker_server.shared.utils.app import now

EmergencyAccessORM = get_emergency_access_model()
ModelParser = get_model_parser()


class EmergencyAccessORMRepository(EmergencyAccessRepository):
    @staticmethod
    def _get_emergency_access_orm(emergency_access_id: str) -> EmergencyAccessORM:
        try:
            return EmergencyAccessORM.objects.get(id=emergency_access_id)
        except EmergencyAccessORM.DoesNotExist:
            return None

    # ------------------------ List EmergencyAccess resource ------------------- #
    def list_by_grantor_id(self, grantor_id: int) -> List[EmergencyAccess]:
        grantor_emergencies_orm = EmergencyAccessORM.objects.filter(
            grantor_id=grantor_id
        ).order_by('creation_date')
        return [
            ModelParser.emergency_access_parser().parse_emergency_access(emergency_access_orm=e)
            for e in grantor_emergencies_orm
        ]

    def list_by_grantee_id(self, grantee_id: int) -> List[EmergencyAccess]:
        grantee_emergencies_orm = EmergencyAccessORM.objects.filter(
            grantee_id=grantee_id
        ).order_by('creation_date')
        return [
            ModelParser.emergency_access_parser().parse_emergency_access(emergency_access_orm=e)
            for e in grantee_emergencies_orm
        ]

    # ------------------------ Get EmergencyAccess resource --------------------- #
    def get_by_id(self, emergency_access_id: str) -> Optional[EmergencyAccess]:
        emergency_access_orm = self._get_emergency_access_orm(emergency_access_id=emergency_access_id)
        if not emergency_access_orm:
            return None
        return ModelParser.emergency_access_parser().parse_emergency_access(emergency_access_orm=emergency_access_orm)

    def check_emergency_existed(self, grantor_id: int, emergency_access_type: str,
                                grantee_id: int = None, email: str = None) -> bool:
        if grantee_id is not None:
            if EmergencyAccessORM.objects.filter(
                grantor_id=grantor_id, type=emergency_access_type, grantee_id=grantee_id
            ).exists():
                return True
        if email is not None:
            if EmergencyAccessORM.objects.filter(
                grantor_id=grantor_id, type=emergency_access_type, email=email
            ).exists():
                return True
        return False

    # ------------------------ Create EmergencyAccess resource --------------------- #
    def invite_emergency_access(self, grantor_id: int, emergency_access_type: str, wait_time_days: int, key: str = None,
                                grantee_id: int = None, email: str = None) -> Optional[EmergencyAccess]:
        emergency_access_orm = EmergencyAccessORM.create(
            grantor_id=grantor_id,
            emergency_access_type=emergency_access_type,
            wait_time_days=wait_time_days,
            grantee_id=grantee_id,
            email=email,
            key_encrypted=key
        )
        return ModelParser.emergency_access_parser().parse_emergency_access(emergency_access_orm=emergency_access_orm)

    # ------------------------ Update EmergencyAccess resource --------------------- #
    def accept_emergency_access(self, emergency_access: EmergencyAccess) -> EmergencyAccess:
        emergency_access_orm = self._get_emergency_access_orm(emergency_access_id=emergency_access.emergency_access_id)
        emergency_access_orm.email = None
        emergency_access_orm.status = EMERGENCY_ACCESS_STATUS_ACCEPTED
        emergency_access_orm.save()
        bump_account_revision_date(user=emergency_access_orm.grantee)

        emergency_access.email = None
        emergency_access.status = EMERGENCY_ACCESS_STATUS_ACCEPTED
        return emergency_access

    def confirm_emergency_access(self, emergency_access: EmergencyAccess, key_encrypted: str) -> EmergencyAccess:
        emergency_access_orm = self._get_emergency_access_orm(emergency_access_id=emergency_access.emergency_access_id)
        emergency_access_orm.email = None
        emergency_access_orm.status = EMERGENCY_ACCESS_STATUS_CONFIRMED
        emergency_access_orm.key_encrypted = key_encrypted
        emergency_access_orm.save()
        bump_account_revision_date(user=emergency_access_orm.grantee)

        emergency_access.email = None
        emergency_access.status = EMERGENCY_ACCESS_STATUS_CONFIRMED
        emergency_access.key_encrypted = key_encrypted
        return emergency_access

    def initiate_emergency_access(self, emergency_access: EmergencyAccess):
        emergency_access_orm = self._get_emergency_access_orm(emergency_access_id=emergency_access.emergency_access_id)
        emergency_access_orm.status = EMERGENCY_ACCESS_STATUS_RECOVERY_INITIATED
        emergency_access_orm.revision_date = now()
        emergency_access_orm.recovery_initiated_date = now()
        emergency_access_orm.last_notification_date = now()
        emergency_access_orm.save()

    def reject_emergency_access(self, emergency_access: EmergencyAccess):
        emergency_access_orm = self._get_emergency_access_orm(emergency_access_id=emergency_access.emergency_access_id)
        emergency_access_orm.status = EMERGENCY_ACCESS_STATUS_CONFIRMED
        emergency_access_orm.save()

    def approve_emergency_access(self, emergency_access: EmergencyAccess):
        emergency_access_orm = self._get_emergency_access_orm(emergency_access_id=emergency_access.emergency_access_id)
        emergency_access_orm.status = EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED
        emergency_access_orm.save()

    def auto_approve_emergency_accesses(self):
        current_time = now()
        EmergencyAccessORM.objects.filter(
            status=EMERGENCY_ACCESS_STATUS_RECOVERY_INITIATED,
            recovery_initiated_date__lte=current_time - F('wait_time_days') * 86400
        ).update(status=EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED)

    # ------------------------ Delete EmergencyAccess resource --------------------- #
    def destroy_emergency_access(self, emergency_access_id: str):
        emergency_access_orm = self._get_emergency_access_orm(emergency_access_id=emergency_access_id)
        if not emergency_access_orm:
            return None
        if emergency_access_orm.status == EMERGENCY_ACCESS_STATUS_CONFIRMED:
            bump_account_revision_date(user=emergency_access_orm.grantee)
        emergency_access_orm.delete()
