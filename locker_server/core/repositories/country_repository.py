from typing import List, Optional
from abc import ABC, abstractmethod

from locker_server.core.entities.payment.country import Country


class CountryRepository(ABC):
    # ------------------------ List Country resource ------------------- #
    @abstractmethod
    def list_countries(self, **filter_params) -> List[Country]:
        pass

    # ------------------------ Get Country resource --------------------- #
    @abstractmethod
    def get_country_by_code(self, country_code: str) -> Optional[Country]:
        pass

    @abstractmethod
    def get_country_by_name(self, country_name: str) -> Optional[Country]:
        pass

    # ------------------------ Create Country resource --------------------- #

    # ------------------------ Update Country resource --------------------- #

    # ------------------------ Delete Country resource --------------------- #
