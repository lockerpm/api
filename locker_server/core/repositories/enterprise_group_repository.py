from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.enterprise.group.group import EnterpriseGroup


class EnterpriseGroupRepository(ABC):
    # ------------------------ List EnterpriseGroup resource ------------------- #
    @abstractmethod
    def list_enterprise_groups(self, **filters) -> List[EnterpriseGroup]:
        pass

    @abstractmethod
    def list_active_user_enterprise_group_ids(self, user_id: int) -> List[str]:
        pass

    # ------------------------ Get EnterpriseGroup resource --------------------- #
    @abstractmethod
    def get_by_id(self, enterprise_group_id: str) -> Optional[EnterpriseGroup]:
        pass

    # ------------------------ Create EnterpriseGroup resource --------------------- #
    @abstractmethod
    def create_enterprise_group(self, enterprise_group_create_data: Dict) -> EnterpriseGroup:
        pass

    # ------------------------ Update EnterpriseGroup resource --------------------- #
    @abstractmethod
    def update_enterprise_group(self, enterprise_group_id: str, enterprise_group_update_data: Dict) \
            -> Optional[EnterpriseGroup]:
        pass

    # ------------------------ Delete EnterpriseGroup resource --------------------- #
    @abstractmethod
    def delete_enterprise_group_by_id(self, enterprise_group_id: str) -> bool:
        pass
