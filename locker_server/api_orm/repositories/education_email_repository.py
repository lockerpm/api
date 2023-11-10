from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.users.education_emails import EducationEmailORM
from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.education_email import EducationEmail
from locker_server.core.entities.user.user import User
from locker_server.core.repositories.education_email_repository import EducationEmailRepository


ModelParser = get_model_parser()


class EducationEmailORMRepository(EducationEmailRepository):
    @staticmethod
    def _get_education_email_orm(education_email_id) -> Optional[EducationEmailORM]:
        try:
            return EducationEmailORM.objects.get(id=education_email_id)
        except EducationEmailORM.DoesNotExist:
            return None

    # ------------------------ List EducationEmail resource ------------------- #

    # ------------------------ Get EducationEmail resource --------------------- #
    def emails_verified(self, emails: List[str]) -> bool:
        return EducationEmailORM.objects.filter(email__in=emails, verified=True).exists()

    def get_by_user_id(self, email: str, user_id: int) -> Optional[EducationEmail]:
        try:
            education_email_orm = EducationEmailORM.objects.get(user_id=user_id, email=email)
        except EducationEmailORM.DoesNotExist:
            return None
        return ModelParser.user_parser().parse_education_email(education_email_orm=education_email_orm)

    # ------------------------ Create EducationEmail resource --------------------- #

    # ------------------------ Update EducationEmail resource --------------------- #
    def update_or_create_education_email(self, user_id: int, education_email: str, education_type: str,
                                         university: str = "", verified: bool = False) -> EducationEmail:
        education_email_orm = EducationEmailORM.update_or_create(user_id, **{
            "email": education_email,
            "education_type": education_type,
            "university": university,
            "verified": verified
        })
        return ModelParser.user_parser().parse_education_email(education_email_orm=education_email_orm)

    def update_education_email(self, education_email: EducationEmail, update_data) -> EducationEmail:
        education_email_orm = self._get_education_email_orm(education_email_id=education_email.education_email_id)
        education_email_orm.promo_code = update_data.get("promo_code", education_email_orm.promo_code)
        education_email_orm.verified = update_data.get("verified", education_email_orm.verified)
        education_email_orm.verification_token = update_data.get(
            "verification_token", education_email_orm.verification_token
        )
        education_email_orm.save()
        return ModelParser.user_parser().parse_education_email(education_email_orm=education_email_orm)

    # ------------------------ Delete EducationEmail resource --------------------- #
