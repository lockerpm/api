from locker_server.api_orm.abstracts.quick_shares.quick_shares import AbstractQuickShareORM
from locker_server.shared.utils.app import now


class QuickShareORM(AbstractQuickShareORM):
    class Meta(AbstractQuickShareORM.Meta):
        swappable = 'LS_QUICK_SHARE_MODEL'
        db_table = 'cs_quick_shares'

    @classmethod
    def create(cls, **data):
        access_id = data.get("access_id") or cls.gen_access_id()
        is_public = data.get("is_public", True)
        quick_share = cls(
            access_id=access_id,
            cipher_id=data.get("cipher_id"),
            creation_date=data.get("creation_date") or now(),
            revision_date=data.get("revision_date") or now(),
            type=data.get("type"),
            data=data.get("data"),
            key=data.get("key"),
            password=data.get("password"),
            each_email_access_count=data.get("each_email_access_count"),
            max_access_count=data.get("max_access_count"),
            expiration_date=data.get("expiration_date"),
            disabled=data.get("disabled", False),
            is_public=is_public,
            require_otp=data.get("require_otp", True)
        )
        quick_share.save()
        emails_data = data.get("emails") or []
        quick_share.quick_share_emails.model.create_multiple(quick_share, emails_data)
        return quick_share
