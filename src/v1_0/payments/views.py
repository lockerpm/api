import json
import math

import jwt
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from core.utils.data_helpers import convert_readable_date
from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from shared.constants.ciphers import *
from shared.constants.relay_address import MAX_FREE_RElAY_DOMAIN
from shared.constants.token import TOKEN_EXPIRED_TIME_TRIAL_ENTERPRISE, TOKEN_TYPE_TRIAL_ENTERPRISE, \
    TOKEN_TYPE_EDUCATION_CLAIM
from shared.constants.transactions import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.payment_pwd_permission import PaymentPwdPermission
from cystack_models.models.payments.payments import Payment
from cystack_models.models.users.users import User
from cystack_models.models.user_plans.pm_plans import PMPlan
from cystack_models.models import Cipher, PromoCode, EducationEmail
from shared.utils.app import now
from shared.utils.student_email import is_academic
from v1_0.resources.serializers import PMPlanSerializer
from v1_0.payments.serializers import CalcSerializer, UpgradePlanSerializer, ListInvoiceSerializer, \
    DetailInvoiceSerializer, AdminUpgradePlanSerializer, UpgradeTrialSerializer, CancelPlanSerializer, \
    UpgradeLifetimeSerializer, UpgradeThreePromoSerializer, UpgradeLifetimePublicSerializer, \
    UpgradeEducationPublicSerializer, CalcLifetimePublicSerializer
from v1_0.general_view import PasswordManagerViewSet


