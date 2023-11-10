from locker_server.api_orm.model_parsers.wrapper_specific_model_parser import get_specific_model_parser
from locker_server.api_orm.models import *
from locker_server.core.entities.quick_share.quick_share import QuickShare
from locker_server.core.entities.quick_share.quick_share_email import QuickShareEmail


class QuickShareParser:
    @classmethod
    def parse_quick_share(cls, quick_share_orm: QuickShareORM, parse_emails=False) -> QuickShare:
        cipher_parser = get_specific_model_parser("CipherParser")

        if parse_emails:
            emails = quick_share_orm.quick_share_emails.values(
                'email', 'max_access_count', 'access_count', 'creation_date'
            )
        else:
            emails = []

        return QuickShare(
            quick_share_id=quick_share_orm.id,
            cipher=cipher_parser.parse_cipher(cipher_orm=quick_share_orm.cipher),
            access_id=quick_share_orm.access_id,
            creation_date=quick_share_orm.creation_date,
            revision_date=quick_share_orm.revision_date,
            deleted_date=quick_share_orm.deleted_date,
            quick_share_type=quick_share_orm.type,
            data=quick_share_orm.get_data(),
            key=quick_share_orm.key,
            password=quick_share_orm.password,
            each_email_access_count=quick_share_orm.each_email_access_count,
            max_access_count=quick_share_orm.max_access_count,
            access_count=quick_share_orm.access_count,
            expiration_date=quick_share_orm.expiration_date,
            disabled=quick_share_orm.disabled,
            is_public=quick_share_orm.is_public,
            require_otp=quick_share_orm.require_otp,
            emails=emails
        )

    @classmethod
    def parse_quick_share_email(cls, quick_share_email_orm: QuickShareEmailORM) -> QuickShareEmail:
        return QuickShareEmail(
            quick_share_email_id=quick_share_email_orm.id,
            creation_date=quick_share_email_orm.creation_date,
            email=quick_share_email_orm.email,
            code=quick_share_email_orm.code,
            code_expired_time=quick_share_email_orm.code_expired_time,
            max_access_count=quick_share_email_orm.max_access_count,
            access_count=quick_share_email_orm.access_count,
            quick_share=cls.parse_quick_share(quick_share_orm=quick_share_email_orm.quick_share)
        )
