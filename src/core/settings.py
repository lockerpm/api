from core.repositories.orm import *


CORE_CONFIG = {
    "services": {

    },
    "repositories": {
        "IUserRepository": UserRepository,
        "IDeviceRepository": DeviceRepository,
        "IPaymentRepository": PaymentRepository,
        "ITeamRepository": TeamRepository,
        "ICipherRepository": CipherRepository,
        "IFolderRepository": FolderRepository,
        "ISharingRepository": SharingRepository,
        "ITeamMemberRepository": TeamMemberRepository,
        "ICollectionRepository": CollectionRepository,
        # "IGroupRepository": GroupRepository,
        "IEventRepository": EventRepository,
        "IEmergencyAccessRepository": EmergencyAccessRepository,
    }
}