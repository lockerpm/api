import ast
import math
from typing import Dict, Optional, List

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import F, Count

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models import PMUserPlanFamilyORM
from locker_server.api_orm.models.wrapper import get_user_model, get_user_plan_model, get_plan_model, \
    get_enterprise_member_model, get_enterprise_model, get_enterprise_member_role_model, get_promo_code_model
from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.payment.promo_code import PromoCode
from locker_server.core.entities.user.user import User
from locker_server.core.entities.user_plan.pm_plan import PMPlan
from locker_server.core.entities.user_plan.pm_user_plan import PMUserPlan
from locker_server.core.entities.user_plan.pm_user_plan_family import PMUserPlanFamily
from locker_server.core.exceptions.payment_exception import PaymentMethodNotSupportException
from locker_server.core.repositories.user_plan_repository import UserPlanRepository
from locker_server.shared.constants.ciphers import *
from locker_server.shared.constants.enterprise_members import E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_STATUS_CONFIRMED
from locker_server.shared.constants.transactions import *
from locker_server.shared.external_services.payment_method.payment_method_factory import PaymentMethodFactory
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.utils.app import now

UserORM = get_user_model()
PMPlanORM = get_plan_model()
PMUserPlanORM = get_user_plan_model()
PromoCodeORM = get_promo_code_model()
EnterpriseMemberRoleORM = get_enterprise_member_role_model()
EnterpriseMemberORM = get_enterprise_member_model()
EnterpriseORM = get_enterprise_model()
ModelParser = get_model_parser()


