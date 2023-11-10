from abc import ABC, abstractmethod
from typing import List, Optional, NoReturn

from locker_server.core.entities.payment.promo_code import PromoCode


class PromoCodeRepository(ABC):

    # ------------------------ List PromoCode resource ------------------- #
    @abstractmethod
    def list_user_promo_codes(self, user_id: int) -> List[PromoCode]:
        pass

    @abstractmethod
    def list_user_generated_promo_codes(self, user_id: int) -> List[PromoCode]:
        pass

    # ------------------------ Get PromoCode resource --------------------- #
    @abstractmethod
    def get_promo_code_by_id(self, promo_code_id: str) -> Optional[PromoCode]:
        pass

    @abstractmethod
    def get_used_promo_code_value(self, user_id: int) -> int:
        pass

    # ------------------------ Create PromoCode resource --------------------- #
    @abstractmethod
    def create_promo_code(self, promo_code_create_data) -> PromoCode:
        pass

    # ------------------------ Update PromoCode resource --------------------- #

    # ------------------------ Delete PromoCode resource --------------------- #
    @abstractmethod
    def delete_promo_code_by_id(self, promo_code_id: str) -> bool:
        pass

    @abstractmethod
    def delete_old_promo_code(self, user_id: int, exclude_promo_code_id: str) -> NoReturn:
        pass
