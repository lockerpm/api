from locker_server.api_orm.abstracts.form_submissions.affiliate_submissions import AbstractAffiliateSubmissionORM


class AffiliateSubmissionORM(AbstractAffiliateSubmissionORM):
    class Meta(AbstractAffiliateSubmissionORM.Meta):
        db_table = 'cs_affiliate_submissions'
