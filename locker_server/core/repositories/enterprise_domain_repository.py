from abc import ABC, abstractmethod
from typing import List, Optional

from locker_server.core.entities.enterprise.domain.domain import Domain


class EnterpriseDomainRepository(ABC):

    # ------------------------ List Domain resource ------------------- #
    @abstractmethod
    def list_domains(self, **filters) -> List[Domain]:
        pass

    @abstractmethod
    def list_enterprise_domains(self, enterprise_id: str, **filters) -> List[Domain]:
        pass

    @abstractmethod
    def check_domain_exist(self, enterprise_id: str, domain: str) -> bool:
        pass

    @abstractmethod
    def check_root_domain_verify(self, root_domain: str, enterprise_id: str = None, exclude_enterprise_id: str = None):
        pass

    @abstractmethod
    def count_unverified_domain(self, enterprise_id: str) -> int:
        pass

    # ------------------------ Get Domain resource --------------------- #
    @abstractmethod
    def get_domain_by_id(self, domain_id: str) -> Optional[Domain]:
        pass

    @abstractmethod
    def get_ownerships_by_domain_id(self, domain_id: str) -> List:
        pass

    @abstractmethod
    def check_verification(self, domain_id: str) -> bool:
        pass

    # ------------------------ Create Domain resource --------------------- #
    @abstractmethod
    def create_domain(self, domain_create_data) -> Domain:
        pass

    # ------------------------ Update Domain resource --------------------- #
    @abstractmethod
    def update_domain(self, domain_id: str, domain_update_data) -> Optional[Domain]:
        pass

    # ------------------------ Delete Domain resource --------------------- #

    @abstractmethod
    def delete_domain_by_id(self, domain_id: str) -> bool:
        pass
