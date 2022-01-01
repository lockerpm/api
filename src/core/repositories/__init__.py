"""
These classes used to integrate with database models.
It seems like DAO (Data Access Object)
"""


from core.repositories.i_user_repository import IUserRepository
from core.repositories.i_session_repository import ISessionRepository
from core.repositories.i_device_repository import IDeviceRepository

from core.repositories.i_payment_repository import IPaymentRepository

from core.repositories.i_team_repository import ITeamRepository
from core.repositories.i_cipher_repository import ICipherRepository
from core.repositories.i_folder_repository import IFolderRepository
from core.repositories.i_sharing_repository import ISharingRepository

from core.repositories.i_team_member_repository import ITeamMemberRepository
from core.repositories.i_collection_repository import ICollectionRepository
from core.repositories.i_group_repository import IGroupRepository
from core.repositories.i_event_repository import IEventRepository

from core.repositories.i_emergency_access_repository import IEmergencyAccessRepository
