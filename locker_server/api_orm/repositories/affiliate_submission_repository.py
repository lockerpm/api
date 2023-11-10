from typing import Optional, List

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_affiliate_submission_model
from locker_server.core.entities.form_submission.affiliate_submission import AffiliateSubmission
from locker_server.core.repositories.affiliate_submission_repository import AffiliateSubmissionRepository

AffiliateSubmissionORM = get_affiliate_submission_model()
ModelParser = get_model_parser()


class AffiliateSubmissionORMRepository(AffiliateSubmissionRepository):
    # ------------------------ List AffiliateSubmission resource ------------------- #
    def list_affiliate_submissions(self, **filters) -> List[AffiliateSubmission]:
        affiliate_submissions_orm = AffiliateSubmissionORM.objects.all().order_by('-created_time')
        q_param = filters.get("q")
        if q_param:
            affiliate_submissions_orm = affiliate_submissions_orm.filter(full_name__icontains=q_param.lower())
        return [
            ModelParser.form_submission_parser().parse_affiliate_submission(
                affiliate_submission_orm=affiliate_submission_orm
            )
            for affiliate_submission_orm in affiliate_submissions_orm
        ]

    # ------------------------ Get AffiliateSubmission resource --------------------- #
    def get_affiliate_submission_by_id(self, affiliate_submission_id: str) -> Optional[AffiliateSubmission]:
        try:
            affiliate_submission_orm = AffiliateSubmissionORM.objects.get(id=affiliate_submission_id)
        except AffiliateSubmissionORM.DoesNotExist:
            return None
        return ModelParser.form_submission_parser().parse_affiliate_submission(
            affiliate_submission_orm=affiliate_submission_orm
        )

    # ------------------------ Create AffiliateSubmission resource --------------------- #
    def create_affiliate_submission(self, affiliate_submission_create_data) -> Optional[AffiliateSubmission]:
        affiliate_submission_orm = AffiliateSubmissionORM.objects.create(**affiliate_submission_create_data)
        return ModelParser.form_submission_parser().parse_affiliate_submission(
            affiliate_submission_orm=affiliate_submission_orm
        )

    # ------------------------ Update AffiliateSubmission resource --------------------- #

    def update_affiliate_submission(self, affiliate_submission_id: str, affiliate_submission_update_data) \
            -> Optional[AffiliateSubmission]:
        try:
            affiliate_submission_orm = AffiliateSubmissionORM.objects.get(id=affiliate_submission_id)
        except AffiliateSubmissionORM.DoesNotExist:
            return None
        status = affiliate_submission_update_data.get("status", affiliate_submission_orm.status)
        affiliate_submission_orm.status = status
        affiliate_submission_orm.save()
        return ModelParser.form_submission_parser().parse_affiliate_submission(
            affiliate_submission_orm=affiliate_submission_orm
        )

    # ------------------------ Delete AffiliateSubmission resource --------------------- #
    def delete_affiliate_submission_by_id(self, affiliate_submission_id: str) -> bool:
        try:
            affiliate_submission_orm = AffiliateSubmissionORM.objects.get(id=affiliate_submission_id)
        except AffiliateSubmissionORM.DoesNotExist:
            return False
        affiliate_submission_orm.delete()
        return True
