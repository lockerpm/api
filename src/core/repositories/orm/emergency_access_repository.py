from core.repositories import IEmergencyAccessRepository
from core.utils.account_revision_date import bump_account_revision_date

from shared.constants.emergency_access import *
from cystack_models.models.users.users import User
from cystack_models.models.emergency_access.emergency_access import EmergencyAccess
from shared.utils.app import now


class EmergencyAccessRepository(IEmergencyAccessRepository):
    def get_by_id(self, emergency_access_id):
        """
        Get emergency access object from id
        :param emergency_access_id: (str) Emergency Access UUID
        :return:
        """
        return EmergencyAccess.objects.get(id=emergency_access_id)

    def get_multiple_by_grantor(self, grantor: User):
        """
        Get list emergency access which user is a grantor
        :param grantor: (obj) Grontor
        :return:
        """
        grantor_emergency = grantor.emergency_grantors.all().order_by('creation_date')
        return grantor_emergency

    def get_multiple_by_grantee(self, grantee: User):
        """
        Get list emergency access which user is a grantee
        :param grantee:
        :return:
        """
        grantee_emergency = grantee.emergency_grantees.all().order_by('creation_date')
        return grantee_emergency

    def delete_emergency_access(self, emergency_access: EmergencyAccess, user_id):
        """
        Destroy an EmergencyAsset object
        :param emergency_access: (obj)
        :param user_id: Grantor or Grantee
        :return:
        """
        if emergency_access.status == EMERGENCY_ACCESS_STATUS_CONFIRMED:
            bump_account_revision_date(user=emergency_access.grantee)
        emergency_access.delete()

    def invite_emergency_access(self, access_type, wait_time_days, grantor, grantee=None, email=None):
        emergency_access = EmergencyAccess.create(
            grantor=grantor, access_type=access_type, wait_time_days=wait_time_days, grantee=grantee, email=email
        )
        return emergency_access

    def accept_emergency_access(self, emergency_access: EmergencyAccess):
        emergency_access.email = None
        emergency_access.status = EMERGENCY_ACCESS_STATUS_ACCEPTED
        emergency_access.save()
        bump_account_revision_date(user=emergency_access.grantee)

    def confirm_emergency_access(self, emergency_access: EmergencyAccess, key_encrypted: str):
        emergency_access.email = None
        emergency_access.status = EMERGENCY_ACCESS_STATUS_CONFIRMED
        emergency_access.key_encrypted = key_encrypted
        emergency_access.save()
        bump_account_revision_date(user=emergency_access.grantee)

    def initiate_emergency_access(self, emergency_access: EmergencyAccess):
        emergency_access.status = EMERGENCY_ACCESS_STATUS_RECOVERY_INITIATED
        emergency_access.revision_date = now()
        emergency_access.recovery_initiated_date = now()
        emergency_access.last_notification_date = now()
        emergency_access.save()

    def reject_emergency_access(self, emergency_access: EmergencyAccess):
        emergency_access.status = EMERGENCY_ACCESS_STATUS_CONFIRMED
        emergency_access.save()

    def approve_emergency_access(self, emergency_access: EmergencyAccess):
        emergency_access.status = EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED
        emergency_access.save()
