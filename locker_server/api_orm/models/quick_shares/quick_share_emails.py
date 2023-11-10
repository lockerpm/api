from locker_server.api_orm.abstracts.quick_shares.quick_share_emails import AbstractQuickShareEmailORM
from locker_server.shared.utils.app import now


class QuickShareEmailORM(AbstractQuickShareEmailORM):
    class Meta(AbstractQuickShareEmailORM.Meta):
        swappable = 'LS_QUICK_SHARE_EMAIL_MODEL'
        db_table = 'cs_quick_share_emails'

    @classmethod
    def create_multiple(cls, quick_share, emails_data):
        quick_share_emails_obj = []
        for email_data in emails_data:
            quick_share_emails_obj.append(
                cls(
                    quick_share=quick_share,
                    email=email_data.get("email"),
                    code=email_data.get("code"),
                    code_expired_time=email_data.get("code_expired_time"),
                    creation_date=email_data.get("creation_date", now()),
                    max_access_count=email_data.get("max_access_count"),
                    access_count=email_data.get("access_count", 0)
                )
            )
        cls.objects.bulk_create(quick_share_emails_obj, ignore_conflicts=True, batch_size=50)