from locker_server.api_orm.abstracts.payments.promo_code_types import AbstractPromoCodeTypeORM


class PromoCodeTypeORM(AbstractPromoCodeTypeORM):
    class Meta(AbstractPromoCodeTypeORM.Meta):
        swappable = 'LS_PROMO_CODE_TYPE_MODEL'
        db_table = 'cs_promo_code_types'
