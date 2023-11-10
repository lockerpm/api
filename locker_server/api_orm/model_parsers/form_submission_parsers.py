from locker_server.api_orm.models import AffiliateSubmissionORM
from locker_server.core.entities.form_submission.affiliate_submission import AffiliateSubmission


class FormSubmissionParser:
    @classmethod
    def parse_affiliate_submission(cls, affiliate_submission_orm: AffiliateSubmissionORM) -> AffiliateSubmission:
        return AffiliateSubmission(
            affiliate_submission_id=affiliate_submission_orm.id,
            created_time=affiliate_submission_orm.created_time,
            full_name=affiliate_submission_orm.full_name,
            email=affiliate_submission_orm.email,
            phone=affiliate_submission_orm.phone,
            company=affiliate_submission_orm.company,
            country=affiliate_submission_orm.country,
            status=affiliate_submission_orm.status,
        )
