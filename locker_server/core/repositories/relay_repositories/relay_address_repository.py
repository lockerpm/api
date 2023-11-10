from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod
from locker_server.core.entities.relay.relay_address import RelayAddress


class RelayAddressRepository(ABC):
    # ------------------------ List RelayAddress resource ------------------- #
    @abstractmethod
    def list_relay_addresses(self, **filters) -> List[RelayAddress]:
        pass

    @abstractmethod
    def list_user_relay_addresses(self, user_id: int, **filters) -> List[RelayAddress]:
        pass

    @abstractmethod
    def count_user_relay_addresses(self, user_id: int, **filters) -> int:
        pass

    # ------------------------ Get RelayAddress resource --------------------- #
    @abstractmethod
    def get_relay_address_by_id(self, relay_address_id: str) -> Optional[RelayAddress]:
        pass

    @abstractmethod
    def get_oldest_user_relay_address(self, user_id: int) -> Optional[RelayAddress]:
        pass

    @abstractmethod
    def get_relay_address_by_full_domain(self, address: str, domain_id: str,
                                         subdomain: str = None) -> Optional[RelayAddress]:
        pass

    @abstractmethod
    def get_relay_address_by_address(self, address: str) -> Optional[RelayAddress]:
        pass

    @abstractmethod
    def get_relay_address_by_address(self, address: str) -> Optional[RelayAddress]:
        pass

    # ------------------------ Create RelayAddress resource --------------------- #
    @abstractmethod
    def create_relay_address(self, relay_address_create_data) -> Optional[RelayAddress]:
        pass

    # ------------------------ Update RelayAddress resource --------------------- #

    @abstractmethod
    def update_relay_address(self, relay_address_id: str, relay_address_update_data) -> Optional[RelayAddress]:
        pass

    @abstractmethod
    def update_relay_address_statistic(self, relay_address_id: str, statistic_type: str,
                                       amount: int) -> Optional[RelayAddress]:
        pass

    # ------------------------ Delete RelayAddress resource --------------------- #
    @abstractmethod
    def delete_relay_address_by_id(self, relay_address_id: str) -> bool:
        pass

    @abstractmethod
    def delete_subdomain_relay_addresses(self, relay_subdomain_id: str) -> bool:
        pass
