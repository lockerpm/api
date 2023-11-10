from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.education_email import EducationEmail
from locker_server.core.entities.user.user import User


class EducationEmailRepository(ABC):
    # ------------------------ List EducationEmail resource ------------------- #

    # ------------------------ Get EducationEmail resource --------------------- #
    @abstractmethod
    def emails_verified(self, emails: List[str]) -> bool:
        pass

    @abstractmethod
    def get_by_user_id(self, email: str, user_id: int) -> Optional[EducationEmail]:
        pass

    # ------------------------ Create EducationEmail resource --------------------- #

    # ------------------------ Update EducationEmail resource --------------------- #
    @abstractmethod
    def update_or_create_education_email(self, user_id: int, education_email: str, education_type: str,
                                         university: str = "", verified: bool = False) -> EducationEmail:
        pass

    @abstractmethod
    def update_education_email(self, education_email: EducationEmail, update_data) -> EducationEmail:
        pass

    # ------------------------ Delete EducationEmail resource --------------------- #