class PaymentPwdViewSet(PasswordManagerViewSet):
    permission_classes = (PaymentPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "calc":
            self.serializer_class = CalcSerializer
        elif self.action == "upgrade_plan":
            self.serializer_class = UpgradePlanSerializer
        elif self.action in ["invoices", "list", "user_invoices"]:
            self.serializer_class = ListInvoiceSerializer
        elif self.action == "retrieve_invoice":
            self.serializer_class = DetailInvoiceSerializer
        elif self.action == "admin_upgrade_plan":
            self.serializer_class = AdminUpgradePlanSerializer
        elif self.action == "upgrade_trial":
            self.serializer_class = UpgradeTrialSerializer
        elif self.action == "upgrade_lifetime":
            self.serializer_class = UpgradeLifetimeSerializer
        elif self.action == "upgrade_three_promo":
            self.serializer_class = UpgradeThreePromoSerializer
        elif self.action == "upgrade_lifetime_public":
            self.serializer_class = UpgradeLifetimePublicSerializer
        elif self.action == "calc_lifetime_public":
            self.serializer_class = CalcLifetimePublicSerializer

        elif self.action == "upgrade_education_public":
            self.serializer_class = UpgradeEducationPublicSerializer
        elif self.action == "cancel_plan":
            self.serializer_class = CancelPlanSerializer
        
        return super(PaymentPwdViewSet, self).get_serializer_class()

    def get_invoice(self):
        try:
            invoice = self.payment_repository.get_invoice_by_user(
                user=self.request.user, invoice_id=self.kwargs.get("pk")
            )
            return invoice
        except Payment.DoesNotExist:
            raise NotFound

    def get_user(self, user_id):
        try:
            user = User.objects.get(user_id=user_id)
            return user
        except User.DoesNotExist:
            return None

    def allow_upgrade_enterprise_trial(self, user):
        # # If this user does not created master pass
        # if user.activated is False:
        #     raise ValidationError({"non_field_errors": [gen_error("1003")]})
        # # If this user has an enterprise => The trial plan is applied
        if user.enterprise_members.exists() is True:
            raise ValidationError({"non_field_errors": [gen_error("7015")]})
        # # If this user is in other plan => Don't allow
        # pm_current_plan = self.user_repository.get_current_plan(user=user)
        # if pm_current_plan.get_plan_type_alias() != PLAN_TYPE_PM_FREE:
        #     raise ValidationError({"non_field_errors": [gen_error("7014")]})

        # TODO: Check the user applied trial enterprise or not
        pm_current_plan = self.user_repository.get_current_plan(user=user)
        if pm_current_plan.is_enterprise_trial_applied() is True:
            raise ValidationError({"non_field_errors": [gen_error("7013")]})

        return pm_current_plan

    def get_queryset(self):
        all_pm_invoices = Payment.objects.filter().order_by('-created_time')
        from_param = self.check_int_param(self.request.query_params.get("from"))
        to_param = self.check_int_param(self.request.query_params.get("to"))
        status_param = self.request.query_params.get("status")
        payment_method_param = self.request.query_params.get("payment_method")
        if from_param:
            all_pm_invoices = all_pm_invoices.filter(created_time__lte=from_param)
        if to_param:
            all_pm_invoices = all_pm_invoices.filter(created_time__gt=to_param)
        if status_param:
            all_pm_invoices = all_pm_invoices.filter(status=status_param)
        if payment_method_param:
            all_pm_invoices = all_pm_invoices.filter(payment_method=payment_method_param)
        return all_pm_invoices

    def list(self, request, *args, **kwargs):
        return super(PaymentPwdViewSet, self).list(request, *args, **kwargs)

    @action(methods=["get"], detail=False)
    def user_invoices(self, request, *args, **kwargs):
        user = self.get_user(user_id=kwargs.get("pk"))
        if not user:
            raise NotFound
        invoices = self.get_queryset().filter(user=user)
        queryset = self.filter_queryset(invoices)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=["post"], detail=False)
    def admin_upgrade_plan(self, request, *args, **kwargs):
        user = self.get_user(user_id=kwargs.get("pk"))
        if not user:
            raise NotFound

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        plan_alias = validated_data.get("plan_alias")
        end_period = validated_data.get("end_period")
        start_period = now()
        # Upgrade plan of the user
        self.user_repository.update_plan(
            user=user, plan_type_alias=plan_alias, scope=settings.SCOPE_PWD_MANAGER,
            **{
                "start_period": start_period,
                "end_period": end_period
            }
        )
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def calc(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        promo_code = validated_data.get("promo_code")
        duration = validated_data.get("duration", DURATION_MONTHLY)
        plan = validated_data.get("plan")
        number_members = validated_data.get("number_members", 1)
        currency = validated_data.get("currency", CURRENCY_USD)
        # Calc payment
        result = self._calc_payment(
            plan=plan, duration=duration, currency=currency, number_members=number_members, promo_code=promo_code
        )
        return Response(status=200, data=result)

    @action(methods=["get"], detail=False)
    def check_trial(self, request, *args, **kwargs):
        user = self.request.user
        pm_current_plan = self.user_repository.get_current_plan(user=user)
        return Response(status=200, data={"personal_trial_applied": pm_current_plan.is_personal_trial_applied()})

    @action(methods=["post"], detail=False)
    def upgrade_trial(self, request, *args, **kwargs):
        user = self.request.user
        pm_current_plan = self.user_repository.get_current_plan(user=user)
        trial_applied = pm_current_plan.is_personal_trial_applied()
        if trial_applied is True:
            raise ValidationError({"non_field_errors": [gen_error("7013")]})
        if user.enterprise_members.filter(enterprise__locked=False).exists():
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        trial_plan_obj = validated_data.get("trial_plan_obj")
        plan_metadata = {
            "start_period": now(),
            "end_period": now() + TRIAL_PERSONAL_PLAN
        }
        self.user_repository.update_plan(
            user=user, plan_type_alias=trial_plan_obj.get_alias(),
            duration=DURATION_MONTHLY, scope=settings.SCOPE_PWD_MANAGER, **plan_metadata
        )
        pm_current_plan.personal_trial_applied = True
        pm_current_plan.personal_trial_web_applied = True
        pm_current_plan.save()
        # Send trial mail
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="trial_successfully", **{
                "user_id": user.user_id,
                "scope": settings.SCOPE_PWD_MANAGER,
                "plan": trial_plan_obj.get_alias(),
                "payment_method": None,
                "duration": TRIAL_PERSONAL_DURATION_TEXT
            }
        )
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def upgrade_trial_enterprise_by_code(self, request, *args, **kwargs):
        token = request.data.get("token")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidAlgorithmError):
            raise ValidationError(detail={"token": ["The upgrade token is not valid"]})
        user_id = payload.get("user_id")
        expired_time = payload.get("expired_time")
        token_type = payload.get("token_type")
        enterprise_name = payload.get("enterprise_name") or "My Enterprise"
        if token_type != TOKEN_TYPE_TRIAL_ENTERPRISE or (expired_time and expired_time < now()):
            raise ValidationError(detail={"token": ["The upgrade token is not valid"]})
        try:
            user = self.user_repository.get_by_id(user_id=user_id)
        except ObjectDoesNotExist:
            raise ValidationError(detail={"token": ["The upgrade token is not valid"]})

        self.allow_upgrade_enterprise_trial(user=user)

        # Cancel immediately the Stripe subscription
        pm_current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        old_plan = pm_current_plan.get_plan_type_alias()
        old_end_period = pm_current_plan.end_period
        PaymentMethodFactory.get_method(
            user=user, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
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
        self.user_repository.update_plan(
            user=user, plan_type_alias=PLAN_TYPE_PM_ENTERPRISE,
            duration=DURATION_MONTHLY, scope=settings.SCOPE_PWD_MANAGER, **plan_metadata
        )
        # Set default payment method and enterprise_trial_applied is True
        pm_current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        pm_current_plan.enterprise_trial_applied = True
        pm_current_plan.save()
        pm_current_plan.set_default_payment_method(PAYMENT_METHOD_CARD)

        # Send trial mail
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="trial_enterprise_successfully", **{
                "user_id": user.user_id,
                "scope": settings.SCOPE_PWD_MANAGER,
            }
        )
        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def generate_trial_enterprise_code(self, request, *args, **kwargs):
        user = self.request.user
        self.allow_upgrade_enterprise_trial(user=user)
        payload = {
            "user_id": user.user_id,
            "plan": PLAN_TYPE_PM_ENTERPRISE,
            "enterprise_name": request.data.get("enterprise_name", "My Enterprise"),
            "token_type": TOKEN_TYPE_TRIAL_ENTERPRISE,
            "expired_time": now() + TOKEN_EXPIRED_TIME_TRIAL_ENTERPRISE
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return Response(status=200, data={"token": token})

    @action(methods=["post"], detail=False)
    def upgrade_lifetime(self, request, *args, **kwargs):
        user = self.request.user
        if user.enterprise_members.filter().exists():
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        plan_obj = validated_data.get("plan_obj")

        if plan_obj.get_alias() == PLAN_TYPE_PM_LIFETIME_FAMILY:
            if user.pm_plan_family.exists():
                raise ValidationError(detail={"non_field_errors": [gen_error("7016")]})
        else:
            if current_plan.get_plan_obj().is_family_plan or user.pm_plan_family.exists():
                raise ValidationError(detail={"non_field_errors": [gen_error("7016")]})
        saas_code = validated_data.get("saas_code")
        saas_code.remaining_times = F('remaining_times') - 1
        saas_code.save()
        saas_code.refresh_from_db()
        # Avoid race conditions - Make sure that this code is still available
        if saas_code.remaining_times < 0:
            raise ValidationError(detail={"code": ["This code is expired or not valid"]})

        # Cancel the current Free/Premium/Family
        # If new plan is family lifetime => Only cancel stripe subscription
        if plan_obj.get_alias() == PLAN_TYPE_PM_LIFETIME_FAMILY:
            if current_plan.pm_stripe_subscription:
                self.user_repository.cancel_plan(user=user, immediately=True)
        else:
            self.user_repository.cancel_plan(user=user, immediately=True)

        if saas_code.saas_market.lifetime_duration is None:
            saas_end_period = None
            upgrade_duration = DURATION_MONTHLY
        else:
            if current_plan.personal_trial_applied is False:
                saas_end_period = now() + saas_code.saas_market.lifetime_duration + TRIAL_PERSONAL_PLAN
                current_plan.personal_trial_applied = True
                current_plan.personal_trial_web_applied = True
                current_plan.save()
            else:
                saas_end_period = now() + saas_code.saas_market.lifetime_duration
            upgrade_duration = DURATION_YEARLY
        plan_metadata = {
            "start_period": now(),
            "end_period": saas_end_period
        }
        self.user_repository.update_plan(
            user=user, plan_type_alias=plan_obj.get_alias(),
            duration=upgrade_duration, scope=settings.SCOPE_PWD_MANAGER, **plan_metadata
        )
        user.set_saas_source(saas_source=saas_code.saas_market.name)

        # Send lifetime welcome mail
        user.refresh_from_db()
        if user.activated:
            if plan_obj.get_alias() in [PLAN_TYPE_PM_LIFETIME, PLAN_TYPE_PM_LIFETIME_FAMILY]:
                LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_locker_mail", **{
                        "user_ids": [user.user_id],
                        "job": "upgraded_to_lifetime_from_code",
                        "scope": settings.SCOPE_PWD_MANAGER,
                        "service_name": user.saas_source,
                    }
                )
            else:
                LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_locker_mail", **{
                        "user_ids": [user.user_id],
                        "job": "upgraded_from_code_promo",
                        "scope": settings.SCOPE_PWD_MANAGER,
                        "service_name": user.saas_source,
                        "plan": plan_obj.get_name()
                    }
                )
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def upgrade_three_promo(self, request, *args, **kwargs):
        user = self.request.user
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        if current_plan.get_plan_type_alias() != PLAN_TYPE_PM_FREE:
            raise ValidationError({"non_field_errors": [gen_error("7010")]})

        card = request.data.get("card")
        if not card:
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        if not card.get("id_card"):
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        promo_code_obj = validated_data.get("promo_code_obj", None)
        duration = DURATION_MONTHLY
        new_plan = PMPlan.objects.get(alias=PLAN_TYPE_PM_PREMIUM)
        metadata = {
            "currency": CURRENCY_USD,
            "promo_code": promo_code_obj,
            "card": card,
            "billing_cycle_anchor": now() + 3 * 30 * 86400,     # Next 3 months
        }
        # Calc payment price of new plan
        promo_code_value = promo_code_obj.code if promo_code_obj else None
        calc_payment = self._calc_payment(
            new_plan, duration=DURATION_MONTHLY, currency=CURRENCY_USD, promo_code=promo_code_value
        )
        immediate_payment = calc_payment.get("immediate_payment")

        payment = PaymentMethodFactory.get_method(
            user=user, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
        )
        payment_result = payment.upgrade_recurring_subscription(
            amount=immediate_payment, plan_type=new_plan.get_alias(), coupon=promo_code_obj, duration=duration,
            **metadata
        )

        update_result = payment_result.get("success")
        if update_result is False:
            if payment_result.get("stripe_error"):
                return Response(status=400, data={
                    "code": "7009",
                    "message": "Your card was declined (insufficient funds, etc...)",
                    "details": payment_result.get("error_details")
                })
            raise ValidationError({"non_field_errors": [gen_error("7009")]})

        # Set default payment method
        try:
            current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
            current_plan.set_default_payment_method(PAYMENT_METHOD_CARD)
        except ObjectDoesNotExist:
            pass
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def calc_lifetime_public(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        promo_code = validated_data.get("promo_code")
        plan_alias = validated_data.get("plan_alias")
        currency = validated_data.get("currency", CURRENCY_USD)
        user_id = validated_data.get("user_id")
        try:
            user = self.user_repository.get_by_id(user_id=user_id)
        except User.DoesNotExist:
            user = None
        # Calc payment
        result = self._calc_lifetime_payment_public(
            plan=plan_alias, currency=currency, promo_code=promo_code, user=user
        )
        return Response(status=200, data=result)

    @action(methods=["post"], detail=False)
    def upgrade_lifetime_public(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        promo_code_obj = validated_data.get("promo_code_obj", None)
        plan_alias = validated_data.get("plan_alias", PLAN_TYPE_PM_LIFETIME)
        duration = validated_data.get("duration", DURATION_MONTHLY)
        currency = validated_data.get("currency")

        if user.enterprise_members.filter().exists():
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        if current_plan.get_plan_type_alias() == plan_alias:
            raise ValidationError(detail={"non_field_errors": [gen_error("7017")]})
        if plan_alias == PLAN_TYPE_PM_LIFETIME_FAMILY:
            if user.pm_plan_family.exists():
                raise ValidationError(detail={"non_field_errors": [gen_error("7016")]})
        else:
            if current_plan.get_plan_obj().is_family_plan or user.pm_plan_family.exists():
                raise ValidationError(detail={"non_field_errors": [gen_error("7016")]})
        card = request.data.get("card")
        if not card:
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        if not card.get("id_card"):
            raise ValidationError({"non_field_errors": [gen_error("7007")]})

        plan_obj = PMPlan.objects.get(alias=plan_alias)
        plan_metadata = {
            "start_period": now(),
            "end_period": None,
            "card": card,
        }

        # Calc payment price of new plan
        promo_code_value = promo_code_obj.code if promo_code_obj else None
        # calc_payment = self._calc_payment(
        #     plan_obj, duration=duration, currency=currency, promo_code=promo_code_value, allow_trial=False
        # )
        calc_payment = self._calc_lifetime_payment_public(
            plan_obj, currency=currency, promo_code=promo_code_value, user=user
        )
        immediate_payment = calc_payment.get("immediate_payment")
        payment = PaymentMethodFactory.get_method(
            user=user, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
        )
        payment_result = payment.onetime_payment(
            amount=immediate_payment, plan_type=plan_obj.get_alias(), coupon=promo_code_obj, **plan_metadata

        )
        update_result = payment_result.get("success")
        if update_result is False:
            if payment_result.get("stripe_error"):
                return Response(status=400, data={
                    "code": "7009",
                    "message": "Your card was declined (insufficient funds, etc...)",
                    "details": payment_result.get("error_details")
                })
            raise ValidationError({"non_field_errors": [gen_error("7009")]})

        current_plan.extra_plan = None
        current_plan.extra_time = 0
        current_plan.save()
        self.user_repository.update_plan(
            user=user, plan_type_alias=plan_obj.get_alias(),
            duration=duration, scope=settings.SCOPE_PWD_MANAGER, **plan_metadata
        )

        # Cancel the current Stripe subscription: Free/Premium/Family
        self.user_repository.cancel_plan(user=user, immediately=True)

        # Make sure upgrade
        self.user_repository.update_plan(
            user=user, plan_type_alias=plan_obj.get_alias(),
            duration=duration, scope=settings.SCOPE_PWD_MANAGER, **plan_metadata
        )

        # Set default payment method
        try:
            current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
            current_plan.set_default_payment_method(PAYMENT_METHOD_CARD)
        except ObjectDoesNotExist:
            pass

        # Send lifetime welcome mail
        user.refresh_from_db()
        # Sending invoice mail if the payment successfully
        try:
            new_payment = Payment.objects.get(payment_id=payment_result.get("payment_id"))
            LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                func_name="pay_successfully", **{"payment": new_payment}
            )
        except Payment.DoesNotExist:
            pass
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def upgrade_education_public(self, request, *args, **kwargs):
        user = self.request.user
        if user.enterprise_members.filter().exists():
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        if current_plan.get_plan_obj().is_family_plan or user.pm_plan_family.exists():
            raise ValidationError(detail={"non_field_errors": [gen_error("7016")]})
        if current_plan.get_plan_type_alias() in [PLAN_TYPE_PM_LIFETIME]:
            raise ValidationError(detail={"non_field_errors": [gen_error("7017")]})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        education_email = validated_data.get("education_email") or ""
        education_type = validated_data.get("education_type")
        university = validated_data.get("university") or ""
        # If the user claimed or the education email claimed
        if EducationEmail.objects.filter(email__in=[email, education_email], verified=True).exists():
            raise ValidationError(detail={"non_field_errors": [gen_error("7019")]})

        if is_academic(email):
            user_education_email = user.education_emails.model.update_or_create(user.user_id, **{
                "email": email,
                "education_type": education_type,
                "university": university,
                "verified": False
            })

        elif is_academic(education_email):
            user_education_email = user.education_emails.model.update_or_create(user.user_id, **{
                "email": education_email,
                "education_type": education_type,
                "university": university,
                "verified": False
            })
        else:
            raise ValidationError(detail={"non_field_errors": [gen_error("7018")]})

        if user_education_email.email == email:
            promo_code = PromoCode.create_education_promo_code(**{"user_id": user.user_id})
            if not promo_code:
                raise ValidationError(detail={"non_field_errors": [gen_error("0008")]})
            user_education_email.promo_code = promo_code.code
            user_education_email.verified = True
            user_education_email.verification_token = None
            user_education_email.save()
            if user.activated:
                job = "education_pack_student_accepted"
                if education_type == "teacher":
                    job = "education_pack_teacher_accepted"
                if promo_code.expired_time:
                    expired_date = convert_readable_date(promo_code.expired_time, datetime_format="%d %b, %Y")
                else:
                    expired_date = None
                LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_locker_mail", **{
                        "user_ids": [user.user_id],
                        "job": job,
                        "scope": settings.SCOPE_PWD_MANAGER,
                        "username": email,
                        "code": promo_code.code,
                        "expired_date": expired_date,
                        "redeem_url": f"{settings.LOCKER_WEB_URL}/manage-plans"
                    }
                )

        else:
            new_user = request.data.get("new_user")
            if new_user is False:
                # Sending notification to verify the Education email
                job = "education_pack_student_email_confirmation"
                if education_type == "teacher":
                    job = "education_pack_teacher_email_confirmation"
                LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_locker_mail", **{
                        "destinations": [{
                            "email": user_education_email.email,
                            "name": request.data.get("full_name") or "there",
                            "language": request.data.get("language") or "en"
                        }],
                        "user_ids": [user.user_id],
                        "job": job,
                        "scope": settings.SCOPE_PWD_MANAGER,
                        "username": request.data.get("username") or email,
                        "locker_email": email,
                        "confirm_url": f"{settings.LOCKER_ID_WEB_URL}/confirmation/education-email/"
                                       f"{user_education_email.verification_token}",

                    }
                )
            else:
                promo_code = PromoCode.create_education_promo_code(**{"user_id": user.user_id})
                if not promo_code:
                    raise ValidationError(detail={"non_field_errors": [gen_error("0008")]})
                user_education_email.promo_code = promo_code.code
                user_education_email.verified = True
                user_education_email.verification_token = None
                user_education_email.save()

        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def verify_education_email(self, request, *args, **kwargs):
        token = self.request.data.get("token")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidAlgorithmError, ValueError):
            raise ValidationError(detail={"non_field_errors": [gen_error("7018")]})
        token_type = payload.get('token_type', None)
        user_id = payload.get('user_id', None)
        education_email = payload.get('education_email')
        expired_time = payload.get("expired_time")
        if token_type != TOKEN_TYPE_EDUCATION_CLAIM or expired_time < now():
            raise ValidationError(detail={"non_field_errors": [gen_error("7018")]})
        try:
            user_education_email = EducationEmail.objects.get(user_id=user_id, email=education_email)
        except EducationEmail.DoesNotExist:
            raise ValidationError(detail={"non_field_errors": [gen_error("7018")]})
        if user_education_email.verification_token != token:
            raise ValidationError(detail={"non_field_errors": [gen_error("7018")]})

        user = user_education_email.user
        email = user.get_from_cystack_id().get("email")
        promo_code = PromoCode.create_education_promo_code(**{"user_id": user.user_id})
        if not promo_code:
            raise ValidationError(detail={"non_field_errors": [gen_error("0008")]})
        user_education_email.promo_code = promo_code.code
        user_education_email.verified = True
        user_education_email.verification_token = None
        user_education_email.save()
        job = "education_pack_student_accepted"
        if user_education_email.education_type == "teacher":
            job = "education_pack_teacher_accepted"
        if promo_code.expired_time:
            expired_date = convert_readable_date(promo_code.expired_time, datetime_format="%d %b, %Y")
        else:
            expired_date = None
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
            func_name="notify_locker_mail", **{
                "user_ids": [user.user_id],
                "job": job,
                "scope": settings.SCOPE_PWD_MANAGER,
                "username": education_email,
                "code": promo_code.code,
                "expired_date": expired_date,
                "redeem_url": f"{settings.LOCKER_WEB_URL}/manage-plans"
            }
        )
        return Response(status=200, data={"success": True, "linked_email": email})

    @action(methods=["get"], detail=False)
    def current_plan(self, request, *args, **kwargs):
        user = self.request.user
        pm_current_plan = self.user_repository.get_current_plan(user=user)
        next_billing_time = pm_current_plan.get_next_billing_time()
        result = PMPlanSerializer(pm_current_plan.pm_plan, many=False).data
        result.update({
            "next_billing_time": next_billing_time,
            "duration": pm_current_plan.duration,
            "subscribing": pm_current_plan.is_subscription(),
            "is_trailing": pm_current_plan.is_trailing(),
            "cancel_at_period_end": pm_current_plan.is_cancel_at_period_end(),
            "payment_method": pm_current_plan.get_default_payment_method(),
            "number_members": pm_current_plan.get_current_number_members(),
            "is_family": user.pm_plan_family.exists() or pm_current_plan.pm_plan.is_family_plan,
            "personal_trial_applied": pm_current_plan.is_personal_trial_applied(),
            "extra_time": pm_current_plan.extra_time,
            "extra_plan": pm_current_plan.extra_plan or PLAN_TYPE_PM_PREMIUM if pm_current_plan.extra_time else None
        })
        return Response(status=200, data=result)

    @action(methods=["get"], detail=False)
    def next_attempt(self, request, *args, **kwargs):
        user = self.request.user
        current_plan = self.user_repository.get_current_plan(user=user)
        return Response(status=200, data={
            "next_payment_attempt": current_plan.get_next_retry_payment_date(),
        })

    @action(methods=["post"], detail=False)
    def upgrade_plan(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        new_plan = validated_data.get("plan")
        promo_code_obj = validated_data.get("promo_code_obj", None)
        duration = validated_data.get("duration", DURATION_MONTHLY)
        number_members = validated_data.get("number_members", 1)
        family_members = json.loads(json.dumps(validated_data.get("family_members", [])))
        card = request.data.get("card")
        bank_id = request.data.get("bank_id")
        payment_method = validated_data.get("payment_method")
        currency = validated_data.get("currency")
        metadata = {
            "currency": currency,
            "promo_code": promo_code_obj,
            "bank_id": bank_id,
            "card": card,
            "number_members": number_members,
            "family_members": list(family_members),
        }
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        # Not allow upgrade the personal plan if the user is in Enterprise plan
        if user.enterprise_members.filter(enterprise__locked=False).exists():
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})
        if payment_method == PAYMENT_METHOD_CARD:
            if not card:
                raise ValidationError({"non_field_errors": [gen_error("7007")]})
            if not card.get("id_card"):
                raise ValidationError({"non_field_errors": [gen_error("7007")]})

        # Calc payment price of new plan
        promo_code_value = promo_code_obj.code if promo_code_obj else None
        calc_payment = self._calc_payment(
            new_plan, duration=duration, currency=currency, number_members=number_members, promo_code=promo_code_value
        )
        immediate_payment = calc_payment.get("immediate_payment")

        if current_plan.is_personal_trial_applied() is False:
            utm_source = user.get_from_cystack_id().get("utm_source")
            if utm_source in LIST_UTM_SOURCE_PROMOTIONS:
                metadata.update({
                    "billing_cycle_anchor": calc_payment.get("next_billing_time")
                })
            else:
                metadata.update({
                    "trial_end": now() + TRIAL_PERSONAL_PLAN
                })

        payment = PaymentMethodFactory.get_method(
            user=user, scope=settings.SCOPE_PWD_MANAGER, payment_method=payment_method
        )
        payment_result = payment.upgrade_recurring_subscription(
            amount=immediate_payment, plan_type=new_plan.get_alias(), coupon=promo_code_obj, duration=duration,
            **metadata
        )
        update_result = payment_result.get("success")
        if update_result is False:
            if payment_result.get("stripe_error"):
                return Response(status=400, data={
                    "code": "7009",
                    "message": "Your card was declined (insufficient funds, etc...)",
                    "details": payment_result.get("error_details")
                })
            raise ValidationError({"non_field_errors": [gen_error("7009")]})

        # Set default payment method
        try:
            current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
            current_plan.set_default_payment_method(payment_method)
        except ObjectDoesNotExist:
            pass
        if payment_result.get("banking_invoice"):
            return Response(status=200, data=DetailInvoiceSerializer(
                payment_result.get("banking_invoice"), many=False
            ).data)
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def cancel_plan(self, request, *args, **kwargs):
        user = self.request.user
        current_plan = self.user_repository.get_current_plan(user=user)
        pm_plan_alias = current_plan.get_plan_type_alias()
        if pm_plan_alias == PLAN_TYPE_PM_FREE:
            raise ValidationError({"non_field_errors": [gen_error("7004")]})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        immediately = validated_data.get("immediately", False)
        end_time = self.user_repository.cancel_plan(
            user=user, scope=settings.SCOPE_PWD_MANAGER, immediately=immediately
        )
        if end_time:
            return Response(status=200, data={
                "user_ids": [user.user_id],
                "expired_date": datetime.utcfromtimestamp(end_time).strftime('%d/%m/%Y'),
                "current_plan": current_plan.get_plan_type_name()
            })
        return Response(status=200, data={"success": True})

    @action(methods=["get"], detail=False)
    def invoices(self, request, *args, **kwargs):
        user = self.request.user
        all_invoices = self.payment_repository.get_list_invoices_by_user(user=user).order_by('-created_time')
        from_param = self.check_int_param(self.request.query_params.get("from"))
        to_param = self.check_int_param(self.request.query_params.get("to"))
        if from_param:
            all_invoices = all_invoices.filter(created_time__lte=from_param)
        if to_param:
            all_invoices = all_invoices.filter(created_time__gt=to_param)

        queryset = self.filter_queryset(all_invoices)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=["get"], detail=False)
    def retrieve_invoice(self, request, *args, **kwargs):
        invoice = self.get_invoice()
        serializer = self.get_serializer(invoice, many=False)
        return Response(status=200, data=serializer.data)

    @action(methods=["post"], detail=False)
    def retry_invoice(self, request, *args, **kwargs):
        invoice = self.get_invoice()
        try:
            self.payment_repository.retry(payment=invoice)
            return Response(status=200, data={"success": True})
        except Exception as e:
            raise ValidationError({"non_field_errors": [gen_error("7009")]})

    @action(methods=["put"], detail=False)
    def set_invoice_status(self, request, *args, **kwargs):
        try:
            invoice = Payment.objects.get(
                payment_id=self.kwargs.get("pk"), scope=settings.SCOPE_PWD_MANAGER,
                status__in=[PAYMENT_STATUS_PENDING, PAYMENT_STATUS_PROCESSING],
                payment_method__in=[PAYMENT_METHOD_BANKING, PAYMENT_METHOD_WALLET]
            )
        except (Payment.DoesNotExist, ValueError):
            raise NotFound

        status = request.data.get("status")
        failure_reason = request.data.get("failure_reason", "")
        if status not in [PAYMENT_STATUS_PAID, PAYMENT_STATUS_FAILED]:
            raise ValidationError(detail={"status": ["Payment status is not valid"]})
        if status == PAYMENT_STATUS_PAID:
            # Set invoice succeed
            self.payment_repository.set_paid(payment=invoice)
            # Upgrade plan for user
            user = invoice.user
            plan_metadata = invoice.get_metadata()
            plan_metadata.update({"promo_code": invoice.promo_code})
            self.user_repository.update_plan(
                user=user, plan_type_alias=invoice.plan, duration=invoice.duration, scope=settings.SCOPE_PWD_MANAGER,
                **plan_metadata
            )
            # Send mail
            LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                func_name="pay_successfully", **{"payment": invoice}
            )
        else:
            self.payment_repository.set_failed(payment=invoice, failure_reason=failure_reason)
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def invoice_processing(self, request, *args, **kwargs):
        # ==== (DEPRECATED) ---- #
        raise NotFound
        # invoice = self.get_invoice()
        # if invoice.status != PAYMENT_STATUS_PENDING or invoice.payment_method != PAYMENT_METHOD_BANKING:
        #     raise NotFound
        # self.payment_repository.set_processing(payment=invoice)
        # return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def invoice_cancel(self, request, *args, **kwargs):
        # ==== (DEPRECATED) ---- #
        raise NotFound
        # invoice = self.get_invoice()
        # if invoice.status != PAYMENT_STATUS_PENDING:
        #     raise NotFound
        # # Delete this invoice
        # self.payment_repository.pending_cancel(payment=invoice)
        # return Response(status=200, data={"success": True})

    def _calc_payment(self, plan, duration=DURATION_MONTHLY, currency=CURRENCY_USD, number_members=1, promo_code=None,
                      allow_trial=True):
        """
        Calc total payment
        :param plan: (obj) PMPlan object
        :param duration: (str) Duration of the plan
        :param currency: (str) Currency: VND/USD
        :param number_members: (str)
        :param promo_code: (str) promo value
        :param allow_trial: (bool)
        :return:
        """
        current_plan = self.user_repository.get_current_plan(user=self.request.user, scope=settings.SCOPE_PWD_MANAGER)
        result = current_plan.calc_update_price(
            new_plan=plan, new_duration=duration, new_quantity=number_members, currency=currency, promo_code=promo_code,
            allow_trial=allow_trial
        )
        result["plan"] = PMPlanSerializer(plan, many=False).data
        return result

    def _calc_lifetime_payment_public(self, plan: str, currency=CURRENCY_USD, promo_code=None, user=None):
        plan = PMPlan.objects.get(alias=plan)
        # Get new plan price
        new_plan_price = plan.get_price(currency=currency)
        old_plan_discount = 0
        if user:
            current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
            if current_plan.get_plan_type_alias() == PLAN_TYPE_PM_LIFETIME and \
                    plan.get_alias() == PLAN_TYPE_PM_LIFETIME_FAMILY:
                old_plan_discount = math.floor(current_plan.pm_plan.get_price(currency=currency))

        # Calc discount
        error_promo = None
        promo_code_obj = None
        promo_description_en = None
        promo_description_vi = None
        if promo_code is not None and promo_code != "":
            promo_code_obj = PromoCode.check_valid(
                value=promo_code, current_user=None, new_plan=plan.get_alias()
            )
            if not promo_code_obj:
                error_promo = {"promo_code": ["This coupon is expired or incorrect"]}
            else:
                promo_description_en = promo_code_obj.description_en
                promo_description_vi = promo_code_obj.description_vi

        total_amount = new_plan_price
        next_billing_time = None

        # Discount and immediate payment
        total_amount = max(total_amount, 0)
        discount = promo_code_obj.get_discount(total_amount) if promo_code_obj else 0.0
        discount = discount + old_plan_discount
        immediate_amount = max(round(total_amount - discount, 2), 0)

        result = {
            "alias": plan.get_alias(),
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
            "quantity": 1,
            "plan": PMPlanSerializer(plan, many=False).data
        }
        return result

    @action(methods=["get"], detail=False)
    def plan_limit(self, request, *args, **kwargs):
        user = self.request.user
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)

        ciphers_statistic = Cipher.objects.filter(created_by_id=user)
        ciphers_statistic_data = {
            "total": ciphers_statistic.count(),
            CIPHER_TYPE_LOGIN: ciphers_statistic.filter(type=CIPHER_TYPE_LOGIN).count(),
            CIPHER_TYPE_NOTE: ciphers_statistic.filter(type=CIPHER_TYPE_NOTE).count(),
            CIPHER_TYPE_IDENTITY: ciphers_statistic.filter(type=CIPHER_TYPE_IDENTITY).count(),
            CIPHER_TYPE_CARD: ciphers_statistic.filter(type=CIPHER_TYPE_CARD).count(),
            CIPHER_TYPE_TOTP: ciphers_statistic.filter(type=CIPHER_TYPE_TOTP).count(),
            CIPHER_TYPE_CRYPTO_WALLET: ciphers_statistic.filter(type=CIPHER_TYPE_CRYPTO_WALLET).count(),
        }
        relay_addresses_statistic_data = {
            "total": user.relay_addresses.count()
        }
        plan_limit = self.user_repository.get_max_allow_cipher_type(user=user)
        plan_obj = current_plan.get_plan_obj()
        if plan_obj.allow_relay_premium() or user.is_active_enterprise_member():
            relay_addresses_limit = None
        else:
            relay_addresses_limit = MAX_FREE_RElAY_DOMAIN
        plan_limit.update({
            "relay_addresses": relay_addresses_limit
        })
        return Response(status=200, data={
            "ciphers": ciphers_statistic_data,
            "relay_addresses": relay_addresses_statistic_data,
            "plan_limit": plan_limit
        })
