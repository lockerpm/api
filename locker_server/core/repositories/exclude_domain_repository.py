from typing import Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.user.exclude_domain import ExcludeDomain


class ExcludeDomainRepository(ABC):
    # ------------------------ List ExcludeDomain resource ------------------- #
    @abstractmethod
    def list_user_exclude_domains(self, user_id: int, **filter_params) -> List[ExcludeDomain]:
        pass

    # ------------------------ Get ExcludeDomain resource --------------------- #
    @abstractmethod
    def get_exclude_domain_by_id(self, exclude_domain_id: str) -> Optional[ExcludeDomain]:
        pass

    # ------------------------ Create ExcludeDomain resource --------------------- #
    @abstractmethod
    def create_exclude_domain(self, user_id: int, domain: str) -> ExcludeDomain:
        pass

    # ------------------------ Update ExcludeDomain resource --------------------- #

    # ------------------------ Delete ExcludeDomain resource --------------------- #
    @abstractmethod
    def remove_exclude_domain(self, exclude_domain_id: str):
        pass
