from typing import List, Optional, Dict

import jwt

from locker_server.core.entities.payment.payment import Payment
from locker_server.core.entities.user.user import User
from locker_server.core.entities.user_plan.pm_plan import PMPlan
from locker_server.core.exceptions.enterprise_member_repository import EnterpriseMemberExistedException
from locker_server.core.exceptions.payment_exception import *
from locker_server.core.exceptions.plan_repository import PlanDoesNotExistException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.exceptions.user_plan_exception import *
from locker_server.core.repositories.cipher_repository import CipherRepository
from locker_server.core.repositories.education_email_repository import EducationEmailRepository
from locker_server.core.repositories.enterprise_member_repository import EnterpriseMemberRepository
from locker_server.core.repositories.payment_repository import PaymentRepository
from locker_server.core.repositories.plan_repository import PlanRepository
from locker_server.core.repositories.relay_repositories.relay_address_repository import RelayAddressRepository
from locker_server.core.repositories.user_plan_repository import UserPlanRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.relay_address import MAX_FREE_RElAY_DOMAIN
from locker_server.shared.constants.token import *
from locker_server.shared.constants.transactions import *
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY
from locker_server.shared.external_services.payment_method.payment_method_factory import PaymentMethodFactory
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.utils.app import now, convert_readable_date
from locker_server.shared.utils.student_email import is_academic