class UserPlanORMRepository(UserPlanRepository):
    @staticmethod
    def _get_current_plan_orm(user_id: int) -> PMUserPlanORM:
        user_orm = UserORM.objects.get(user_id=user_id)
        try:
            user_plan_orm = user_orm.pm_user_plan
        except (ValueError, AttributeError):
            user_plan_orm = PMUserPlanORM.update_or_create(
                user=user_orm,
            )
        return user_plan_orm

    @staticmethod
    def _get_user_orm(user_id: int) -> Optional[UserORM]:
        try:
            return UserORM.objects.get(user_id=user_id)
        except UserORM.DoesNotExist:
            return None

    def __cancel_family_members(self, user_plan_orm: PMUserPlanORM):
        family_members_orm = user_plan_orm.pm_plan_family.all()
        for family_member_orm in family_members_orm:
            if family_member_orm.user:
                self.update_plan(
                    user_id=int(user_plan_orm.user_id),
                    plan_type_alias=PLAN_TYPE_PM_FREE,
                    scope=settings.SCOPE_PWD_MANAGER
                )
            family_member_orm.delete()

    def __create_family_members(self, user_plan_orm: PMUserPlanORM, family_members) -> PMUserPlanORM:
        plan_orm = user_plan_orm.pm_plan
        if plan_orm.is_family_plan is False:
            return user_plan_orm
        # If this pm user plan has family members => Not create
        if user_plan_orm.pm_plan_family.exists():
            family_members = user_plan_orm.pm_plan_family.all()
            for family_member in family_members:
                # Update period for the family members
                if family_member.user:
                    self.update_plan(
                        user_id=family_member.user_id,
                        plan_type_alias=PLAN_TYPE_PM_PREMIUM,
                        duration=user_plan_orm.duration,
                        scope=settings.SCOPE_PWD_MANAGER,
                        **{
                            "start_period": user_plan_orm.start_period,
                            "end_period": user_plan_orm.end_period,
                            "number_members": 1
                        }
                    )
            return user_plan_orm

        family_members = ast.literal_eval(str(family_members))
        for family_member in family_members:
            email = family_member.get("email")
            user_id = family_member.get("user_id")
            self.add_to_family_sharing(family_user_plan_id=user_plan_orm.user_id, user_id=user_id, email=email)
        return user_plan_orm

    def __create_enterprise(self, user_id, enterprise_name):
        enterprise = self.get_default_enterprise(
            user_id=user_id, enterprise_name=enterprise_name, create_if_not_exist=True
        )
        return enterprise

    def __create_default_enterprise_orm(self, user_id: int, enterprise_name: str) -> EnterpriseORM:
        user_orm = self._get_user_orm(user_id=user_id)
        user_data = user_orm.get_from_cystack_id()
        enterprise_name = enterprise_name or user_data.get("organization") or "My Enterprise"
        enterprise_phone = user_data.get("phone") or ""
        enterprise_country = user_data.get("country") or ""
        default_enterprise = EnterpriseORM.create(**{
            "name": enterprise_name,
            "enterprise_phone": enterprise_phone,
            "enterprise_country": enterprise_country,
            "description": "",
            "members": [{
                "user": user_orm,
                "role": EnterpriseMemberRoleORM.objects.get(name=E_MEMBER_ROLE_PRIMARY_ADMIN),
                "status": E_MEMBER_STATUS_CONFIRMED,
                "is_default": True,
                "is_primary": True
            }]
        })
        return default_enterprise

    # ------------------------ List PMUserPlan resource ------------------- #
    def list_downgrade_plans(self) -> List[PMUserPlan]:
        user_plans_orm = PMUserPlanORM.objects.filter(
            pm_stripe_subscription__isnull=True
        ).exclude(
            pm_plan__alias=PLAN_TYPE_PM_FREE
        ).exclude(end_period__isnull=True).filter(end_period__lte=now()).annotate(
            family_members_count=Count('user__pm_plan_family')
        ).filter(family_members_count__lt=1).select_related('user')
        return [
            ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=user_plan_orm)
            for user_plan_orm in user_plans_orm
        ]

    def list_expiring_plans(self) -> List[PMUserPlan]:
        current_time = now()
        expiring_plans_orm = PMUserPlanORM.objects.exclude(
            pm_plan__alias=PLAN_TYPE_PM_FREE
        ).exclude(end_period__isnull=True).annotate(
            plan_period=F('end_period') - F('start_period'),
        ).filter(
            plan_period__lte=15 * 86400, plan_period__gt=0
        ).exclude(cancel_at_period_end=True).filter(
            end_period__gte=current_time + 5 * 86400,
            end_period__lte=current_time + 7 * 86400
        ).select_related('pm_plan').select_related('user')
        return [
            ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=user_plan_orm)
            for user_plan_orm in expiring_plans_orm
        ]

    def list_expiring_enterprise_plans(self) -> List[PMUserPlan]:
        current_time = now()
        expiring_enterprise_plans_orm = PMUserPlanORM.objects.filter(pm_plan__alias=PLAN_TYPE_PM_ENTERPRISE).filter(
            pm_stripe_subscription__isnull=False, end_period__isnull=False,
        ).filter(
            end_period__gte=current_time + 4 * 86400,
            end_period__lte=current_time + 5 * 86400
        ).select_related('pm_plan')
        return [
            ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=user_plan_orm)
            for user_plan_orm in expiring_enterprise_plans_orm
        ]

    # ------------------------ Get PMUserPlan resource --------------------- #
    def get_user_plan(self, user_id: int) -> Optional[PMUserPlan]:
        user_plan_orm = self._get_current_plan_orm(user_id=user_id)
        return ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=user_plan_orm)

    def get_mobile_user_plan(self, pm_mobile_subscription: str) -> Optional[PMUserPlan]:
        try:
            user_plan_orm = PMUserPlanORM.objects.get(pm_mobile_subscription=pm_mobile_subscription)
            return ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=user_plan_orm)
        except PMUserPlanORM.DoesNotExist:
            return None

    def get_default_enterprise(self, user_id: int, enterprise_name: str = None,
                               create_if_not_exist=False) -> Optional[Enterprise]:
        try:
            default_enterprise_orm = EnterpriseMemberORM.objects.get(is_default=True, user_id=user_id).enterprise
        except EnterpriseMemberORM.DoesNotExist:
            if create_if_not_exist is False:
                return None
            default_enterprise_orm = self.__create_default_enterprise_orm(
                user_id=user_id, enterprise_name=enterprise_name
            )
        except MultipleObjectsReturned:
            # If user has multiple default teams because of concurrent requests => Delete others
            multiple_default_enterprises_orm = EnterpriseMemberORM.objects.filter(
                is_default=True, user_id=user_id
            ).order_by('-creation_date')

            # Set first team as default
            default_enterprise_orm = multiple_default_enterprises_orm.first().team
            multiple_default_enterprises_orm.exclude(enterprise_id=default_enterprise_orm.id).delete()
        return ModelParser.enterprise_parser().parse_enterprise(enterprise_orm=default_enterprise_orm)

    def get_max_allow_cipher_type(self, user: User) -> Dict:
        user_orm = self._get_user_orm(user_id=user.user_id)
        user_enterprise_ids = user_orm.enterprise_members.filter(
            status=E_MEMBER_STATUS_CONFIRMED, is_activated=True,
            enterprise__locked=False
        ).values_list('enterprise_id', flat=True)
        primary_admins = EnterpriseMemberORM.objects.filter(enterprise_id__in=list(user_enterprise_ids)).filter(
            role_id=E_MEMBER_ROLE_PRIMARY_ADMIN
        ).values_list('user_id', flat=True)
        personal_plans_orm = PMUserPlanORM.objects.filter(
            user_id__in=list(primary_admins) + [user.user_id]
        ).select_related('pm_plan')
        cipher_limits = PMPlanORM.objects.filter(id__in=personal_plans_orm.values_list('pm_plan_id')).values(
            'limit_password', 'limit_secure_note', 'limit_identity', 'limit_payment_card', 'limit_crypto_asset'
        )
        limit_password = [cipher_limit.get("limit_password") for cipher_limit in cipher_limits]
        limit_secure_note = [cipher_limit.get("limit_secure_note") for cipher_limit in cipher_limits]
        limit_identity = [cipher_limit.get("limit_identity") for cipher_limit in cipher_limits]
        limit_payment_card = [cipher_limit.get("limit_payment_card") for cipher_limit in cipher_limits]
        limit_crypto_asset = [cipher_limit.get("limit_crypto_asset") for cipher_limit in cipher_limits]
        return {
            CIPHER_TYPE_LOGIN: None if None in limit_password else max(limit_password),
            CIPHER_TYPE_NOTE: None if None in limit_secure_note else max(limit_secure_note),
            CIPHER_TYPE_IDENTITY: None if None in limit_identity else max(limit_identity),
            CIPHER_TYPE_CARD: None if None in limit_payment_card else max(limit_payment_card),
            CIPHER_TYPE_CRYPTO_ACCOUNT: None if None in limit_crypto_asset else max(limit_crypto_asset),
            CIPHER_TYPE_CRYPTO_WALLET: None if None in limit_crypto_asset else max(limit_crypto_asset),
            CIPHER_TYPE_TOTP: None
        }

    def is_in_family_plan(self, user_plan: PMUserPlan) -> bool:
        user_id = user_plan.user.user_id
        return user_plan.pm_plan.is_family_plan or self.is_family_member(user_id=user_id)

    def is_family_member(self, user_id: int) -> bool:
        return PMUserPlanFamilyORM.objects.filter(user_id=user_id).exists()

    def get_family_members(self, user_id: int) -> Dict:
        current_plan_orm = self._get_current_plan_orm(user_id=user_id)
        pm_current_plan_alias = current_plan_orm.pm_plan.alias

        # The retrieving user is owner of the family plan
        if current_plan_orm.pm_plan.is_family_plan:
            owner_orm = current_plan_orm.user
            family_members_orm = current_plan_orm.pm_plan_family.all().order_by('-user_id', '-created_time')
        # Else, user is a member
        else:
            user_orm = current_plan_orm.user
            family_user_plan_orm = user_orm.pm_plan_family.first()
            if family_user_plan_orm:
                family_members_orm = family_user_plan_orm.root_user_plan.pm_plan_family.all().order_by(
                    '-user_id', '-created_time'
                )
                owner_orm = family_user_plan_orm.root_user_plan.user
            else:
                family_members_orm = []
                owner_orm = None
        return {
            "family_members": [
                ModelParser.user_plan_parser().parse_user_plan_family(user_plan_family_orm=m)
                for m in family_members_orm
            ],
            "owner": ModelParser.user_parser().parse_user(user_orm=owner_orm) if owner_orm else None
        }

    def get_family_member(self, owner_user_id: int, family_member_id: int) -> Optional[PMUserPlanFamily]:
        try:
            family_member_orm = PMUserPlanFamilyORM.objects.get(root_user_plan_id=owner_user_id, id=family_member_id)
            return ModelParser.user_plan_parser().parse_user_plan_family(user_plan_family_orm=family_member_orm)
        except PMUserPlanFamilyORM.DoesNotExist:
            return None

    def count_family_members(self, user_id: int) -> int:
        return PMUserPlanFamilyORM.objects.filter(root_user_plan_id=user_id).count()

    def calc_update_price(self, current_plan: PMUserPlan, new_plan: PMPlan, new_duration: str, new_quantity: int = 1,
                          currency: str = CURRENCY_USD, promo_code: str = None, allow_trial: bool = True,
                          utm_source: str = None) -> Dict:
        current_time = now()
        current_plan_orm = self._get_current_plan_orm(user_id=current_plan.user.user_id)
        # Get new plan price
        new_plan_price = new_plan.get_price(duration=new_duration, currency=currency)
        # Number of month duration billing by new duration
        duration_next_billing_month = PMUserPlan.get_duration_month_number(new_duration)
        # Calc discount
        error_promo = None
        promo_code_orm = None
        promo_description_en = None
        promo_description_vi = None
        if promo_code is not None and promo_code != "":
            promo_code_orm = PromoCodeORM.check_valid(
                value=promo_code, current_user=current_plan_orm.user, new_duration=new_duration, new_plan=new_plan.alias
            )
            if not promo_code_orm:
                error_promo = {"promo_code": ["This coupon is expired or incorrect"]}
            else:
                promo_description_en = promo_code_orm.description_en
                promo_description_vi = promo_code_orm.description_vi

        total_amount = new_plan_price * new_quantity
        next_billing_time = current_time + duration_next_billing_month * 30 * 86400

        # Discount and immediate payment
        total_amount = max(total_amount, 0)
        discount = promo_code_orm.get_discount(total_amount, duration=new_duration) if promo_code_orm else 0.0
        immediate_amount = max(round(total_amount - discount, 2), 0)

        result = {
            "alias": new_plan.alias,
            "price": round(new_plan_price, 2),
            "total_price": total_amount,
            "discount": discount,
            "duration": new_duration,
            "currency": currency,
            "immediate_payment": immediate_amount,
            "next_billing_time": next_billing_time,
            "personal_trial_applied": current_plan.is_personal_trial_applied(),
            "promo_description": {
                "en": promo_description_en,
                "vi": promo_description_vi
            },
            "error_promo": error_promo
        }
        if new_plan.is_team_plan is False:
            if current_plan.is_personal_trial_applied() is False and allow_trial is True:
                if utm_source in LIST_UTM_SOURCE_PROMOTIONS:
                    result["next_billing_time"] = next_billing_time + TRIAL_PERSONAL_PLAN
                else:
                    result["next_billing_time"] = now() + TRIAL_PERSONAL_PLAN
                    result["next_billing_payment"] = immediate_amount
                    result["immediate_payment"] = 0
        else:
            if current_plan.end_period and current_plan.end_period > now():
                result["next_billing_time"] = current_plan.end_period
                result["next_billing_payment"] = immediate_amount
                result["immediate_payment"] = 0
        return result

    def calc_payment_public(self, new_plan: PMPlan, new_duration: str, new_quantity: int, currency: str = CURRENCY_USD,
                            promo_code: str = None, allow_trial: bool = True, utm_source: str = None,
                            ) -> Dict:
        current_time = now()
        # Get new plan price
        new_plan_price = new_plan.get_price(duration=new_duration, currency=currency)
        # Number of month duration billing by new duration
        duration_next_billing_month = PMUserPlan.get_duration_month_number(new_duration)
        # Calc discount
        error_promo = None
        promo_code_orm = None
        promo_description_en = None
        promo_description_vi = None
        if promo_code is not None and promo_code != "":
            promo_code_orm = PromoCodeORM.check_valid(value=promo_code, current_user=None, new_duration=new_duration,
                                                      new_plan=new_plan.alias)
            if not promo_code_orm:
                error_promo = {"promo_code": ["This coupon is expired or incorrect"]}
            else:
                promo_description_en = promo_code_orm.description_en
                promo_description_vi = promo_code_orm.description_vi

        total_amount = new_plan_price * new_quantity
        next_billing_time = current_time + duration_next_billing_month * 30 * 86400

        # Discount and immediate payment
        total_amount = max(total_amount, 0)
        discount = promo_code_orm.get_discount(total_amount, duration=new_duration) if promo_code_orm else 0.0
        immediate_amount = max(round(total_amount - discount, 2), 0)

        result = {
            "alias": new_plan.alias,
            "price": round(new_plan_price, 2),
            "total_price": total_amount,
            "discount": discount,
            "duration": new_duration,
            "currency": currency,
            "immediate_payment": immediate_amount,
            "next_billing_time": next_billing_time,
            "promo_description": {
                "en": promo_description_en,
                "vi": promo_description_vi
            },
            "error_promo": error_promo,
            "quantity": new_quantity
        }
        return result

    def calc_lifetime_payment_public(self, new_plan: PMPlan, currency: str = CURRENCY_USD, promo_code: str = None,
                                     user: User = None):
        current_time = now()
        # Get new plan price
        new_plan_price = new_plan.get_price(currency=currency)
        old_plan_discount = 0
        if user:
            current_plan = self.get_user_plan(user_id=user.user_id)
            if current_plan.pm_plan.alias == PLAN_TYPE_PM_LIFETIME and new_plan.alias == PLAN_TYPE_PM_LIFETIME_FAMILY:
                old_plan_discount = math.floor(current_plan.pm_plan.get_price(currency=currency))
        # Calc discount
        error_promo = None
        promo_code_orm = None
        promo_description_en = None
        promo_description_vi = None
        if promo_code is not None and promo_code != "":
            promo_code_orm = PromoCodeORM.check_valid(value=promo_code, current_user=None, new_plan=new_plan.alias)
            if not promo_code_orm:
                error_promo = {"promo_code": ["This coupon is expired or incorrect"]}
            else:
                promo_description_en = promo_code_orm.description_en
                promo_description_vi = promo_code_orm.description_vi

        total_amount = new_plan_price
        next_billing_time = None

        # Discount and immediate payment
        total_amount = max(total_amount, 0)
        discount = promo_code_orm.get_discount(total_amount) if promo_code_orm else 0.0
        discount = discount + old_plan_discount
        immediate_amount = max(round(total_amount - discount, 2), 0)

        result = {
            "alias": new_plan.alias,
            "price": round(new_plan_price, 2),
            "total_price": total_amount,
            "discount": discount,
            "duration": "lifetime",
            "currency": currency,
            "immediate_payment": immediate_amount,
            "next_billing_time": next_billing_time,
            "promo_description": {
                "en": promo_description_en,
                "vi": promo_description_vi
            },
            "error_promo": error_promo,
            "quantity": 1
        }
        return result

    def is_update_personal_to_enterprise(self, current_plan: PMUserPlan, new_plan_alias: str) -> bool:
        """
        Handle event hooks: The plan update event is a personal plan while the current plan is Enterprise plan
        So, we don't need to update the plan of this user
        :param current_plan: (obj) The current plan
        :param new_plan_alias: (str) Event hook plan
        :return: True - Event hook is personal plan. Current plan is Enterprise
        """
        try:
            new_plan_obj = PMPlanORM.objects.get(alias=new_plan_alias)
            if current_plan.pm_plan.is_team_plan is True and new_plan_obj.is_team_plan is False:
                return True
        except PMPlanORM.DoesNotExist:
            pass
        return False

    # ------------------------ Create PMUserPlan resource --------------------- #
    def add_to_family_sharing(self, family_user_plan_id: int, user_id: int = None,
                              email: str = None) -> Optional[PMUserPlan]:
        family_user_plan_orm = self._get_current_plan_orm(user_id=family_user_plan_id)
        if user_id and family_user_plan_orm.pm_plan_family.filter(user_id=user_id).exists():
            return ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=family_user_plan_orm)
        if email and family_user_plan_orm.pm_plan_family.filter(email=email).exists():
            return ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=family_user_plan_orm)

        # Retrieve user
        try:
            family_member_user_orm = UserORM.objects.get(user_id=user_id, activated=True)
        except UserORM.DoesNotExist:
            family_member_user_orm = None

        if family_member_user_orm:
            current_member_plan_orm = self._get_current_plan_orm(user_id=family_member_user_orm.user_id)
            current_member_plan = ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=current_member_plan_orm)
            # If the member user has a plan => Cancel this plan if this plan is not a team plan
            if current_member_plan_orm.pm_plan.is_family_plan is False and \
                    current_member_plan_orm.pm_plan.is_team_plan is False:
                # Cancel current plan
                try:
                    PaymentMethodFactory.get_method(
                        user_plan=current_member_plan,
                        scope=settings.SCOPE_PWD_MANAGER,
                        payment_method=current_member_plan.default_payment_method
                    ).cancel_immediately_recurring_subscription()
                except PaymentMethodNotSupportException as e:
                    CyLog.warning(**{"message": "cancel_immediately_recurring_subscription user {} {} failed".format(
                        family_member_user_orm, e.payment_method
                    )})

                # Add to family plan
                family_user_plan_orm.pm_plan_family.model.create(
                    family_user_plan_orm.user_id, family_member_user_orm.user_id, None
                )

                # Then upgrade to Premium
                self.update_plan(
                    user_id=family_member_user_orm.user_id,
                    plan_type_alias=PLAN_TYPE_PM_PREMIUM,
                    duration=family_user_plan_orm.duration,
                    scope=settings.SCOPE_PWD_MANAGER, **{
                        "start_period": family_user_plan_orm.start_period,
                        "end_period": family_user_plan_orm.end_period,
                        "number_members": 1
                    }
                )
        else:
            family_user_plan_orm.pm_plan_family.model.create(family_user_plan_orm.user_id, None, email)
        return ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=family_user_plan_orm)

    # ------------------------ Update PMUserPlan resource --------------------- #
    def update_plan(self, user_id: int, plan_type_alias: str, duration: str = DURATION_MONTHLY, scope: str = None,
                    **kwargs):
        start_period = kwargs.get("start_period")
        end_period = kwargs.get("end_period")
        number_members = kwargs.get("number_members", 1)
        promo_code = kwargs.get("promo_code")
        cancel_at_period_end = kwargs.get("cancel_at_period_end", False)
        extra_time = kwargs.get("extra_time")
        extra_plan = kwargs.get("extra_plan")
        if start_period is None and plan_type_alias != PLAN_TYPE_PM_FREE:
            start_period = now(return_float=True)
        if end_period is None and plan_type_alias != PLAN_TYPE_PM_FREE:
            if duration == DURATION_HALF_YEARLY:
                end_period = 6 * 30 * 86400 + start_period
            elif duration == DURATION_YEARLY:
                end_period = 365 * 86400 + start_period
            else:
                end_period = 30 * 86400 + start_period
        if plan_type_alias in [PLAN_TYPE_PM_LIFETIME, PLAN_TYPE_PM_LIFETIME_FAMILY]:
            end_period = None

        user_plan_orm = self._get_current_plan_orm(user_id=user_id)
        user_orm = user_plan_orm.user
        user_plan_orm.pm_plan = PMPlanORM.objects.get(alias=plan_type_alias)
        user_plan_orm.duration = duration
        user_plan_orm.start_period = start_period
        user_plan_orm.end_period = end_period
        user_plan_orm.number_members = number_members
        if isinstance(promo_code, PromoCode):
            user_plan_orm.promo_code_id = promo_code.promo_code_id
        else:
            user_plan_orm.promo_code = promo_code
        user_plan_orm.cancel_at_period_end = cancel_at_period_end
        if extra_time and extra_time > 0:
            user_plan_orm.extra_time += extra_time
            if extra_plan:
                user_plan_orm.extra_plan = extra_plan
        user_plan_orm.save()

        if plan_type_alias == PLAN_TYPE_PM_FREE:
            user_plan_orm.start_period = None
            user_plan_orm.end_period = None
            user_plan_orm.attempts = 0
            user_plan_orm.cancel_mobile_subscription()
            # Lock all primary sharing
            primary_sharing_owners_orm = user_orm.team_members.filter(is_primary=True, key__isnull=False)
            for primary_sharing_owner_orm in primary_sharing_owners_orm:
                primary_sharing_owner_orm.team.lock_pm_team(lock=True)
            # Lock all enterprises
            primary_admin_enterprises_orm = user_orm.enterprise_members.filter(is_primary=True)
            for primary_sharing_owner_orm in primary_admin_enterprises_orm:
                primary_sharing_owner_orm.enterprise.lock_enterprise(lock=True)
            # Downgrade all family members
            self.__cancel_family_members(user_plan_orm=user_plan_orm)

            # If this plan has extra time => Upgrade to Premium
            extra_time = user_plan_orm.extra_time
            if extra_time > 0:
                user_plan_orm.extra_time = 0
                user_plan_orm.extra_plan = None
                user_plan_orm.save()
                self.update_plan(
                    user_id=user_id,
                    plan_type_alias=user_plan_orm.extra_plan or PLAN_TYPE_PM_PREMIUM,
                    **{
                        "start_period": now(),
                        "end_period": now() + extra_time,
                        "cancel_at_period_end": True
                    }
                )

        else:
            user_plan_orm.attempts = kwargs.get("attempts", 0)
            # Unlock all their sharing
            primary_sharing_owners_orm = user_orm.team_members.filter(is_primary=True, key__isnull=False)
            for primary_sharing_owner_orm in primary_sharing_owners_orm:
                primary_sharing_owner_orm.team.lock_pm_team(lock=False)

        user_plan_orm.save()

        # Update plan rule here
        # If the plan is team plan => Create Enterprise
        plan_orm = user_plan_orm.pm_plan
        if plan_orm.is_team_plan:
            # Leave other family plans if user is a member
            user_orm.pm_plan_family.all().delete()
            # Create enterprise here
            enterprise_name = kwargs.get("enterprise_name")
            self.__create_enterprise(user_id=user_orm.user_id, enterprise_name=enterprise_name)
            # Unlock enterprises
            primary_admin_enterprises_orm = user_orm.enterprise_members.filter(is_primary=True)
            for primary_sharing_owner_orm in primary_admin_enterprises_orm:
                primary_sharing_owner_orm.enterprise.lock_enterprise(lock=False)

        # If the plan is family plan => Upgrade plan for the user
        if plan_orm.is_family_plan:
            # Leave other family plans if user is a member
            user_orm.pm_plan_family.all().delete()
            # Create family members
            family_members = kwargs.get("family_members", [])
            self.__create_family_members(user_plan_orm=user_plan_orm, family_members=family_members)

        return ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=user_plan_orm)

    def set_personal_trial_applied(self, user_id: int, applied: bool = True, platform: str = None):
        if platform is not None:
            assert platform in ["web", "mobile"]
        user_plan_orm = self._get_current_plan_orm(user_id=user_id)
        user_plan_orm.personal_trial_applied = applied
        if platform == "web":
            user_plan_orm.personal_trial_web_applied = True
        elif platform == "mobile":
            user_plan_orm.personal_trial_mobile_applied = True
        user_plan_orm.save()

    def set_enterprise_trial_applied(self, user_id: int, applied: bool = True, platform: str = None):
        user_plan_orm = self._get_current_plan_orm(user_id=user_id)
        user_plan_orm.enterprise_trial_applied = applied
        user_plan_orm.save()

    def set_default_payment_method(self, user_id: int, payment_method: str):
        user_plan_orm = self._get_current_plan_orm(user_id=user_id)
        user_plan_orm.default_payment_method = payment_method
        user_plan_orm.save()

    def upgrade_member_family_plan(self, user: User) -> Optional[User]:
        user_orm = self._get_user_orm(user_id=user.user_id)
        if not user_orm:
            return
        email = user_orm.get_from_cystack_id().get("email")
        if not email:
            return user
        family_invitations_orm = PMUserPlanFamilyORM.objects.filter(email=email).order_by('created_time')
        family_invitation_orm = family_invitations_orm.first()
        if family_invitation_orm:
            root_user_plan = family_invitation_orm.root_user_plan
            self.update_plan(
                user_id=user.user_id, plan_type_alias=PLAN_TYPE_PM_PREMIUM, duration=root_user_plan.duration,
                scope=settings.SCOPE_PWD_MANAGER, **{
                    "start_period": root_user_plan.start_period,
                    "end_period": root_user_plan.end_period,
                    "number_members": 1
                }
            )
            family_invitations_orm.update(user=user_orm, email=None)
        return user

    def update_user_plan_by_id(self, user_plan_id: str, user_plan_update_data) -> Optional[PMUserPlan]:
        try:
            user_plan_orm = PMUserPlanORM.objects.get(user_id=user_plan_id)
        except PMUserPlanORM.DoesNotExist:
            return None
        if user_plan_update_data.get("extra_time"):
            user_plan_orm.extra_time = F('extra_time') + user_plan_update_data.get("extra_time", 0)
        if user_plan_update_data.get("extra_time_value"):
            user_plan_orm.extra_time = user_plan_update_data.get("extra_time_value", user_plan_orm.extra_time)
        user_plan_orm.extra_plan = user_plan_update_data.get("extra_plan", user_plan_orm.extra_plan)
        user_plan_orm.pm_mobile_subscription = user_plan_update_data.get(
            "pm_mobile_subscription", user_plan_orm.pm_mobile_subscription
        )
        user_plan_orm.default_payment_method = user_plan_update_data.get(
            "default_payment_method",
            user_plan_orm.default_payment_method
        )
        user_plan_orm.cancel_at_period_end = user_plan_update_data.get(
            "cancel_at_period_end", user_plan_orm.cancel_at_period_end
        )
        user_plan_orm.pm_stripe_subscription = user_plan_update_data.get(
            "pm_stripe_subscription", user_plan_orm.pm_stripe_subscription
        )
        user_plan_orm.pm_stripe_subscription_created_time = user_plan_update_data.get(
            "pm_stripe_subscription_created_time", user_plan_orm.pm_stripe_subscription_created_time
        )
        user_plan_orm.promo_code = user_plan_update_data.get("promo_code", user_plan_orm.promo_code)
        user_plan_orm.personal_trial_applied = user_plan_update_data.get(
            "personal_trial_applied", user_plan_orm.personal_trial_applied
        )
        user_plan_orm.personal_trial_web_applied = user_plan_update_data.get(
            "personal_trial_web_applied", user_plan_orm.personal_trial_web_applied
        )
        user_plan_orm.attempts = user_plan_update_data.get(
            "attempts", user_plan_orm.attempts
        )
        user_plan_orm.end_period = user_plan_update_data.get(
            "end_period", user_plan_orm.end_period
        )
        user_plan_orm.member_billing_updated_time = user_plan_update_data.get(
            "member_billing_updated_time", user_plan_orm.member_billing_updated_time
        )
        user_plan_orm.save()
        return ModelParser.user_plan_parser().parse_user_plan(user_plan_orm=user_plan_orm)

    # ------------------------ Delete PMUserPlan resource --------------------- #
    def cancel_plan(self, user: User, immediately=False, **kwargs):
        current_plan = self.get_user_plan(user_id=user.user_id)
        pm_plan_alias = current_plan.pm_plan.alias
        if pm_plan_alias == PLAN_TYPE_PM_FREE:
            return
        stripe_subscription = current_plan.get_stripe_subscription()
        payment_method = PAYMENT_METHOD_CARD if stripe_subscription else PAYMENT_METHOD_WALLET
        if immediately is False:
            end_time = PaymentMethodFactory.get_method(
                user_plan=current_plan, scope=settings.SCOPE_PWD_MANAGER, payment_method=payment_method
            ).cancel_recurring_subscription(**kwargs)
        else:
            PaymentMethodFactory.get_method(
                user_plan=current_plan, scope=settings.SCOPE_PWD_MANAGER, payment_method=payment_method
            ).cancel_immediately_recurring_subscription()
            end_time = now()
        return end_time

    def delete_family_member(self, family_member_id: int):
        try:
            family_member_orm = PMUserPlanFamilyORM.objects.get(id=family_member_id)
        except PMUserPlanFamilyORM.DoesNotExist:
            return
        if family_member_orm.user:
            self.update_plan(
                user_id=family_member_orm.user_id, plan_type_alias=PLAN_TYPE_PM_FREE, scope=settings.SCOPE_PWD_MANAGER
            )
        family_user_id = family_member_orm.user_id
        family_email = family_member_orm.email
        family_member_orm.delete()
        return family_user_id, family_email
