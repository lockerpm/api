import os
from typing import Optional, List, Dict
import stripe
import stripe.error

from django.db.models import F, OuterRef, Subquery, FloatField, CharField

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models import CustomerORM
from locker_server.api_orm.models.wrapper import get_payment_model, get_promo_code_model, get_user_model, \
    get_user_plan_model, get_plan_model
from locker_server.core.entities.payment.payment import Payment
from locker_server.core.entities.payment.promo_code import PromoCode
from locker_server.core.repositories.payment_repository import PaymentRepository
from locker_server.shared.constants.transactions import *
from locker_server.shared.utils.app import now, random_n_digit

PaymentORM = get_payment_model()
UserORM = get_user_model()
PromoCodeORM = get_promo_code_model()
PMUserPlanORM = get_user_plan_model()
PMPlanORM = get_plan_model()
ModelParser = get_model_parser()


class PaymentORMRepository(PaymentRepository):
    @staticmethod
    def _get_payment_orm(payment_id: str) -> Optional[PaymentORM]:
        try:
            return PaymentORM.objects.get(payment_id=payment_id)
        except PaymentORM.DoesNotExist:
            return None

    @staticmethod
    def _get_user_orm(user_id: int) -> Optional[UserORM]:
        try:
            return UserORM.objects.get(user_id=user_id)
        except UserORM.DoesNotExist:
            return None

    @staticmethod
    def _get_promo_code_orm(promo_code_id: str) -> Optional[PromoCodeORM]:
        try:
            return PromoCodeORM.objects.get(id=promo_code_id)
        except PromoCodeORM.DoesNotExist:
            return None

    @staticmethod
    def _get_current_plan_orm(user_id: int) -> PMUserPlanORM:
        user_orm = UserORM.objects.get(user_id=user_id)
        try:
            user_plan_orm = user_orm.pm_user_plan
        except (ValueError, AttributeError):
            user_plan_orm = PMUserPlanORM.update_or_create(user=user_orm)
        return user_plan_orm

    # ------------------------ List Payment resource ------------------- #
    def list_all_invoices(self, **filter_params) -> List[Payment]:
        payments_orm = PaymentORM.objects.filter().order_by('-created_time')
        from_param = filter_params.get("from")
        to_param = filter_params.get("to")
        status_param = filter_params.get("status")
        payment_method_param = filter_params.get("payment_method")
        user_id_param = filter_params.get("user_id")
        enterprise_id_param = filter_params.get("enterprise_id")
        if from_param:
            payments_orm = payments_orm.filter(created_time__lte=from_param)
        if to_param:
            payments_orm = payments_orm.filter(created_time__gt=to_param)
        if status_param:
            payments_orm = payments_orm.filter(status=status_param)
        if payment_method_param:
            payments_orm = payments_orm.filter(payment_method=payment_method_param)
        if user_id_param:
            payments_orm = payments_orm.filter(user_id=user_id_param)
        if enterprise_id_param:
            payments_orm = payments_orm.filter(enterprise_id=enterprise_id_param)

        payments_orm = payments_orm.select_related('user')
        payments = []
        for payment_orm in payments_orm:
            payments.append(ModelParser.payment_parser().parse_payment(payment_orm=payment_orm))
        return payments

    def list_invoices_by_user(self, user_id: int, **filter_params) -> List[Payment]:
        payments_orm = PaymentORM.objects.filter(user_id=user_id).order_by('-created_time')
        from_param = filter_params.get("from")
        to_param = filter_params.get("to")
        if from_param:
            payments_orm = payments_orm.filter(created_time__lte=from_param)
        if to_param:
            payments_orm = payments_orm.filter(created_time__gt=to_param)

        payments = []
        for payment_orm in payments_orm:
            payments.append(ModelParser.payment_parser().parse_payment(payment_orm=payment_orm))
        return payments

    def list_feedback_after_subscription(self, after_days: int = 30) -> List[Dict]:
        payments_orm = PaymentORM.objects.filter(
            user_id=OuterRef("user_id"), total_price__gt=0,
            status=PAYMENT_STATUS_PAID
        ).order_by('created_time')
        users_feedback = UserORM.objects.filter(activated=True).annotate(
            first_payment_date=Subquery(payments_orm.values('created_time')[:1], output_field=FloatField()),
            first_payment_plan=Subquery(payments_orm.values('plan')[:1], output_field=CharField()),
        ).exclude(first_payment_date__isnull=True).filter(
            first_payment_date__gte=now() - after_days * 86400,
            first_payment_date__lt=now() - (after_days-1) * 86400
        ).values('user_id', 'first_payment_plan')
        return users_feedback

    # ------------------------ Get Payment resource --------------------- #
    def is_blocked_by_source(self, user_id: int, utm_source: str) -> bool:
        if utm_source in LIST_UTM_SOURCE_PROMOTIONS and PaymentORM.objects.filter(
                user_id=user_id, status=PAYMENT_STATUS_PAID
        ).exists() is False:
            return True
        return False

    def get_by_user_id(self, user_id: int, payment_id: str) -> Optional[Payment]:
        payment_orm = self._get_payment_orm(payment_id=payment_id)
        if not payment_orm or payment_orm.user_id != user_id:
            return None
        return ModelParser.payment_parser().parse_payment(payment_orm=payment_orm)

    def get_by_payment_id(self, payment_id: str) -> Optional[Payment]:
        payment_orm = self._get_payment_orm(payment_id=payment_id)
        if not payment_orm:
            return None
        return ModelParser.payment_parser().parse_payment(payment_orm=payment_orm)

    def get_by_mobile_invoice_id(self, mobile_invoice_id: str) -> Optional[Payment]:
        payment_orm = PaymentORM.objects.filter(mobile_invoice_id=mobile_invoice_id).first()
        return ModelParser.payment_parser().parse_payment(payment_orm=payment_orm) if payment_orm else None

    def get_by_stripe_invoice_id(self, stripe_invoice_id: str) -> Optional[Payment]:
        payment_orm = PaymentORM.objects.filter(stripe_invoice_id=stripe_invoice_id).first()
        return ModelParser.payment_parser().parse_payment(payment_orm=payment_orm) if payment_orm else None

    def get_by_banking_code(self, code: str) -> Optional[Payment]:
        try:
            payment_orm = PaymentORM.objects.get(code=code)
            return ModelParser.payment_parser().parse_payment(payment_orm=payment_orm)
        except PaymentORM.DoesNotExist:
            return None

    def check_saas_promo_code(self, user_id: int, code: str) -> Optional[PromoCode]:
        user_orm = self._get_user_orm(user_id=user_id)
        if not user_orm:
            return None
        promo_code_orm = PromoCodeORM.check_saas_valid(value=code, current_user=user_orm)
        if not promo_code_orm:
            return None
        return ModelParser.payment_parser().parse_promo_code(promo_code_orm=promo_code_orm)

    def check_promo_code(self, user_id: int, code: str, new_duration: str = None,
                         new_plan: str = None) -> Optional[PromoCode]:
        user_orm = self._get_user_orm(user_id=user_id)
        if not user_orm:
            return None
        promo_code_orm = PromoCodeORM.check_valid(
            value=code, current_user=user_orm, new_duration=new_duration, new_plan=new_plan
        )
        if not promo_code_orm:
            return None
        return ModelParser.payment_parser().parse_promo_code(promo_code_orm=promo_code_orm)

    def count_referral_payments(self, referral_user_ids: List[int]) -> int:
        return PaymentORM.objects.filter(
            status__in=[PAYMENT_STATUS_PAID], user_id__in=referral_user_ids
        ).count()

    # ------------------------ Create Payment resource --------------------- #
    def create_payment(self, **payment_data) -> Optional[Payment]:
        payment_orm = PaymentORM.create(**payment_data)
        # Set promo code and customer
        promo_code = payment_data.get("promo_code", None)
        payment_orm = self.__set_promo_code(payment_orm=payment_orm, promo_code=promo_code)
        # Set customer
        customer = payment_data.get('customer', None)
        payment_orm = self.__set_customer(payment_orm=payment_orm, customer=customer)
        # Create payment items
        payment_orm = self.__set_payment_items(payment_orm, **payment_data)
        # Set total price
        total_price = payment_data.get("total_price")
        if total_price is None:
            payment_orm = self.__set_total_price(payment_orm)
        else:
            payment_orm.total_price = total_price
            payment_orm.save()
        # Set banking code
        payment_orm = self.__set_banking_code(payment_orm=payment_orm, bank_id=payment_data.get("bank_id"))

        return ModelParser.payment_parser().parse_payment(payment_orm=payment_orm)

    @staticmethod
    def __set_promo_code(payment_orm: PaymentORM, promo_code: str = None):
        if promo_code is None:
            payment_orm.promo_code = None
        else:
            try:
                promo_orm = PromoCodeORM.objects.get(id=promo_code)
                payment_orm.promo_code = promo_orm
                promo_orm.remaining_times = F('remaining_times') - 1
                promo_orm.save()
            except PromoCodeORM.DoesNotExist:
                payment_orm.promo_code = None
        payment_orm.save()
        return payment_orm

    @staticmethod
    def __set_customer(payment_orm: PaymentORM, customer=None):
        if customer is None:
            payment_orm.customer = None
        else:
            new_customer = CustomerORM.create(**customer)
            payment_orm.customer = new_customer
        payment_orm.save()
        return payment_orm

    @staticmethod
    def __set_payment_items(payment_orm: PaymentORM, **data):
        payments_items = data.get("payment_items", [])
        payment_orm.payment_items.model.create_multiple(payment_orm, *payments_items)
        return payment_orm

    @staticmethod
    def __set_total_price(payment_orm: PaymentORM):
        # Get total price without discount
        number = int(payment_orm.get_metadata().get("number_members", 1))
        plan_price = PMPlanORM.objects.get(alias=payment_orm.plan).get_price(
            duration=payment_orm.duration, currency=payment_orm.currency
        )
        payment_orm.total_price = plan_price * number
        # Get discount here
        if payment_orm.promo_code is not None:
            payment_orm.discount = payment_orm.promo_code.get_discount(
                payment_orm.total_price, duration=payment_orm.duration
            )
        # Finally, calc total price
        payment_orm.total_price = max(round(payment_orm.total_price - payment_orm.discount, 2), 0)
        payment_orm.save()
        return payment_orm

    @staticmethod
    def __set_banking_code(payment_orm: PaymentORM, bank_id=None):
        # Set banking code
        if payment_orm.payment_method == PAYMENT_METHOD_BANKING:
            payment_orm.code = "{}{}".format(BANKING_ID_PWD_MANAGER, 10000 + payment_orm.id)
            payment_orm.bank_id = bank_id
            payment_orm.save()
        return payment_orm

    def create_education_promo_code(self, user_id: int) -> Optional[PromoCode]:
        # The promo code will be expired in one year
        expired_time = int(now() + 365 * 86400)
        value = 100
        code = f"{EDUCATION_PROMO_PREFIX}{random_n_digit(n=12)}".upper()
        only_user_id = user_id
        promo_code_data = {
            "type": PROMO_PERCENTAGE,
            "expired_time": expired_time,
            "code": code,
            "value": value,
            "duration": 1,
            "number_code": 1,
            "description_en": "Locker PromoCode Reward",
            "description_vi": "Locker PromoCode Reward",
            "only_user_id": only_user_id,
            "only_period": DURATION_YEARLY,
            "only_plan": PLAN_TYPE_PM_PREMIUM,
        }
        promo_code_orm = PromoCodeORM.create(**promo_code_data)

        # Create on Stripe
        if os.getenv("PROD_ENV") in ["prod", "staging"]:
            try:
                stripe.Coupon.create(
                    duration='once',
                    id="{}_yearly".format(promo_code_orm.id),
                    percent_off=value,
                    name=code,
                    redeem_by=expired_time
                )
            except stripe.error.StripeError:
                promo_code_orm.delete()
                return None
        return ModelParser.payment_parser().parse_promo_code(promo_code_orm=promo_code_orm)

    # ------------------------ Update Payment resource --------------------- #
    def update_promo_code_remaining_times(self, promo_code: PromoCode, amount: int = 1) -> PromoCode:
        promo_code_orm = self._get_promo_code_orm(promo_code_id=promo_code.promo_code_id)
        promo_code_orm.remaining_times = F('remaining_times') - 1
        promo_code_orm.save()
        promo_code_orm.refresh_from_db()
        return ModelParser.payment_parser().parse_promo_code(promo_code_orm=promo_code_orm)

    def update_payment(self, payment: Payment, update_data) -> Payment:
        payment_orm = self._get_payment_orm(payment_id=payment.payment_id)
        payment_orm.total_price = update_data.get("total_price", payment_orm.total_price)
        payment_orm.discount = update_data.get("discount", payment_orm.discount)
        payment_orm.transaction_type = update_data.get("transaction_type", payment_orm.transaction_type)
        payment_orm.stripe_invoice_id = update_data.get("stripe_invoice_id", payment_orm.stripe_invoice_id)
        payment_orm.status = update_data.get("status", payment_orm.status)
        payment_orm.save()
        return ModelParser.payment_parser().parse_payment(payment_orm=payment_orm)

    def set_paid(self, payment: Payment) -> Payment:
        payment_orm = self._get_payment_orm(payment_id=payment.payment_id)
        payment_orm.status = PAYMENT_STATUS_PAID
        payment_orm.save()
        # Set paid
        payment.status = PAYMENT_STATUS_PAID
        return payment

    def set_past_due(self, payment: Payment, failure_reason=None) -> Payment:
        payment_orm = self._get_payment_orm(payment_id=payment.payment_id)
        payment_orm.failure_reason = failure_reason
        payment_orm.status = PAYMENT_STATUS_PAST_DUE
        payment_orm.save()
        # Set
        payment.failure_reason = failure_reason
        payment.status = PAYMENT_STATUS_PAST_DUE
        return payment

    def set_failed(self, payment: Payment, failure_reason=None):
        payment_orm = self._get_payment_orm(payment_id=payment.payment_id)
        payment_orm.failure_reason = failure_reason
        payment_orm.status = PAYMENT_STATUS_FAILED
        payment_orm.save()
        # Set
        payment.failure_reason = failure_reason
        payment.status = PAYMENT_STATUS_FAILED
        return payment

    # ------------------------ Delete Payment resource --------------------- #
