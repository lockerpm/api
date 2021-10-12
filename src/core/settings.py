from core.repositories.orm import *


CORE_CONFIG = {
    "services": {

    },
    "repositories": {
        "IUserRepository": UserRepository,
        "ISessionRepository": SessionRepository,
        "ITeamRepository": TeamRepository,
        "ICipherRepository": CipherRepository,
        "IFolderRepository": FolderRepository,
        "ITeamMemberRepository": TeamMemberRepository,
        "ICollectionRepository": CollectionRepository,
        "IPaymentRepository": PaymentRepository
    }
}