class PaymentService:
    """
    This class represents Use Cases related Payment
    """

    def __init__(self, payment_repository: PaymentRepository,
                 user_plan_repository: UserPlanRepository,
                 plan_repository: PlanRepository,
                 user_repository: UserRepository,
                 enterprise_member_repository: EnterpriseMemberRepository,
                 education_email_repository: EducationEmailRepository,
                 cipher_repository: CipherRepository,
                 relay_address_repository: RelayAddressRepository):
        self.payment_repository = payment_repository
        self.user_plan_repository = user_plan_repository
        self.plan_repository = plan_repository
        self.user_repository = user_repository
        self.enterprise_member_repository = enterprise_member_repository
        self.education_email_repository = education_email_repository
        self.cipher_repository = cipher_repository
        self.relay_address_repository = relay_address_repository

    def get_by_user_id(self, user_id: int, payment_id: str) -> Optional[Payment]:
        payment = self.payment_repository.get_by_user_id(
            user_id=user_id, payment_id=payment_id
        )
        if not payment:
            raise PaymentInvoiceDoesNotExistException
        return payment

    def get_by_payment_id(self, payment_id: str) -> Optional[Payment]:
        payment = self.payment_repository.get_by_payment_id(payment_id=payment_id)
        if not payment:
            raise PaymentInvoiceDoesNotExistException
        return payment

    def allow_upgrade_enterprise_trial(self, user_id: int):
        if self.enterprise_member_repository.is_in_enterprise(user_id=user_id):
            raise EnterpriseMemberExistedException
        current_plan = self.user_plan_repository.get_user_plan(user_id=user_id)
        if current_plan.enterprise_trial_applied is True:
            raise EnterpriseTrialAppliedException
        return current_plan

    def list_all_invoices(self, **filter_params) -> List[Payment]:
        return self.payment_repository.list_all_invoices(**filter_params)

    def list_user_invoices(self, user_id: int, **filter_params) -> List[Payment]:
        return self.payment_repository.list_invoices_by_user(user_id=user_id, **filter_params)

    def calc_payment(self, user_id: int, plan_alias: str, duration: str = DURATION_MONTHLY,
                     currency: str = CURRENCY_USD, number_members: int = 1, promo_code: str = None,
                     allow_trial: bool = True) -> Dict:
        """
        Calc total payment
        :param user_id: (int) The user id
        :param plan_alias: (str) Plan alias
        :param duration: (str) Duration of the plan
        :param currency: (str) Currency: VND/USD
        :param number_members: (str)
        :param promo_code: (str) promo value
        :param allow_trial: (bool)
        :return:
        """
        new_plan = self.plan_repository.get_plan_by_alias(alias=plan_alias)
        if not new_plan:
            raise PlanDoesNotExistException
        if new_plan.is_team_plan is False:
            number_members = 1
        current_plan = self.user_plan_repository.get_user_plan(user_id=user_id)
        utm_source = self.user_repository.get_from_cystack_id(user_id=user_id).get("utm_source")
        result = self.user_plan_repository.calc_update_price(
            current_plan=current_plan,
            new_plan=new_plan,
            new_duration=duration,
            new_quantity=number_members,
            currency=currency,
            promo_code=promo_code,
            allow_trial=allow_trial,
            utm_source=utm_source,
        )
        result["plan"] = new_plan.to_json()
        return result

    def calc_lifetime_payment_public(self, plan_alias: str, currency: str = CURRENCY_USD, promo_code: str = None,
                                     user=None):
        new_plan = self.plan_repository.get_plan_by_alias(alias=plan_alias)
        if not new_plan:
            raise PlanDoesNotExistException
        result = self.user_plan_repository.calc_lifetime_payment_public(
            new_plan=new_plan,
            currency=currency,
            promo_code=promo_code,
            user=user
        )
        result["plan"] = new_plan.to_json()
        return result

    def admin_upgrade_plan(self, user_id: int, plan_alias: str, end_period: float = None, scope: str = None):
        new_plan = self.plan_repository.get_plan_by_alias(alias=plan_alias)
        if not new_plan:
            raise PlanDoesNotExistException
        self.user_plan_repository.update_plan(user_id=user_id, plan_type_alias=plan_alias, scope=scope, **{
            "start_period": now(),
            "end_period": end_period
        })

    def upgrade_trial(self, user_id: int, trial_plan_alias: str, **plan_metadata):
        trial_plan = self.plan_repository.get_plan_by_alias(alias=trial_plan_alias)
        if not trial_plan:
            raise PlanDoesNotExistException
        self.user_plan_repository.update_plan(
            user_id=user_id, plan_type_alias=trial_plan_alias, duration=DURATION_MONTHLY, **plan_metadata
        )
        self.user_plan_repository.set_personal_trial_applied(user_id=user_id, applied=True, platform="web")

    def upgrade_trial_enterprise_by_code(self, token: str, secret_key: str, scope: str = None):
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidAlgorithmError):
            raise EnterpriseTrialCodeInvalidException
        user_id = payload.get("user_id")
        expired_time = payload.get("expired_time")
        token_type = payload.get("token_type")
        enterprise_name = payload.get("enterprise_name") or "My Enterprise"
        if token_type != TOKEN_TYPE_TRIAL_ENTERPRISE or (expired_time and expired_time < now()):
            raise EnterpriseTrialCodeInvalidException

        user = self.user_repository.get_user_by_id(user_id=user_id)
        if not user:
            raise UserDoesNotExistException

        current_plan = self.allow_upgrade_enterprise_trial(user_id=user.user_id)

        # Cancel immediately the Stripe subscription
        old_plan = current_plan.pm_plan.alias
        old_end_period = current_plan.end_period
        PaymentMethodFactory.get_method(
            user_plan=current_plan, scope=scope, payment_method=PAYMENT_METHOD_CARD
        ).cancel_immediately_recurring_subscription()

        plan_metadata = {
            "start_period": now(),
            "end_period": now() + TRIAL_TEAM_PLAN,
            "number_members": TRIAL_TEAM_MEMBERS,
            "enterprise_name": enterprise_name
        }
        if old_plan != PLAN_TYPE_PM_FREE and old_end_period:
            plan_metadata.update({
                "extra_time": max(old_end_period - now(), 0),
                "extra_plan": old_plan
            })

        self.user_plan_repository.update_plan(
            user_id=user_id, plan_type_alias=PLAN_TYPE_PM_ENTERPRISE, duration=DURATION_MONTHLY, scope=scope,
            **plan_metadata
        )
        self.user_plan_repository.set_enterprise_trial_applied(user_id=user_id, applied=True)
        self.user_plan_repository.set_default_payment_method(user_id=user_id, payment_method=PAYMENT_METHOD_CARD)

        return user

    def generate_trial_enterprise_code(self, user_id: int, secret_key: str,
                                       enterprise_name: str = "My Enterprise") -> str:
        self.allow_upgrade_enterprise_trial(user_id=user_id)
        payload = {
            "user_id": user_id,
            "plan": PLAN_TYPE_PM_ENTERPRISE,
            "enterprise_name": enterprise_name,
            "token_type": TOKEN_TYPE_TRIAL_ENTERPRISE,
            "expired_time": now() + TOKEN_EXPIRED_TIME_TRIAL_ENTERPRISE
        }
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        return token

    def upgrade_lifetime(self, user_id: int, code: str, scope: str = None):
        if self.enterprise_member_repository.is_in_enterprise(user_id=user_id):
            raise EnterpriseMemberExistedException
        saas_code = self.payment_repository.check_saas_promo_code(user_id=user_id, code=code)
        if not saas_code:
            raise PaymentPromoCodeInvalidException
        saas_plan_alias = saas_code.saas_plan or PLAN_TYPE_PM_LIFETIME
        plan = self.plan_repository.get_plan_by_alias(alias=saas_plan_alias)
        if not plan:
            CyLog.warning(**{"message": f"[!] Not found the saas plan of the {saas_code}"})
            plan = self.plan_repository.get_plan_by_alias(alias=PLAN_TYPE_PM_LIFETIME)

        current_plan = self.user_plan_repository.get_user_plan(user_id=user_id)

        if plan.alias == PLAN_TYPE_PM_LIFETIME_FAMILY:
            if self.user_plan_repository.is_family_member(user_id=user_id):
                raise PaymentFailedByUserInFamilyException
        else:
            if self.user_plan_repository.is_in_family_plan(user_plan=current_plan):
                raise PaymentFailedByUserInFamilyException

        # Update remaining times of the promo code
        saas_code = self.payment_repository.update_promo_code_remaining_times(promo_code=saas_code)
        # Avoid race conditions - Make sure that this code is still available
        if saas_code.remaining_times < 0:
            raise PaymentPromoCodeInvalidException

        # Cancel the current Free/Premium/Family
        # If new plan is family lifetime => Only cancel stripe subscription
        if plan.alias == PLAN_TYPE_PM_LIFETIME_FAMILY:
            if current_plan.pm_stripe_subscription:
                self.user_plan_repository.cancel_plan(user=current_plan.user, immediately=True)
        else:
            self.user_plan_repository.cancel_plan(user=current_plan.user, immediately=True)

        if saas_code.saas_market.lifetime_duration is None:
            saas_end_period = None
            upgrade_duration = DURATION_MONTHLY
        else:
            if current_plan.personal_trial_applied is False:
                saas_end_period = now() + saas_code.saas_market.lifetime_duration + TRIAL_PERSONAL_PLAN
                self.user_plan_repository.set_personal_trial_applied(user_id=user_id, applied=True, platform="web")
            else:
                saas_end_period = now() + saas_code.saas_market.lifetime_duration
            upgrade_duration = DURATION_YEARLY
        plan_metadata = {
            "start_period": now(),
            "end_period": saas_end_period
        }
        self.user_plan_repository.update_plan(
            user_id=user_id, plan_type_alias=plan.alias, duration=upgrade_duration, scope=scope, **plan_metadata
        )
        user = self.user_repository.update_user(user_id=user_id,
                                                user_update_data={"saas_source": saas_code.saas_market.name})

        if user.activated:
            if plan.alias in [PLAN_TYPE_PM_LIFETIME, PLAN_TYPE_PM_LIFETIME_FAMILY]:
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_locker_mail", **{
                        "user_ids": [user.user_id],
                        "job": "upgraded_to_lifetime_from_code",
                        "scope": scope,
                        "service_name": user.saas_source,
                    }
                )
            else:
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_locker_mail", **{
                        "user_ids": [user.user_id],
                        "job": "upgraded_from_code_promo",
                        "scope": scope,
                        "service_name": user.saas_source,
                        "plan": plan.name
                    }
                )

    def upgrade_three_promo(self, user_id: int, card, promo_code: str = None, scope: str = None):
        current_plan = self.user_plan_repository.get_user_plan(user_id=user_id)
        if current_plan.pm_plan.alias != PLAN_TYPE_PM_FREE:
            raise CurrentPlanDoesNotSupportOperatorException

        duration = DURATION_MONTHLY
        promo_code_obj = None
        if promo_code:
            promo_code_obj = self.payment_repository.check_promo_code(
                user_id=user_id, code=promo_code, new_duration=duration
            )
            if not promo_code_obj:
                raise PaymentPromoCodeInvalidException

        new_plan = self.plan_repository.get_plan_by_alias(alias=PLAN_TYPE_PM_PREMIUM)
        metadata = {
            "currency": CURRENCY_USD,
            "promo_code": promo_code_obj,
            "card": card,
            "billing_cycle_anchor": now() + 3 * 30 * 86400,  # Next 3 months
        }
        # Calc payment price of new plan
        promo_code_value = promo_code_obj.code if promo_code_obj else None
        calc_payment = self.user_plan_repository.calc_update_price(
            current_plan=current_plan,
            new_plan=new_plan,
            new_duration=duration,
            currency=CURRENCY_USD,
            promo_code=promo_code_value,
        )
        immediate_payment = calc_payment.get("immediate_payment")
        # Start payment here
        payment = PaymentMethodFactory.get_method(
            user_plan=current_plan, scope=scope, payment_method=PAYMENT_METHOD_CARD
        )
        payment_result = payment.upgrade_recurring_subscription(
            amount=immediate_payment, plan_type=new_plan.alias, coupon=promo_code_obj, duration=duration,
            **metadata
        )
        if payment_result.get("success") is True:
            self.user_plan_repository.set_default_payment_method(user_id=user_id, payment_method=PAYMENT_METHOD_CARD)
        return payment_result

    def upgrade_lifetime_public(self, user_id: int, card, plan_alias: str = PLAN_TYPE_PM_LIFETIME,
                                promo_code: str = None, scope: str = None):
        if self.enterprise_member_repository.is_in_enterprise(user_id=user_id):
            raise EnterpriseMemberExistedException

        promo_code_obj = None
        if promo_code:
            promo_code_obj = self.payment_repository.check_promo_code(
                user_id=user_id, code=promo_code, new_plan=plan_alias
            )
            if not promo_code_obj:
                raise PaymentPromoCodeInvalidException
        current_plan = self.user_plan_repository.get_user_plan(user_id=user_id)
        if current_plan.pm_plan.alias == plan_alias:
            raise PaymentFailedByUserInLifetimeException
        if plan_alias == PLAN_TYPE_PM_LIFETIME_FAMILY:
            if self.user_plan_repository.is_family_member(user_id=user_id):
                raise PaymentFailedByUserInFamilyException
        else:
            if self.user_plan_repository.is_in_family_plan(user_plan=current_plan):
                raise PaymentFailedByUserInFamilyException

        plan_obj = self.plan_repository.get_plan_by_alias(alias=plan_alias)
        plan_metadata = {
            "start_period": now(),
            "end_period": None,
            "card": card,
        }
        promo_code_value = promo_code_obj.code if promo_code_obj else None
        calc_payment = self.user_plan_repository.calc_lifetime_payment_public(
            new_plan=plan_obj,
            currency=CURRENCY_USD,
            promo_code=promo_code_value,
            user=current_plan.user
        )
        immediate_payment = calc_payment.get("immediate_payment")
        # Start payment here
        payment = PaymentMethodFactory.get_method(
            user_plan=current_plan, scope=scope, payment_method=PAYMENT_METHOD_CARD
        )
        payment_result = payment.onetime_payment(
            amount=immediate_payment, plan_type=plan_obj.alias, coupon=promo_code_obj, **plan_metadata

        )
        if payment_result.get("success") is True:
            self.user_plan_repository.update_user_plan_by_id(user_plan_id=user_id, user_plan_update_data={
                "extra_plan": None,
                "extra_time_value": 0
            })

            self.user_plan_repository.update_plan(
                user_id=user_id, plan_type_alias=plan_obj.alias,
                duration=DURATION_MONTHLY, scope=scope, **plan_metadata
            )
            # Cancel the current Stripe subscription: Free/Premium/Family
            self.user_plan_repository.cancel_plan(user=current_plan.user, immediately=True)
            # Make sure the plan is upgraded
            self.user_plan_repository.update_plan(
                user_id=user_id, plan_type_alias=plan_obj.alias,
                duration=DURATION_MONTHLY, scope=scope, **plan_metadata
            )

            # Set default payment method
            self.user_plan_repository.set_default_payment_method(user_id=user_id, payment_method=PAYMENT_METHOD_CARD)

            # Sending invoice mail if the payment successfully
            new_payment = self.payment_repository.get_by_payment_id(payment_id=payment_result.get("payment_id"))
            if new_payment:
                BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                    func_name="pay_successfully", **{"payment": new_payment}
                )

        return payment_result

    def upgrade_education_public(self, user_id: int, email: str, education_email: str = "",
                                 education_type: str = "student", university: str = "", scope: str = None,
                                 new_user: bool = False, user_fullname: str = "", username: str = "",
                                 locker_web_url: str = "", locker_id_url: str = ""):
        current_plan = self.user_plan_repository.get_user_plan(user_id=user_id)
        user = current_plan.user
        if self.enterprise_member_repository.is_in_enterprise(user_id=user_id):
            raise EnterpriseMemberExistedException
        if self.user_plan_repository.is_in_family_plan(user_plan=current_plan):
            raise PaymentFailedByUserInFamilyException
        if current_plan.is_personal_trial_applied() in [PLAN_TYPE_PM_LIFETIME, PLAN_TYPE_PM_LIFETIME_FAMILY]:
            raise PaymentFailedByUserInLifetimeException

        # If the user claimed or the education email claimed
        if self.education_email_repository.emails_verified(emails=[email, education_email]) is True:
            raise EducationEmailClaimedException

        if is_academic(email):
            user_education_email = self.education_email_repository.update_or_create_education_email(
                user_id=user_id, education_email=email, education_type=education_type, university=university,
                verified=False
            )
        elif is_academic(education_email):
            user_education_email = self.education_email_repository.update_or_create_education_email(
                user_id=user_id, education_email=education_email, education_type=education_type, university=university,
                verified=False
            )
        else:
            raise EducationEmailInvalidException

        if user_education_email.email == email:
            promo_code = self.payment_repository.create_education_promo_code(user_id=user_id)
            if not promo_code:
                raise CreateEducationEmailPromoCodeFailedException
            self.education_email_repository.update_education_email(
                education_email=user_education_email, update_data={
                    "promo_code": promo_code.code,
                    "verified": True,
                    "verification_token": None,
                }
            )
            if current_plan.user.activated:
                job = "education_pack_student_accepted"
                if education_type == "teacher":
                    job = "education_pack_teacher_accepted"
                if promo_code.expired_time:
                    expired_date = convert_readable_date(promo_code.expired_time, datetime_format="%d %b, %Y")
                else:
                    expired_date = None
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_locker_mail", **{
                        "user_ids": [user_id],
                        "job": job,
                        "scope": scope,
                        "username": email,
                        "code": promo_code.code,
                        "expired_date": expired_date,
                        "redeem_url": f"{locker_web_url}/manage-plans"
                    }
                )
        else:
            if new_user is False:
                # Sending notification to verify the Education email
                job = "education_pack_student_email_confirmation"
                if education_type == "teacher":
                    job = "education_pack_teacher_email_confirmation"
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_locker_mail", **{
                        "destinations": [{
                            "email": user_education_email.email,
                            "name": user_fullname or "there",
                            "language": "en"
                        }],
                        "user_ids": [user.user_id],
                        "job": job,
                        "scope": scope,
                        "username": username or email,
                        "locker_email": email,
                        "confirm_url": f"{locker_id_url}/confirmation/education-email/"
                                       f"{user_education_email.verification_token}",

                    }
                )
            else:
                promo_code = self.payment_repository.create_education_promo_code(user_id=user_id)
                if not promo_code:
                    raise CreateEducationEmailPromoCodeFailedException
                self.education_email_repository.update_education_email(
                    education_email=user_education_email, update_data={
                        "promo_code": promo_code.code,
                        "verified": True,
                        "verification_token": None,
                    }
                )

    def verify_education_email(self, token: str, secret_key: str, scope: str = None, locker_web_url: str = ""):
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidAlgorithmError, ValueError):
            raise EducationEmailInvalidException
        token_type = payload.get('token_type', None)
        user_id = payload.get('user_id', None)
        education_email = payload.get('education_email')
        expired_time = payload.get("expired_time")
        if token_type != TOKEN_TYPE_EDUCATION_CLAIM or expired_time < now():
            raise EducationEmailInvalidException

        user_education_email = self.education_email_repository.get_by_user_id(user_id=user_id, email=education_email)
        if not user_education_email:
            raise EducationEmailInvalidException
        if user_education_email.verification_token != token:
            raise EducationEmailInvalidException
        user = user_education_email.user
        email = self.user_repository.get_from_cystack_id(user_id=user_id).get("email")
        promo_code = self.payment_repository.create_education_promo_code(user_id=user_id)
        if not promo_code:
            raise CreateEducationEmailPromoCodeFailedException

        self.education_email_repository.update_education_email(education_email=user_education_email, update_data={
            "promo_code": promo_code.code,
            "verified": True,
            "verification_token": None
        })
        job = "education_pack_student_accepted"
        if user_education_email.education_type == "teacher":
            job = "education_pack_teacher_accepted"
        if promo_code.expired_time:
            expired_date = convert_readable_date(promo_code.expired_time, datetime_format="%d %b, %Y")
        else:
            expired_date = None
        BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
            func_name="notify_locker_mail", **{
                "user_ids": [user.user_id],
                "job": job,
                "scope": scope,
                "username": education_email,
                "code": promo_code.code,
                "expired_date": expired_date,
                "redeem_url": f"{locker_web_url}/manage-plans"
            }
        )

        return user_education_email.email

    def upgrade_plan(self, user_id: int, plan_alias: str, duration: str = DURATION_MONTHLY, number_members: int = 1,
                     promo_code: str = None, scope: str = None, **metadata):
        payment_method = metadata.get("payment_method", PAYMENT_METHOD_CARD)
        bank_id = metadata.get("bank_id")
        card = metadata.get("card")
        family_members = metadata.get("family_members", [])

        new_plan = self.plan_repository.get_plan_by_alias(alias=plan_alias)
        if not new_plan:
            raise PlanDoesNotExistException

        current_plan = self.user_plan_repository.get_user_plan(user_id=user_id)

        # Validate promo code
        promo_code_obj = None
        if promo_code:
            promo_code_obj = self.payment_repository.check_promo_code(
                user_id=user_id, code=promo_code, new_duration=duration, new_plan=new_plan.alias
            )
            if not promo_code_obj:
                raise PaymentPromoCodeInvalidException
        # Check plan duration
        if current_plan.pm_plan.alias == plan_alias and current_plan.duration == duration:
            raise UpgradePlanNotChangeException
        # Check payment method
        if current_plan.pm_plan.alias != PLAN_TYPE_PM_FREE and current_plan.default_payment_method != payment_method:
            raise UpgradePaymentMethodChangedException
        currency = CURRENCY_USD if payment_method == PAYMENT_METHOD_CARD else CURRENCY_VND
        # Check family members
        if new_plan.is_family_plan:
            if len(family_members) > new_plan.max_number - 1:
                raise MaxFamilyMemberReachedException
        else:
            family_members = []
        # Check card
        if payment_method == PAYMENT_METHOD_CARD:
            if not card:
                raise PaymentNotFoundCardException
            if not card.get("id_card"):
                raise PaymentNotFoundCardException
        # Check user is in enterprise or not
        if self.enterprise_member_repository.is_in_enterprise(user_id=user_id, enterprise_locked=False):
            raise EnterpriseMemberExistedException

        upgrade_metadata = {
            "currency": currency,
            "promo_code": promo_code_obj,
            "bank_id": bank_id,
            "card": card,
            "number_members": number_members,
            "family_members": list(family_members),
        }
        # Calc payment price of new plan
        promo_code_value = promo_code_obj.code if promo_code_obj else None
        calc_payment = self.user_plan_repository.calc_update_price(
            current_plan=current_plan, new_plan=new_plan, new_duration=duration, currency=currency,
            new_quantity=number_members, promo_code=promo_code_value
        )
        immediate_payment = calc_payment.get("immediate_payment")

        if current_plan.is_personal_trial_applied() is False:
            utm_source = self.user_repository.get_from_cystack_id(user_id=user_id).get("utm_source")
            if utm_source in LIST_UTM_SOURCE_PROMOTIONS:
                metadata.update({
                    "billing_cycle_anchor": calc_payment.get("next_billing_time")
                })
            else:
                metadata.update({
                    "trial_end": now() + TRIAL_PERSONAL_PLAN
                })

        # Start payment here
        payment = PaymentMethodFactory.get_method(
            user_plan=current_plan, scope=scope, payment_method=payment_method
        )
        payment_result = payment.upgrade_recurring_subscription(
            amount=immediate_payment, plan_type=new_plan.alias, coupon=promo_code_obj, duration=duration,
            **upgrade_metadata
        )
        if payment_result.get("success") is True:
            self.user_plan_repository.set_default_payment_method(user_id=user_id, payment_method=payment_method)

        return payment_result

    def cancel_plan(self, user_id: int, immediately: bool = False):
        current_plan = self.user_plan_repository.get_user_plan(user_id=user_id)
        if current_plan.pm_plan.alias == PLAN_TYPE_PM_FREE:
            raise CannotCancelDefaultPlanException

        end_time = self.user_plan_repository.cancel_plan(user=current_plan.user, immediately=immediately)
        return current_plan.pm_plan.name, end_time

    def plan_limit(self, user_id: int):
        current_plan = self.user_plan_repository.get_user_plan(user_id=user_id)
        ciphers_statistic_data = self.cipher_repository.statistic_created_ciphers(user_id=user_id)

        relay_addresses_statistic_data = {
            "total": self.relay_address_repository.count_user_relay_addresses(user_id=user_id)
        }

        plan_limit = self.user_plan_repository.get_max_allow_cipher_type(user=current_plan.user)
        plan_obj = current_plan.pm_plan
        if plan_obj.relay_premium or self.enterprise_member_repository.is_active_enterprise_member(user_id=user_id):
            relay_addresses_limit = None
        else:
            relay_addresses_limit = MAX_FREE_RElAY_DOMAIN
        plan_limit.update({
            "relay_addresses": relay_addresses_limit
        })

        return {
            "ciphers": ciphers_statistic_data,
            "relay_addresses": relay_addresses_statistic_data,
            "plan_limit": plan_limit
        }

    def get_pm_plan_by_alias(self, alias: str) -> PMPlan:
        plan = self.plan_repository.get_plan_by_alias(alias=alias)
        return plan

    def calc_payment_public(self, plan_alias: str, quantity: int, duration: str = DURATION_MONTHLY,
                            currency: str = CURRENCY_USD, promo_code: str = None,
                            allow_trial: bool = True) -> Dict:
        """
        Calc total payment
        :param plan_alias: (str) Plan alias
        :param duration: (str) Duration of the plan
        :param currency: (str) Currency: VND/USD
        :param quantity: (int)
        :param promo_code: (str) promo value
        :param allow_trial: (bool)
        :return:
        """
        new_plan = self.plan_repository.get_plan_by_alias(alias=plan_alias)
        if not new_plan:
            raise PlanDoesNotExistException
        result = self.user_plan_repository.calc_payment_public(
            new_plan=new_plan,
            new_duration=duration,
            new_quantity=quantity,
            currency=currency,
            promo_code=promo_code,
            allow_trial=allow_trial,
        )
        result["plan"] = new_plan.to_json()
        return result

    def check_valid_promo_code(self, promo_code: str, current_user: User) -> Optional[str]:
        return self.payment_repository.check_promo_code(
            user_id=current_user.user_id,
            code=promo_code
        )

    def create_payment(self, **payment_data) -> Payment:
        return self.payment_repository.create_payment(**payment_data)

    def update_payment(self, payment: Payment, update_data) -> Payment:
        return self.payment_repository.update_payment(payment=payment, update_data=update_data)
