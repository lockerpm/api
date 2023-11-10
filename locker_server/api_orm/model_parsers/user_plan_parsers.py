from locker_server.api_orm.model_parsers.wrapper_specific_model_parser import get_specific_model_parser
from locker_server.api_orm.models import *
from locker_server.core.entities.user_plan.plan_type import PlanType
from locker_server.core.entities.user_plan.pm_plan import PMPlan
from locker_server.core.entities.user_plan.pm_user_plan import PMUserPlan
from locker_server.core.entities.user_plan.pm_user_plan_family import PMUserPlanFamily


class UserPlanParser:
    @classmethod
    def parse_plan_type(cls, plan_type_orm: PlanTypeORM) -> PlanType:
        return PlanType(name=plan_type_orm.name)

    @classmethod
    def parse_plan(cls, plan_orm: PMPlanORM) -> PMPlan:
        return PMPlan(
            plan_id=plan_orm.id,
            alias=plan_orm.alias,
            name=plan_orm.name,
            price_usd=plan_orm.price_usd,
            price_vnd=plan_orm.price_vnd,
            half_yearly_price_usd=plan_orm.half_yearly_price_usd,
            half_yearly_price_vnd=plan_orm.half_yearly_price_vnd,
            yearly_price_usd=plan_orm.yearly_price_usd,
            yearly_price_vnd=plan_orm.yearly_price_vnd,
            sync_device=plan_orm.sync_device,
            limit_password=plan_orm.limit_password,
            limit_secure_note=plan_orm.limit_secure_note,
            limit_identity=plan_orm.limit_identity,
            limit_payment_card=plan_orm.limit_payment_card,
            limit_crypto_asset=plan_orm.limit_crypto_asset,
            tools_password_reuse=plan_orm.tools_password_reuse,
            tools_master_password_check=plan_orm.tools_master_password_check,
            tools_data_breach=plan_orm.tools_data_breach,
            emergency_access=plan_orm.emergency_access,
            personal_share=plan_orm.personal_share,
            relay_premium=plan_orm.relay_premium,
            is_family_plan=plan_orm.is_family_plan,
            max_number=plan_orm.max_number,
            team_dashboard=plan_orm.team_dashboard,
            team_policy=plan_orm.team_policy,
            team_prevent_password=plan_orm.team_prevent_password,
            team_activity_log=plan_orm.team_activity_log,
            plan_type=cls.parse_plan_type(plan_type_orm=plan_orm)
        )

    @classmethod
    def parse_user_plan(cls, user_plan_orm: PMUserPlanORM) -> PMUserPlan:
        user_parser = get_specific_model_parser("UserParser")
        payment_parser = get_specific_model_parser("PaymentParser")
        promo_code = None
        if user_plan_orm.promo_code:
            promo_code = payment_parser.parse_promo_code(promo_code_orm=user_plan_orm.promo_code)
        return PMUserPlan(
            pm_user_plan_id=user_plan_orm.user_id,
            user=user_parser.parse_user(user_orm=user_plan_orm.user),
            duration=user_plan_orm.duration,
            start_period=user_plan_orm.start_period,
            end_period=user_plan_orm.end_period,
            cancel_at_period_end=user_plan_orm.cancel_at_period_end,
            custom_endtime=user_plan_orm.custom_endtime,
            default_payment_method=user_plan_orm.default_payment_method,
            ref_plan_code=user_plan_orm.ref_plan_code,
            number_members=user_plan_orm.number_members,
            personal_trial_applied=user_plan_orm.personal_trial_applied,
            enterprise_trial_applied=user_plan_orm.enterprise_trial_applied,
            personal_trial_mobile_applied=user_plan_orm.personal_trial_mobile_applied,
            personal_trial_web_applied=user_plan_orm.personal_trial_web_applied,
            pm_stripe_subscription=user_plan_orm.pm_stripe_subscription,
            pm_stripe_subscription_created_time=user_plan_orm.pm_stripe_subscription_created_time,
            pm_mobile_subscription=user_plan_orm.pm_mobile_subscription,
            extra_time=user_plan_orm.extra_time,
            extra_plan=user_plan_orm.extra_plan,
            member_billing_updated_time=user_plan_orm.member_billing_updated_time,
            attempts=user_plan_orm.attempts,
            pm_plan=cls.parse_plan(plan_orm=user_plan_orm.pm_plan),
            promo_code=promo_code
        )

    @classmethod
    def parse_user_plan_family(cls, user_plan_family_orm: PMUserPlanFamilyORM) -> PMUserPlanFamily:
        user_parser = get_specific_model_parser("UserParser")
        return PMUserPlanFamily(
            pm_user_plan_family_id=user_plan_family_orm.id,
            created_time=user_plan_family_orm.created_time,
            email=user_plan_family_orm.email,
            user=user_parser.parse_user(user_orm=user_plan_family_orm.user) if user_plan_family_orm.user else None,
            root_user_plan=cls.parse_user_plan(user_plan_orm=user_plan_family_orm.root_user_plan)
        )
