import json

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.micro_service_permissions.mobile_permission import MobilePaymentPermission
from locker_server.core.exceptions.payment_exception import CurrentPlanIsEnterpriseException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.shared.constants.transactions import *
from .serializers import UpgradePlanSerializer, MobileRenewalSerializer, MobileCancelSubscriptionSerializer, \
    MobileDestroySubscriptionSerializer


class MobilePaymentViewSet(APIBaseViewSet):
    permission_classes = (MobilePaymentPermission, )
    http_method_names = ["head", "options", "post", "put"]

    def get_serializer_class(self):
        if self.action == "upgrade_plan":
            self.serializer_class = UpgradePlanSerializer
        elif self.action == "mobile_renewal":
            self.serializer_class = MobileRenewalSerializer
        elif self.action == "mobile_cancel_subscription":
            self.serializer_class = MobileCancelSubscriptionSerializer
        elif self.action == "mobile_destroy_subscription":
            self.serializer_class = MobileDestroySubscriptionSerializer
        return super().get_serializer_class()

    @action(methods=["post"], detail=False)
    def upgrade_plan(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user_id = validated_data.get("user_id")
        family_members = json.loads(json.dumps(validated_data.get("family_members", [])))
        description = validated_data.get("description", "")
        promo_code = validated_data.get("promo_code")
        paid = validated_data.get("paid", True)
        duration = validated_data.get("duration", DURATION_MONTHLY)
        plan = validated_data.get("plan")
        platform = validated_data.get("platform")
        mobile_invoice_id = validated_data.get("mobile_invoice_id")
        mobile_original_id = validated_data.get("mobile_original_id")
        confirm_original_id = validated_data.get("confirm_original_id")
        currency = validated_data.get("currency", CURRENCY_USD)
        failure_reason = validated_data.get("failure_reason")
        is_trial_period = validated_data.get("is_trial_period", False)

        try:
            new_payment = self.mobile_payment_service.upgrade_plan(
                user_id=user_id, plan_alias=plan, duration=duration,
                promo_code=promo_code, paid=paid, failure_reason=failure_reason,
                is_trial_period=is_trial_period,
                payment_platform="iOS" if "ios" in request.path else "Android",
                scope=settings.SCOPE_PWD_MANAGER,
                **{
                    "description": description,
                    "failure_reason"
                    "family_members": family_members,
                    "platform": platform,
                    "mobile_invoice_id": mobile_invoice_id,
                    "mobile_original_id": mobile_original_id,
                    "confirm_original_id": confirm_original_id,
                    "currency": currency,
                }
            )
        except UserDoesNotExistException:
            raise ValidationError(detail={"user_id": ["User does not exist"]})

        return Response(status=status.HTTP_200_OK, data={
            "success": True,
            "scope": new_payment.scope,
            "payment_id": new_payment.payment_id
        })

    @action(methods=["post"], detail=False)
    def mobile_renewal(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        description = validated_data.get("description", "")
        promo_code = validated_data.get("promo_code")
        payment_status = validated_data.get("status", True)
        duration = validated_data.get("duration", DURATION_MONTHLY)
        plan = validated_data.get("plan")
        platform = validated_data.get("platform")
        mobile_invoice_id = validated_data.get("mobile_invoice_id")
        mobile_original_id = validated_data.get("mobile_original_id")
        currency = validated_data.get("currency", CURRENCY_USD)
        failure_reason = validated_data.get("failure_reason")
        end_period = validated_data.get("end_period")

        try:
            new_payment = self.mobile_payment_service.mobile_renewal(
                status=payment_status, plan_alias=plan, duration=duration, promo_code=promo_code,
                failure_reason=failure_reason, payment_platform=platform,
                scope=settings.SCOPE_PWD_MANAGER, **{
                    "currency": currency,
                    "end_period": end_period,
                    "mobile_invoice_id": mobile_invoice_id,
                    "mobile_original_id": mobile_original_id,
                    "description": description
                }
            )
        except UserDoesNotExistException:
            raise ValidationError(detail={
                "mobile_original_id": ["The mobile subscription id does not exist"]
            })
        except CurrentPlanIsEnterpriseException:
            return Response(status=status.HTTP_200_OK, data={"is_update_personal_to_enterprise": True})
        return Response(status=status.HTTP_200_OK, data={
            "success": True,
            "user_id": new_payment.user.user_id,
            "scope": new_payment.scope,
            "status": new_payment.status,
            "failure_reason": failure_reason,
            "payment_id": new_payment.payment_id
        })

    @action(methods=["put"], detail=False)
    def mobile_cancel_subscription(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        cancel_at_period_end = validated_data.get("cancel_at_period_end")
        mobile_original_id = validated_data.get("mobile_original_id")
        end_period = validated_data.get("end_period")

        try:
            self.mobile_payment_service.mobile_cancel_subscription(
                mobile_original_id=mobile_original_id, cancel_at_period_end=cancel_at_period_end,
                end_period=end_period,
                plan_alias=request.data.get("plan"),
                scope=settings.SCOPE_PWD_MANAGER
            )
        except UserDoesNotExistException:
            raise ValidationError(detail={"mobile_original_id": ["The mobile subscription id does not exist"]})
        except CurrentPlanIsEnterpriseException:
            return Response(status=status.HTTP_200_OK, data={"is_update_personal_to_enterprise": True})
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["put"], detail=False)
    def mobile_destroy_subscription(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        mobile_original_id = validated_data.get("mobile_original_id")

        try:
            old_plan_name = self.mobile_payment_service.mobile_destroy_subscription(
                plan_alias="", mobile_original_id=mobile_original_id,
                scope=settings.SCOPE_PWD_MANAGER
            )
        except UserDoesNotExistException:
            raise ValidationError(detail={"mobile_original_id": ["The mobile subscription id does not exist"]})

        return Response(status=status.HTTP_200_OK, data={"old_plan": old_plan_name})
