from locker_server.core.exceptions.payment_exception import CurrentPlanIsEnterpriseException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.repositories.payment_repository import PaymentRepository
from locker_server.core.repositories.user_plan_repository import UserPlanRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.transactions import *
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY
from locker_server.shared.utils.app import now


class MobilePaymentService:
    """
    This class represents Use Cases related Payment
    """
    def __init__(self, payment_repository: PaymentRepository,
                 user_plan_repository: UserPlanRepository,
                 user_repository: UserRepository):
        self.payment_repository = payment_repository
        self.user_plan_repository = user_plan_repository
        self.user_repository = user_repository

    def upgrade_plan(self, user_id: int,  plan_alias: str, duration: str = DURATION_MONTHLY, number_members: int = 1,
                     promo_code: str = None, paid: bool = True, failure_reason: str = None,
                     is_trial_period: bool = False, payment_platform: str = "",
                     scope: str = None, **metadata):
        user = self.user_repository.get_user_by_id(user_id=user_id)
        if not user:
            raise UserDoesNotExistException

        # Check confirm original id
        confirm_original_id = metadata.get("confirm_original_id")
        if confirm_original_id:
            mobile_original_id_registered = self.user_plan_repository.get_mobile_user_plan(confirm_original_id)
            # Downgrade plan of the existed mobile original id
            if mobile_original_id_registered and mobile_original_id_registered.user.user_id != user.user_id:
                self.user_plan_repository.update_plan(
                    user_id=mobile_original_id_registered.user.user_id, plan_type_alias=PLAN_TYPE_PM_FREE, scope=scope
                )

        mobile_original_id = metadata.get("mobile_original_id")
        family_members = list(metadata.get("family_members", []))
        new_payment_data = {
            "user_id": user.user_id,
            "description": metadata.get("description", ""),
            "plan": plan_alias,
            "duration": duration,
            "promo_code": promo_code,
            "currency": metadata.get("currency", CURRENCY_USD),
            "payment_method": PAYMENT_METHOD_MOBILE,
            "mobile_invoice_id": metadata.get("mobile_invoice_id"),
            "metadata": {
                "platform": metadata.get("platform"),
                "mobile_invoice_id": metadata.get("mobile_invoice_id"),
                "mobile_original_id": mobile_original_id,
                "user_id": user.user_id,
                "scope": scope,
                "family_members": family_members,
            }
        }
        new_payment = self.payment_repository.create_payment(**new_payment_data)
        if paid:
            new_payment = self.payment_repository.set_paid(payment=new_payment)

        # Set pm mobile subscription
        self.user_plan_repository.get_user_plan(user_id=user_id)
        self.user_plan_repository.update_user_plan_by_id(user_plan_id=user_id, user_plan_update_data={
            "pm_mobile_subscription": mobile_original_id
        })

        # Upgrade new plan
        subscription_metadata = {
            "start_period": metadata.get("start_period"),
            "end_period": metadata.get("end_period"),
            "promo_code": new_payment.promo_code,
            "family_members": family_members,
        }
        self.user_plan_repository.update_plan(
            user_id=new_payment.user.user_id, plan_type_alias=new_payment.plan, duration=new_payment.duration,
            scope=scope, **subscription_metadata
        )

        # Set default payment method
        send_trial_mail = False
        self.user_plan_repository.set_default_payment_method(user_id=user_id, payment_method=PAYMENT_METHOD_MOBILE)
        # if current_plan.is_personal_trial_applied() is False and is_trial_period is True:
        if is_trial_period is True:
            self.user_plan_repository.set_personal_trial_applied(user_id=user_id, applied=True, platform="mobile")
            send_trial_mail = True
            # Update payment -> trial
            new_payment = self.payment_repository.update_payment(
                payment=new_payment, update_data={"total_price": 0, "discount": 0}
            )

        # Send mail
        if send_trial_mail is True:
            BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                func_name="trial_successfully", **{
                    "user_id": new_payment.user.user_id,
                    "plan": new_payment.plan,
                    "payment_method": new_payment.payment_method,
                    "duration": TRIAL_PERSONAL_DURATION_TEXT
                }
            )

        BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="pay_successfully", **{"payment": new_payment, "payment_platform": payment_platform}
        )
        return new_payment

    def mobile_renewal(self, status: str, plan_alias: str, duration: str = DURATION_MONTHLY, promo_code: str = None,
                       failure_reason: str = None, payment_platform: str = "",
                       scope: str = None, **metadata):
        mobile_original_id = metadata.get("mobile_original_id")
        user_plan = self.user_plan_repository.get_mobile_user_plan(pm_mobile_subscription=mobile_original_id)
        if not user_plan:
            raise UserDoesNotExistException
        user = user_plan.user

        # Check the invoice with mobile_invoice_id exists or not?
        mobile_payment = None
        mobile_invoice_id = metadata.get("mobile_invoice_id")
        if mobile_invoice_id:
            mobile_payment = self.payment_repository.get_by_mobile_invoice_id(mobile_invoice_id=mobile_invoice_id)
        if not mobile_payment:
            new_payment_data = {
                "user_id": user.user_id,
                "description": metadata.get("description", ""),
                "plan": plan_alias,
                "duration": duration,
                "promo_code": promo_code,
                "currency": metadata.get("currency", CURRENCY_USD),
                "payment_method": PAYMENT_METHOD_MOBILE,
                "mobile_invoice_id": mobile_invoice_id,
                "metadata": {
                    "platform": payment_platform,
                    "mobile_invoice_id": mobile_invoice_id,
                    "mobile_original_id": mobile_original_id,
                    "user_id": user.user_id,
                    "scope": scope,
                }
            }
            # Create new payment
            new_payment = self.payment_repository.create_payment(**new_payment_data)
        else:
            new_payment = mobile_payment

        # Set paid or not
        if status == PAYMENT_STATUS_PAID:
            # If this plan is canceled because the Personal Plan upgrade to Enterprise Plan => Not downgrade
            current_plan = self.user_plan_repository.get_user_plan(user_id=user.user_id)
            if self.user_plan_repository.is_update_personal_to_enterprise(
                current_plan=current_plan, new_plan_alias=new_payment.plan
            ) is True:
                raise CurrentPlanIsEnterpriseException
            # Upgrade new plan
            subscription_metadata = {
                "end_period": metadata.get("end_period"),
                "promo_code": new_payment.promo_code,
            }
            self.user_plan_repository.update_plan(
                user_id=new_payment.user.user_id, plan_type_alias=new_payment.plan, duration=new_payment.duration,
                scope=scope, **subscription_metadata
            )
            self.user_plan_repository.set_default_payment_method(
                user_id=user.user_id, payment_method=PAYMENT_METHOD_MOBILE
            )
            if new_payment.status != PAYMENT_STATUS_PAID:
                self.payment_repository.set_paid(payment=new_payment)
                # Send mail
                BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                    func_name="pay_successfully", **{
                        "payment": new_payment, "payment_platform": payment_platform.title()
                    }
                )
        elif status == PAYMENT_STATUS_PAST_DUE:
            self.payment_repository.set_past_due(payment=new_payment, failure_reason=failure_reason)
        else:
            self.payment_repository.set_failed(payment=new_payment, failure_reason=failure_reason)
            # Only Downgrade - Not set mobile_original_id is Null
            current_plan = self.user_plan_repository.get_user_plan(user_id=user.user_id)
            if self.user_plan_repository.is_update_personal_to_enterprise(
                current_plan=current_plan, new_plan_alias=new_payment.plan
            ) is True:
                raise CurrentPlanIsEnterpriseException
            old_plan = current_plan.pm_plan.alias
            if not self.user_plan_repository.is_family_member(current_plan.user.user_id):
                self.user_plan_repository.update_plan(
                    user_id=user.user_id, plan_type_alias=PLAN_TYPE_PM_FREE, scope=scope
                )
                # Notify downgrade here
                BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=True).run(
                    func_name="downgrade_plan", **{
                        "user_id": user.user_id, "old_plan": old_plan, "downgrade_time": now(),
                        "scope": scope, **{"payment_data": {}}
                    }
                )

        return new_payment

    def mobile_cancel_subscription(self, plan_alias: str, mobile_original_id: str, cancel_at_period_end: bool,
                                   end_period: float = None, scope: str = None):
        user_plan = self.user_plan_repository.get_mobile_user_plan(pm_mobile_subscription=mobile_original_id)
        if not user_plan:
            raise UserDoesNotExistException
        user = user_plan.user
        current_plan = self.user_plan_repository.get_user_plan(user_id=user.user_id)
        if self.user_plan_repository.is_update_personal_to_enterprise(
            current_plan=current_plan, new_plan_alias=plan_alias
        ) is True:
            raise CurrentPlanIsEnterpriseException
        self.user_plan_repository.update_user_plan_by_id(
            user_plan_id=user.user_id, user_plan_update_data={
                "cancel_at_period_end": cancel_at_period_end
            }
        )
        if cancel_at_period_end is True:
            # Notify cancel plan here
            # CHANGE LATER ...
            # BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=True).run(
            #     func_name="cancel_plan", **{
            #         "user_id": user.user_id, "old_plan": current_plan.get_plan_type_name(),
            #         "expired_date": current_plan.end_period,
            #     }
            # )
            pass

    def mobile_destroy_subscription(self, plan_alias: str, mobile_original_id: str, scope: str = None):
        user_plan = self.user_plan_repository.get_mobile_user_plan(pm_mobile_subscription=mobile_original_id)
        if not user_plan:
            raise UserDoesNotExistException
        user = user_plan.user
        current_plan = self.user_plan_repository.get_user_plan(user_id=user.user_id)
        payment_data = {}
        old_plan = current_plan.pm_plan.name
        if self.user_plan_repository.is_update_personal_to_enterprise(
            current_plan=current_plan, new_plan_alias=plan_alias
        ) is True:
            return old_plan

        if not self.user_plan_repository.is_family_member(user_id=current_plan.user.user_id):
            self.user_plan_repository.update_plan(
                user_id=user.user_id, plan_type_alias=PLAN_TYPE_PM_FREE, scope=scope
            )
            # Notify downgrade here
            BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=True).run(
                func_name="downgrade_plan", **{
                    "user_id": user.user_id, "old_plan": old_plan, "downgrade_time": now(),
                    "scope": scope, **{"payment_data": payment_data}
                }
            )

        return old_plan
