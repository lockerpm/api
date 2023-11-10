import json
from datetime import datetime

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.payment_pwd_permission import PaymentPwdPermission
from locker_server.core.exceptions.enterprise_member_repository import EnterpriseMemberExistedException
from locker_server.core.exceptions.payment_exception import *
from locker_server.core.exceptions.plan_repository import PlanDoesNotExistException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.exceptions.user_plan_exception import EnterpriseTrialCodeInvalidException, \
    EnterpriseTrialAppliedException
from locker_server.shared.constants.transactions import *
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY
from locker_server.shared.utils.app import now
from .serializers import CalcSerializer, ListInvoiceSerializer, AdminUpgradePlanSerializer, UpgradeTrialSerializer, \
    UpgradeThreePromoSerializer, UpgradeLifetimeSerializer, UpgradeLifetimePublicSerializer, \
    UpgradeEducationPublicSerializer, CancelPlanSerializer, UpgradePlanSerializer, DetailInvoiceSerializer, \
    CalcLifetimePublicSerializer


class PaymentPwdViewSet(APIBaseViewSet):
    permission_classes = (PaymentPwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_throttles(self):
        return super().get_throttles()

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
        return super().get_serializer_class()

    def get_invoice(self):
        invoice = self.payment_service.get_by_user_id(
            user_id=self.request.user.user_id, payment_id=self.kwargs.get("pk")
        )
        if not invoice:
            raise PaymentInvoiceDoesNotExistException
        return invoice

    def get_user(self, user_id: int):
        try:
            return self.user_service.retrieve_by_id(user_id=user_id)
        except UserDoesNotExistException:
            return None

    def allow_upgrade_enterprise_trial(self, user):
        if self.enterprise_service.is_in_enterprise(user_id=user.user_id):
            raise ValidationError({"non_field_errors": [gen_error("7015")]})

        pm_current_plan = self.user_service.get_current_plan(user=user)
        if pm_current_plan.enterprise_trial_applied is True:
            raise ValidationError({"non_field_errors": [gen_error("7013")]})

        return pm_current_plan

    def get_queryset(self):
        all_invoices = self.payment_service.list_all_invoices(**{
            "from": self.check_int_param(self.request.query_params.get("from")),
            "to": self.check_int_param(self.request.query_params.get("to")),
            "status": self.request.query_params.get("status"),
            "payment_method": self.request.query_params.get("payment_method")
        })
        return all_invoices

    def list(self, request, *args, **kwargs):
        return super(PaymentPwdViewSet, self).list(request, *args, **kwargs)

    @action(methods=["get"], detail=False)
    def user_invoices(self, request, *args, **kwargs):
        user = self.get_user(user_id=kwargs.get("pk"))
        if not user:
            raise NotFound

        invoices = self.payment_service.list_all_invoices(**{
            "from": self.check_int_param(self.request.query_params.get("from")),
            "to": self.check_int_param(self.request.query_params.get("to")),
            "status": self.request.query_params.get("status"),
            "payment_method": self.request.query_params.get("payment_method"),
            "user_id": user.user_id
        })
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

        try:
            self.payment_service.admin_upgrade_plan(
                user_id=user.user_id, plan_alias=plan_alias, end_period=end_period,
                scope=settings.SCOPE_PWD_MANAGER
            )
        except PlanDoesNotExistException:
            raise ValidationError(detail={"plan_alias": ["This plan does not exist"]})
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def calc(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        promo_code = validated_data.get("promo_code")
        duration = validated_data.get("duration", DURATION_MONTHLY)
        plan_alias = validated_data.get("plan_alias")
        number_members = validated_data.get("number_members", 1)
        currency = validated_data.get("currency", CURRENCY_USD)
        # Calc payment
        try:
            result = self.payment_service.calc_payment(
                user_id=self.request.user.user_id,
                plan_alias=plan_alias,
                duration=duration,
                currency=currency,
                number_members=number_members,
                promo_code=promo_code
            )
        except PlanDoesNotExistException:
            raise ValidationError(detail={"plan_alias": ["This plan alias does not exist"]})
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def check_trial(self, request, *args, **kwargs):
        user = self.request.user
        current_plan = self.user_service.get_current_plan(user=user)
        return Response(status=status.HTTP_200_OK, data={
            "personal_trial_applied": current_plan.is_personal_trial_applied()
        })

    @action(methods=["post"], detail=False)
    def upgrade_trial(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        current_plan = self.user_service.get_current_plan(user=user)
        trial_applied = current_plan.is_personal_trial_applied()
        if trial_applied is True:
            raise ValidationError({"non_field_errors": [gen_error("7013")]})
        if self.enterprise_service.is_in_enterprise(user_id=user.user_id, enterprise_locked=False):
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})

        plan_metadata = {
            "start_period": now(),
            "end_period": now() + TRIAL_PERSONAL_PLAN
        }
        try:
            self.payment_service.upgrade_trial(
                user_id=user.user_id, trial_plan_alias=validated_data.get("trial_plan"),
                **plan_metadata
            )
        except PlanDoesNotExistException:
            raise ValidationError(detail={"trial_plan": ["The trial plan does not exist"]})

        # Send trial mail
        BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="trial_successfully", **{
                "user_id": user.user_id,
                "plan": validated_data.get("trial_plan"),
                "payment_method": None,
                "duration": TRIAL_PERSONAL_DURATION_TEXT
            }
        )
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def upgrade_trial_enterprise_by_code(self, request, *args, **kwargs):
        token = request.data.get("token")
        try:
            user = self.payment_service.upgrade_trial_enterprise_by_code(
                token=token, secret_key=settings.SECRET_KEY, scope=settings.SCOPE_PWD_MANAGER
            )
        except (EnterpriseTrialCodeInvalidException, UserDoesNotExistException):
            raise ValidationError(detail={"token": ["The upgrade token is not valid"]})
        except EnterpriseMemberExistedException:
            raise ValidationError({"non_field_errors": [gen_error("7015")]})
        except EnterpriseTrialAppliedException:
            raise ValidationError({"non_field_errors": [gen_error("7013")]})
        # Send trial mail
        BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="trial_enterprise_successfully", **{
                "user_id": user.user_id,
                "scope": settings.SCOPE_PWD_MANAGER,
            }
        )
        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def generate_trial_enterprise_code(self, request, *args, **kwargs):
        user = self.request.user
        try:
            token = self.payment_service.generate_trial_enterprise_code(
                user_id=user.user_id,
                secret_key=settings.SECRET_KEY,
                enterprise_name=request.data.get("enterprise_name", "My Enterprise")
            )
        except EnterpriseMemberExistedException:
            raise ValidationError({"non_field_errors": [gen_error("7015")]})
        except EnterpriseTrialAppliedException:
            raise ValidationError({"non_field_errors": [gen_error("7013")]})

        return Response(status=status.HTTP_200_OK, data={"token": token})

    @action(methods=["post"], detail=False)
    def upgrade_lifetime(self, request, *args, **kwargs):
        user = self.request.user
        if self.enterprise_service.is_in_enterprise(user_id=user.user_id):
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})
        # current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        code = validated_data.get("code")

        try:
            self.payment_service.upgrade_lifetime(user_id=user.user_id, code=code, scope=settings.SCOPE_PWD_MANAGER)
        except EnterpriseMemberExistedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})
        except PaymentPromoCodeInvalidException:
            raise ValidationError(detail={"code": ["This code is expired or invalid"]})
        except PaymentFailedByUserInFamilyException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7016")]})
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def upgrade_three_promo(self, request, *args, **kwargs):
        user = self.request.user
        card = request.data.get("card")
        if not card:
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        if not card.get("id_card"):
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            payment_result = self.payment_service.upgrade_three_promo(
                user_id=user.user_id,
                card=card,
                promo_code=validated_data.get("promo_code"),
                scope=settings.SCOPE_PWD_MANAGER
            )
        except CurrentPlanDoesNotSupportOperatorException:
            raise ValidationError({"non_field_errors": [gen_error("7010")]})
        except PaymentPromoCodeInvalidException:
            raise ValidationError(detail={"promo_code": ["This coupon is expired or invalid"]})
        update_result = payment_result.get("success")
        if update_result is False:
            if payment_result.get("stripe_error"):
                return Response(status=status.HTTP_400_BAD_REQUEST, data={
                    "code": "7009",
                    "message": "Your card was declined (insufficient funds, etc...)",
                    "details": payment_result.get("error_details")
                })
            raise ValidationError({"non_field_errors": [gen_error("7009")]})
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def calc_lifetime_public(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        promo_code = validated_data.get("promo_code")
        plan_alias = validated_data.get("plan_alias")
        currency = validated_data.get("currency", CURRENCY_USD)
        email = validated_data.get("email")
        try:
            user = self.user_service.retrieve_by_email(email=email)
        except UserDoesNotExistException:
            user = None

        # Calc payment
        result = self.payment_service.calc_lifetime_payment_public(
            plan_alias=plan_alias,
            currency=currency,
            promo_code=promo_code,
            user=user
        )
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["post"], detail=False)
    def upgrade_lifetime_public(self, request, *args, **kwargs):
        user = self.request.user
        card = request.data.get("card")
        if not card:
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        if not card.get("id_card"):
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            payment_result = self.payment_service.upgrade_lifetime_public(
                user_id=user.user_id, card=card,
                promo_code=validated_data.get("promo_code"),
                plan_alias=validated_data.get("plan_alias") or PLAN_TYPE_PM_LIFETIME,
                scope=settings.SCOPE_PWD_MANAGER
            )
        except EnterpriseMemberExistedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})
        except PaymentPromoCodeInvalidException:
            raise ValidationError(detail={"promo_code": ["This coupon is expired or invalid"]})
        except PaymentFailedByUserInFamilyException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7016")]})
        except PaymentFailedByUserInLifetimeException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7017")]})
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            from locker_server.shared.log.cylog import CyLog
            CyLog.error(**{"message": f"[!] upgrade_lifetime_public error:::{tb}"})
            raise e
        update_result = payment_result.get("success")
        if update_result is False:
            if payment_result.get("stripe_error"):
                return Response(status=status.HTTP_400_BAD_REQUEST, data={
                    "code": "7009",
                    "message": "Your card was declined (insufficient funds, etc...)",
                    "details": payment_result.get("error_details")
                })
            raise ValidationError({"non_field_errors": [gen_error("7009")]})
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def upgrade_education_public(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        education_email = validated_data.get("education_email") or ""
        education_type = validated_data.get("education_type")
        university = validated_data.get("university") or ""
        try:
            self.payment_service.upgrade_education_public(
                user_id=user.user_id,
                email=email, education_email=education_email,
                education_type=education_type, university=university,
                scope=settings.SCOPE_PWD_MANAGER,
                new_user=request.data.get("new_user"),
                user_fullname=request.data.get("full_name"),
                username=request.data.get("username"),
                locker_web_url=settings.LOCKER_WEB_URL,
                locker_id_url=settings.LOCKER_ID_WEB_URL

            )
        except EnterpriseMemberExistedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})
        except PaymentFailedByUserInFamilyException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7016")]})
        except PaymentFailedByUserInLifetimeException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7017")]})
        except EducationEmailClaimedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7019")]})
        except EducationEmailInvalidException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7018")]})
        except CreateEducationEmailPromoCodeFailedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("0008")]})
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def verify_education_email(self, request, *args, **kwargs):
        token = self.request.data.get("token")
        try:
            email = self.payment_service.verify_education_email(
                token=token,
                secret_key=settings.SECRET_KEY,
                scope=settings.SCOPE_PWD_MANAGER,
                locker_web_url=settings.LOCKER_WEB_URL
            )
        except EducationEmailInvalidException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7018")]})
        except CreateEducationEmailPromoCodeFailedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("0008")]})
        return Response(status=status.HTTP_200_OK, data={"success": True, "linked_email": email})

    @action(methods=["get"], detail=False)
    def current_plan(self, request, *args, **kwargs):
        user = self.request.user
        current_plan = self.user_service.get_current_plan(user=user)
        next_billing_time = current_plan.get_next_billing_time()
        result = current_plan.pm_plan.to_json()
        result.update({
            "next_billing_time": next_billing_time,
            "duration": current_plan.duration,
            "subscribing": current_plan.is_subscription(),
            "is_trailing": current_plan.is_trialing(),
            "cancel_at_period_end": current_plan.is_cancel_at_period_end(),
            "payment_method": current_plan.default_payment_method,
            "number_members": current_plan.number_members,
            "is_family": self.family_service.is_in_family_plan(user_plan=current_plan),
            "personal_trial_applied": current_plan.is_personal_trial_applied(),
            "extra_time": current_plan.extra_time,
            "extra_plan": current_plan.extra_plan or PLAN_TYPE_PM_PREMIUM if current_plan.extra_time else None
        })
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def next_attempt(self, request, *args, **kwargs):
        user = self.request.user
        current_plan = self.user_service.get_current_plan(user=user)
        return Response(status=status.HTTP_200_OK, data={
            "next_payment_attempt": current_plan.get_next_retry_payment_date()
        })

    @action(methods=["post"], detail=False)
    def upgrade_plan(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        plan_alias = validated_data.get("plan_alias")
        promo_code = validated_data.get("promo_code", None)
        duration = validated_data.get("duration", DURATION_MONTHLY)
        number_members = validated_data.get("number_members", 1)
        family_members = json.loads(json.dumps(validated_data.get("family_members", [])))
        payment_method = validated_data.get("payment_method")
        card = request.data.get("card")
        bank_id = request.data.get("bank_id")

        try:
            payment_result = self.payment_service.upgrade_plan(
                user_id=user.user_id, plan_alias=plan_alias, duration=duration, number_memberS=number_members,
                promo_code=promo_code, scope=settings.SCOPE_PWD_MANAGER, **{
                    "payment_method": payment_method,
                    "bank_id": bank_id,
                    "card": card,
                    "family_members": family_members,
                }
            )
        except PlanDoesNotExistException:
            raise ValidationError(detail={'plan_alias': ["This plan does not exist"]})
        except PaymentPromoCodeInvalidException:
            raise ValidationError(detail={"promo_code": ["This coupon is expired or invalid"]})
        except UpgradePlanNotChangeException:
            raise ValidationError(detail={"plan": ["Plan is not changed"]})
        except UpgradePaymentMethodChangedException:
            raise ValidationError(detail={
                "payment_method": ["This payment method must be same as current payment method of your plan"]
            })
        except MaxFamilyMemberReachedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7012")]})
        except PaymentNotFoundCardException:
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        except EnterpriseMemberExistedException:
            raise ValidationError(detail={"non_field_errors": [gen_error("7015")]})

        update_result = payment_result.get("success")
        if update_result is False:
            if payment_result.get("stripe_error"):
                return Response(status=status.HTTP_400_BAD_REQUEST, data={
                    "code": "7009",
                    "message": "Your card was declined (insufficient funds, etc...)",
                    "details": payment_result.get("error_details")
                })
            raise ValidationError({"non_field_errors": [gen_error("7009")]})
        if payment_result.get("banking_invoice"):
            return Response(status=status.HTTP_200_OK, data=DetailInvoiceSerializer(
                payment_result.get("banking_invoice"), many=False
            ).data)
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def cancel_plan(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        immediately = validated_data.get("immediately", False)
        try:
            current_plan_name, end_time = self.payment_service.cancel_plan(
                user_id=user.user_id, immediately=immediately
            )
        except CannotCancelDefaultPlanException:
            raise ValidationError({"non_field_errors": [gen_error("7004")]})
        if end_time:
            return Response(status=status.HTTP_200_OK, data={
                "user_ids": [user.user_id],
                "expired_date": datetime.utcfromtimestamp(end_time).strftime('%d/%m/%Y'),
                "current_plan": current_plan_name
            })
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["get"], detail=False)
    def invoices(self, request, *args, **kwargs):
        user = self.request.user
        all_invoices = self.payment_service.list_user_invoices(user_id=user.user_id, **{
            "from": self.check_int_param(self.request.query_params.get("from")),
            "to": self.check_int_param(self.request.query_params.get("to"))
        })
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
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["get"], detail=False)
    def plan_limit(self, request, *args, **kwargs):
        user = self.request.user
        result = self.payment_service.plan_limit(user_id=user.user_id)
        return Response(status=status.HTTP_200_OK, data=result)
