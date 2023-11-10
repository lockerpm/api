from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import jwt
from django.conf import settings
from django.db.models import F

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_quick_share_model, get_quick_share_email_model
from locker_server.core.entities.quick_share.quick_share import QuickShare
from locker_server.core.entities.release.release import Release
from locker_server.core.repositories.quick_share_repository import QuickShareRepository
from locker_server.shared.constants.token import TOKEN_TYPE_QUICK_SHARE_ACCESS
from locker_server.shared.utils.app import now, diff_list

QuickShareORM = get_quick_share_model()
QuickShareEmailORM = get_quick_share_email_model()
ModelParser = get_model_parser()


class QuickShareORMRepository(QuickShareRepository):
    @staticmethod
    def _get_quick_share_orm(quick_share_id: str) -> Optional[QuickShareORM]:
        try:
            return QuickShareORM.objects.get(id=quick_share_id)
        except QuickShareORM.DoesNotExist:
            return None

    @staticmethod
    def validate_public_access_token(email, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get("token_type") != TOKEN_TYPE_QUICK_SHARE_ACCESS:
                return False
            if payload.get("email") != email:
                return False
            if payload.get("expired_time") < now():
                return False
            return True
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidAlgorithmError):
            return False

    # ------------------------ List QuickShare resource ------------------- #
    def list_quick_shares(self, parse_emails=True, **filter_params) -> List[QuickShare]:
        quick_shares_orm = QuickShareORM.objects.all().order_by('-creation_date')
        cipher_ids_param = filter_params.get("cipher_ids")
        if cipher_ids_param is not None:
            quick_shares_orm = quick_shares_orm.filter(cipher_id__in=cipher_ids_param)
        quick_shares_orm = quick_shares_orm.prefetch_related('quick_share_emails')
        return [ModelParser.quick_share_parser().parse_quick_share(
            quick_share_orm=q, parse_emails=parse_emails
        ) for q in quick_shares_orm]

    # ------------------------ Get QuickShare resource --------------------- #
    def get_by_id(self, quick_share_id: str) -> Optional[QuickShare]:
        quick_share_orm = self._get_quick_share_orm(quick_share_id=quick_share_id)
        if not quick_share_orm:
            return None
        return ModelParser.quick_share_parser().parse_quick_share(quick_share_orm=quick_share_orm)

    def get_by_access_id(self, access_id: str, parse_emails=True) -> Optional[QuickShare]:
        try:
            quick_share_orm = QuickShareORM.objects.get(access_id=access_id)
            return ModelParser.quick_share_parser().parse_quick_share(
                quick_share_orm=quick_share_orm, parse_emails=parse_emails
            )
        except QuickShareORM.DoesNotExist:
            return None

    def check_valid_access(self, quick_share: QuickShare, email: str = None, code: str = None,
                           token: str = None) -> bool:
        if quick_share.disabled is True:
            return False
        if quick_share.is_public is False:
            try:
                quick_share_email_orm = QuickShareEmailORM.objects.get(
                    email=email, quick_share_id=quick_share.quick_share_id
                )
            except QuickShareEmailORM.DoesNotExist:
                return False
            if quick_share_email_orm.max_access_count and \
                    quick_share_email_orm.access_count >= quick_share_email_orm.max_access_count:
                return False
            if not code and not token:
                return False
            if code and (quick_share_email_orm.code != code or quick_share_email_orm.code_expired_time < now()):
                return False
            if token and self.validate_public_access_token(email=quick_share_email_orm.email, token=token) is False:
                return False
        if quick_share.max_access_count and quick_share.access_count >= quick_share.max_access_count:
            return False
        if quick_share.expiration_date and quick_share.expiration_date < now():
            return False
        return True

    def check_email_access(self, quick_share: QuickShare, email: str = None) -> bool:
        quick_share_email_orm = None
        if email:
            try:
                quick_share_email_orm = QuickShareEmailORM.objects.get(
                    email=email, quick_share_id=quick_share.quick_share_id
                )
            except QuickShareEmailORM.DoesNotExist:
                pass

        if quick_share.is_public is True or (quick_share_email_orm and quick_share_email_orm.check_access() is True):
            return True
        return False

    # ------------------------ Create QuickShare resource --------------------- #
    def create_quick_share(self, **quick_share_data) -> QuickShare:
        quick_share_orm = QuickShareORM.create(**quick_share_data)
        return ModelParser.quick_share_parser().parse_quick_share(quick_share_orm=quick_share_orm)

    def generate_public_access_token(self, quick_share: QuickShare, email: str) -> Tuple:
        expired_time = now() + 30 * 86400
        payload = {
            "email": email,
            "created_time": now(),
            "expired_time": expired_time,
            "access_id": quick_share.access_id,
            "token_type": TOKEN_TYPE_QUICK_SHARE_ACCESS
        }
        token_value = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return token_value, expired_time

    # ------------------------ Update QuickShare resource --------------------- #
    def update_quick_share(self, quick_share_id: str, **quick_share_data) -> Optional[QuickShare]:
        quick_share_orm = self._get_quick_share_orm(quick_share_id=quick_share_id)
        if not quick_share_orm:
            return None
        quick_share_orm.revision_date = now()
        quick_share_orm.data = quick_share_data.get("data") or quick_share_orm.data
        quick_share_orm.key = quick_share_data.get("key") or quick_share_orm.key
        quick_share_orm.password = quick_share_data.get("password") or quick_share_orm.password
        quick_share_orm.max_access_count = quick_share_data.get("max_access_count") or quick_share_orm.max_access_count
        quick_share_orm.expiration_date = quick_share_data.get("expiration_date") or quick_share_orm.expiration_date
        quick_share_orm.is_public = quick_share_data.get("is_public") or quick_share_orm.is_public
        quick_share_orm.disabled = quick_share_data.get("disabled") or quick_share_orm.disabled
        quick_share_orm.require_otp = quick_share_data.get("require_otp") or quick_share_orm.require_otp
        quick_share_orm.save()

        quick_share_emails = list(quick_share_orm.quick_share_emails.values_list('email', flat=True))
        emails_data = quick_share_data.get("emails", [])
        emails = [email_data.get("email") for email_data in emails_data]
        removed_emails = diff_list(quick_share_emails, emails)
        added_emails = diff_list(emails, quick_share_emails)
        if removed_emails:
            quick_share_orm.quick_share_emails.filter(email__in=removed_emails).delete()
        if added_emails:
            added_emails_data = [{"email": e} for e in added_emails]
            quick_share_orm.quick_share_emails.model.create_multiple(quick_share_orm, added_emails_data)

        return ModelParser.quick_share_parser().parse_quick_share(quick_share_orm=quick_share_orm)

    def update_access_count(self, quick_share_id: str, amount: int = 1, email: str = None) -> Optional[QuickShare]:
        quick_share_orm = self._get_quick_share_orm(quick_share_id=quick_share_id)
        if not quick_share_orm:
            return None
        quick_share_orm.access_count = F('access_count') + amount
        quick_share_orm.revision_date = now()
        quick_share_orm.save()
        quick_share_orm.refresh_from_db()
        if email:
            try:
                quick_share_email = quick_share_orm.quick_share_emails.get(email=email)
                quick_share_email.clear_code()
                quick_share_email.access_count = F('access_count') + 1
                quick_share_email.save()
            except QuickShareEmailORM.DoesNotExist:
                pass
        return ModelParser.quick_share_parser().parse_quick_share(quick_share_orm=quick_share_orm)

    def set_email_otp(self, quick_share_id: str, email: str) -> Optional[str]:
        try:
            quick_share_email_orm = QuickShareEmailORM.objects.get(email=email, quick_share_id=quick_share_id)
            quick_share_email_orm.clear_code()
            quick_share_email_orm.access_count = F('access_count') + 1
            quick_share_email_orm.save()
        except QuickShareEmailORM.DoesNotExist:
            return None
        quick_share_email_orm.set_random_code()
        return quick_share_email_orm.code

    # ------------------------ Delete QuickShare resource --------------------- #
    def delete_quick_share(self, quick_share_id: str):
        quick_share_orm = self._get_quick_share_orm(quick_share_id=quick_share_id)
        if not quick_share_orm:
            return None
        quick_share_orm.delete()
