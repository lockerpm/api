from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod
from locker_server.core.entities.relay.relay_subdomain import RelaySubdomain


class RelaySubdomainRepository(ABC):
    # ------------------------ List RelaySubdomain resource ------------------- #
    @abstractmethod
    def list_relay_subdomains(self, **filters) -> List[RelaySubdomain]:
        pass

    @abstractmethod
    def list_user_relay_subdomains(self, user_id: int, **filters) -> List[RelaySubdomain]:
        pass

    @abstractmethod
    def check_existed(self, **filters) -> bool:
        pass

    @abstractmethod
    def check_used_subdomain(self, user_id: str, subdomain: str) -> bool:
        pass

    # ------------------------ Get RelaySubdomain resource --------------------- #
    @abstractmethod
    def get_relay_subdomain_by_id(self, relay_subdomain_id: str) -> Optional[RelaySubdomain]:
        pass

    @abstractmethod
    def get_relay_subdomain_by_subdomain(self, subdomain: str) -> Optional[RelaySubdomain]:
        pass

    @abstractmethod
    def get_first_subdomain_by_domain_id(self, user_id: str, domain_id: str) -> Optional[RelaySubdomain]:
        pass

    # ------------------------ Create RelaySubdomain resource --------------------- #
    @abstractmethod
    def create_atomic_relay_subdomain(self, relay_subdomain_create_data) -> RelaySubdomain:
        pass

    @abstractmethod
    def create_relay_subdomain(self, relay_subdomain_create_data) -> RelaySubdomain:
        pass

    # ------------------------ Update RelaySubdomain resource --------------------- #

    @abstractmethod
    def update_relay_subdomain(self, relay_subdomain_id: str, relay_subdomain_update_data) -> Optional[RelaySubdomain]:
        pass

    # ------------------------ Delete RelaySubdomain resource --------------------- #
    @abstractmethod
    def delete_relay_subdomain_by_id(self, relay_subdomain_id: str) -> bool:
        pass
