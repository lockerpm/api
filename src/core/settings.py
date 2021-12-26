from core.repositories.orm import *


CORE_CONFIG = {
    "services": {

    },
    "repositories": {
        "IUserRepository": UserRepository,
        "ISessionRepository": SessionRepository,
        "IDeviceRepository": DeviceRepository,
        "IPaymentRepository": PaymentRepository,
        "ITeamRepository": TeamRepository,
        "ICipherRepository": CipherRepository,
        "IFolderRepository": FolderRepository,
        "ITeamMemberRepository": TeamMemberRepository,
        "ICollectionRepository": CollectionRepository,
        "IGroupRepository": GroupRepository,
        "IEventRepository": EventRepository,
        "IEmergencyAccessRepository": EmergencyAccessRepository,
    }
}