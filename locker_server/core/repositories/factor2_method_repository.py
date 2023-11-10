from typing import Optional, List, Dict
from abc import ABC, abstractmethod

from locker_server.core.entities.factor2.factor2_method import Factor2Method


class Factor2MethodRepository(ABC):
    # ------------------------ List Factor2Method resource ------------------- #
    @abstractmethod
    def list_user_factor2_methods(self, user_id: int, **filter_params) -> List[Factor2Method]:
        pass

    # ------------------------ Get Factor2Method resource --------------------- #
    @abstractmethod
    def get_factor2_method_by_id(self, factor2_method_id: str) -> Optional[Factor2Method]:
        pass

    @abstractmethod
    def get_factor2_method_by_method(self, user_id: int, method: str) -> Factor2Method:
        pass

    # ------------------------ Create Factor2Method resource --------------------- #
    @abstractmethod
    def create_factor2_method(self, factor2_method_create_data: Dict) -> Factor2Method:
        pass

    @abstractmethod
    def create_activate_code_by_method(self, user_id: int, method: str, new_code: bool) -> Factor2Method:
        pass

    # ------------------------ Update Factor2Method resource --------------------- #
    @abstractmethod
    def update_factor2_method(self, factor2_method_id: str, factor2_method_update_data: Dict) -> Factor2Method:
        pass

    @abstractmethod
    def disable_factor2_by_user(self, user_id: int):
        pass
    # ------------------------ Delete Factor2Method resource --------------------- #
