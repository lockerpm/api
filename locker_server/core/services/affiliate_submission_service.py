from typing import List, Optional

from locker_server.core.entities.form_submission.affiliate_submission import AffiliateSubmission
from locker_server.core.exceptions.affiliate_submission_exception import AffiliateSubmissionDoesNotExistException
from locker_server.core.exceptions.country_exception import CountryDoesNotExistException
from locker_server.core.repositories.affiliate_submission_repository import AffiliateSubmissionRepository
from locker_server.core.repositories.country_repository import CountryRepository


class AffiliateSubmissionService:
    """
    This class represents Use Cases related affiliate submission
    """

    def __init__(self, affiliate_submission_repository: AffiliateSubmissionRepository,
                 country_repository: CountryRepository):
        self.affiliate_submission_repository = affiliate_submission_repository
        self.country_repository = country_repository

    def list_affiliate_submissions(self, **filters) -> List[AffiliateSubmission]:
        return self.affiliate_submission_repository.list_affiliate_submissions(**filters)

    def get_affiliate_submission_by_id(self, affiliate_submission_id: str) -> Optional[AffiliateSubmission]:
        affiliate_submission = self.affiliate_submission_repository.get_affiliate_submission_by_id(
            affiliate_submission_id=affiliate_submission_id
        )
        if not affiliate_submission:
            raise AffiliateSubmissionDoesNotExistException
        return affiliate_submission

    def create_affiliate_submission(self, affiliate_submission_create_data) -> AffiliateSubmission:
        country_name = affiliate_submission_create_data.get("country", "")
        if country_name:
            country = self.country_repository.get_country_by_name(country_name=country_name)
            if not country:
                raise CountryDoesNotExistException
        affiliate_submission = self.affiliate_submission_repository.create_affiliate_submission(
            affiliate_submission_create_data=affiliate_submission_create_data
        )
        return affiliate_submission

    def update_affiliate_submission(self, affiliate_submission_id: str,
                                    affiliate_submission_update_data) -> Optional[AffiliateSubmission]:
        updated_affiliate_submission = self.affiliate_submission_repository.update_affiliate_submission(
            affiliate_submission_id=affiliate_submission_id,
            affiliate_submission_update_data=affiliate_submission_update_data
        )
        if not updated_affiliate_submission:
            raise AffiliateSubmissionDoesNotExistException
        return updated_affiliate_submission

    def delete_affiliate_submission(self, affiliate_submission_id: str) -> bool:
        deleted_affiliate_submission = self.affiliate_submission_repository.delete_affiliate_submission_by_id(
            affiliate_submission_id=affiliate_submission_id
        )
        if not deleted_affiliate_submission:
            raise AffiliateSubmissionDoesNotExistException
        return deleted_affiliate_submission
