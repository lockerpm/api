from typing import Tuple, Dict, List, Optional

from locker_server.core.entities.user.exclude_domain import ExcludeDomain
from locker_server.core.exceptions.exclude_domain_exception import ExcludeDomainNotExistException
from locker_server.core.repositories.exclude_domain_repository import ExcludeDomainRepository


class ExcludeDomainService:
    """
    This class represents Use Cases related ExcludeDomain
    """

    def __init__(self, exclude_domain_repository: ExcludeDomainRepository):
        self.exclude_domain_repository = exclude_domain_repository

    def list_user_exclude_domains(self, user_id: int, **filter_params) -> List[ExcludeDomain]:
        return self.exclude_domain_repository.list_user_exclude_domains(user_id, **filter_params)

    def get_user_exclude_domain(self, user_id: int, exclude_domain_id: str) -> Optional[ExcludeDomain]:
        exclude_domain = self.exclude_domain_repository.get_exclude_domain_by_id(exclude_domain_id=exclude_domain_id)
        if not exclude_domain or exclude_domain.user.user_id != user_id:
            raise ExcludeDomainNotExistException
        return exclude_domain

    def create_exclude_domain(self, user_id: int, domain: str) -> ExcludeDomain:
        return self.exclude_domain_repository.create_exclude_domain(user_id=user_id, domain=domain)

    def delete_exclude_domain(self, exclude_domain_id: str):
        result = self.exclude_domain_repository.remove_exclude_domain(exclude_domain_id=exclude_domain_id)
        if result is False:
            raise ExcludeDomainNotExistException
        return True
