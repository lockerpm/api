from abc import ABC, abstractmethod
from typing import List, Optional

from locker_server.core.entities.form_submission.affiliate_submission import AffiliateSubmission


class AffiliateSubmissionRepository(ABC):

    # ------------------------ List AffiliateSubmission resource ------------------- #
    @abstractmethod
    def list_affiliate_submissions(self, **filters) -> List[AffiliateSubmission]:
        pass

    # ------------------------ Get AffiliateSubmission resource --------------------- #
    @abstractmethod
    def get_affiliate_submission_by_id(self, affiliate_submission_id: str) -> Optional[AffiliateSubmission]:
        pass

    # ------------------------ Create AffiliateSubmission resource --------------------- #
    @abstractmethod
    def create_affiliate_submission(self, affiliate_submission_create_data) -> Optional[AffiliateSubmission]:
        pass

    # ------------------------ Update AffiliateSubmission resource --------------------- #

    @abstractmethod
    def update_affiliate_submission(self, affiliate_submission_id: str,
                                    affiliate_submission_update_data) -> Optional[AffiliateSubmission]:
        pass

    # ------------------------ Delete AffiliateSubmission resource --------------------- #
    @abstractmethod
    def delete_affiliate_submission_by_id(self, affiliate_submission_id: str) -> bool:
        pass
