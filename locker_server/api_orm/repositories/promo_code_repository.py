from typing import Optional, List, NoReturn

from django.db.models import Q, Sum

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_promo_code_model
from locker_server.core.entities.payment.promo_code import PromoCode
from locker_server.core.repositories.promo_code_repository import PromoCodeRepository
from locker_server.shared.constants.transactions import MISSION_REWARD_PROMO_PREFIX
from locker_server.shared.utils.app import now

PromoCodeORM = get_promo_code_model()
ModelParser = get_model_parser()


class PromoCodeORMRepository(PromoCodeRepository):

    # ------------------------ List PromoCode resource ------------------- #
    def list_user_promo_codes(self, user_id: int) -> List[PromoCode]:
        promo_codes_orm = PromoCodeORM.objects.filter(
            only_user_id=user_id,
            valid=True, remaining_times__gt=0
        ).filter(
            Q(expired_time__isnull=True) | Q(expired_time__gt=now())
        ).order_by('-created_time')
        return [
            ModelParser.payment_parser().parse_promo_code(promo_code_orm=promo_code_orm)
            for promo_code_orm in promo_codes_orm
        ]

    def list_user_generated_promo_codes(self, user_id: int) -> List[PromoCode]:
        promo_codes_orm = PromoCodeORM.objects.filter(
            only_user_id=user_id,
            code__startswith=MISSION_REWARD_PROMO_PREFIX,
            valid=True,
            remaining_times__gt=0
        ).filter(
            Q(expired_time__isnull=True) | Q(expired_time__gt=now())
        ).order_by('-created_time')
        return [
            ModelParser.payment_parser().parse_promo_code(promo_code_orm=promo_code_orm)
            for promo_code_orm in promo_codes_orm
        ]

    # ------------------------ Get PromoCode resource --------------------- #
    def get_promo_code_by_id(self, promo_code_id: str) -> Optional[PromoCode]:
        pass

    def get_used_promo_code_value(self, user_id: int) -> int:
        used_promo_code_value = PromoCodeORM.objects.filter(
            only_user_id=user_id,
            code__startswith=MISSION_REWARD_PROMO_PREFIX
        ).filter(
            Q(expired_time__isnull=True) | Q(expired_time__lt=now()) | Q(remaining_times=0)
        ).aggregate(Sum('value')).get("value__sum") or 0
        return used_promo_code_value

    # ------------------------ Create PromoCode resource --------------------- #
    def create_promo_code(self, promo_code_create_data) -> PromoCode:
        promo_code_orm = PromoCodeORM.create(**promo_code_create_data)
        return ModelParser.payment_parser().parse_promo_code(promo_code_orm=promo_code_orm)

    # ------------------------ Update PromoCode resource --------------------- #

    # ------------------------ Delete PromoCode resource --------------------- #
    def delete_promo_code_by_id(self, promo_code_id: str) -> bool:
        try:
            promo_code_orm = PromoCodeORM.objects.get(id=promo_code_id)
        except PromoCodeORM.DoesNotExist:
            return False
        promo_code_orm.delete()
        return True

    def delete_old_promo_code(self, user_id: int, exclude_promo_code_id: str) -> NoReturn:
        PromoCodeORM.objects.filter(
            only_user_id=user_id,
            code__startswith=MISSION_REWARD_PROMO_PREFIX,
            expired_time__gt=now(),
            remaining_times__gt=0
        ).exclude(id=exclude_promo_code_id).delete()
