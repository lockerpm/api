from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod
from locker_server.core.entities.relay.deleted_relay_address import DeletedRelayAddress


class DeletedRelayAddressRepository(ABC):
    # ------------------------ List DeletedRelayAddress resource ------------------- #
    @abstractmethod
    def list_deleted_relay_addresses(self, **filters) -> List[DeletedRelayAddress]:
        pass

    @abstractmethod
    def list_user_deleted_relay_addresses(self, user_id: int, **filters) -> List[DeletedRelayAddress]:
        pass

    # ------------------------ Get DeletedRelayAddress resource --------------------- #
    @abstractmethod
    def get_deleted_relay_address_by_id(self, relay_address_id: str) -> Optional[DeletedRelayAddress]:
        pass

    @abstractmethod
    def check_exist_address_hash(self, address_hash: str) -> bool:
        pass

    # ------------------------ Create DeletedRelayAddress resource --------------------- #
    @abstractmethod
    def create_deleted_relay_address(self, deleted_relay_address_create_data) -> DeletedRelayAddress:
        pass

    # ------------------------ Update DeletedRelayAddress resource --------------------- #

    # ------------------------ Delete DeletedRelayAddress resource --------------------- #
