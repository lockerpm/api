from core.repositories import IEmergencyAccessRepository

from cystack_models.models.users.users import User
from cystack_models.models.emergency_access.emergency_access import EmergencyAccess


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
