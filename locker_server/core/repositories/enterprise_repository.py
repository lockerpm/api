from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.enterprise.enterprise import Enterprise


class EnterpriseRepository(ABC):
    # ------------------------ List Enterprise resource ------------------- #
    @abstractmethod
    def list_enterprises(self, **filters) -> List[Enterprise]:
        pass

    @abstractmethod
    def list_user_enterprises(self, user_id: int, **filter_params) -> List[Enterprise]:
        pass

    @abstractmethod
    def list_user_enterprise_ids(self, user_id: int, **filter_params) -> List[str]:
        pass

    # ------------------------ Get Enterprise resource --------------------- #
    @abstractmethod
    def get_enterprise_by_id(self, enterprise_id: str) -> Optional[Enterprise]:
        pass

    @abstractmethod
    def get_enterprise_avatar_url_by_id(self, enterprise_id: str) -> Optional[str]:
        pass

    # ------------------------ Create Enterprise resource --------------------- #
    @abstractmethod
    def create_enterprise(self, enterprise_create_data: Dict) -> Enterprise:
        pass

    # ------------------------ Update Enterprise resource --------------------- #
    @abstractmethod
    def update_enterprise(self, enterprise_id: str, enterprise_update_data) -> Optional[Enterprise]:
        pass

    # ------------------------ Delete EnterpriseMember resource --------------------- #
    @abstractmethod
    def delete_completely(self, enterprise: Enterprise):
        pass

    @abstractmethod
    def clear_data(self, enterprise: Enterprise):
        pass
