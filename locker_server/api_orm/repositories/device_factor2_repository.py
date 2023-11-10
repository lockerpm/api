from typing import Optional, List, Dict

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.core.entities.factor2.device_factor2 import DeviceFactor2
from locker_server.api_orm.models.factor2.device_factor2 import DeviceFactor2ORM
from locker_server.core.repositories.device_factor2_repository import DeviceFactor2Repository

DeviceFactor2ORM = DeviceFactor2ORM
ModelParser = get_model_parser()


class DeviceFactor2ORMRepository(DeviceFactor2Repository):
    # ------------------------ List DeviceFactor2 resource ------------------- #
    def list_user_device_factor2s(self, user_id: int, **filter_params) -> List[DeviceFactor2]:
        pass

    # ------------------------ Get DeviceFactor2 resource --------------------- #
    def get_device_factor2_by_id(self, device_factor2_id: str) -> Optional[DeviceFactor2]:
        pass

    def get_device_factor2_by_method(self, user_id: int, method: str) -> DeviceFactor2:
        pass

    # ------------------------ Create DeviceFactor2 resource --------------------- #
    def create_device_factor2(self, device_factor2_create_data: Dict) -> DeviceFactor2:
        pass

    # ------------------------ Update DeviceFactor2 resource --------------------- #

    # ------------------------ Delete DeviceFactor2 resource --------------------- #
