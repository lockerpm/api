import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action

from micro_services.apps import MicroServiceViewSet
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from shared.constants.transactions import *
from shared.permissions.micro_service_permissions.mobile_payment_permissions import MobilePaymentPermission
from shared.utils.app import now
from cystack_models.models.payments.payments import Payment
from micro_services.mobile_payments.serializers import UpgradePlanSerializer, MobileRenewalSerializer, \
    MobileCancelSubscriptionSerializer


class MobilePaymentViewSet(MicroServiceViewSet):
    permission_classes = (MobilePaymentPermission,)
    http_method_names = ["head", "options", "post", "put"]

    def get_serializer_class(self):
        if self.action == "upgrade_plan":
            self.serializer_class = UpgradePlanSerializer
        elif self.action == "mobile_renewal":
            self.serializer_class = MobileRenewalSerializer
        elif self.action == "mobile_cancel_subscription":
            self.serializer_class = MobileCancelSubscriptionSerializer
        return super(MobilePaymentViewSet, self).get_serializer_class()

    @action(methods=["post"], detail=False)
    def upgrade_plan(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = validated_data.get("user")
        family_members = json.loads(json.dumps(validated_data.get("family_members", [])))
        description = validated_data.get("description", "")
        promo_code = validated_data.get("promo_code")
        paid = validated_data.get("paid", True)
        duration = validated_data.get("duration", DURATION_MONTHLY)
        plan = validated_data.get("plan")
        platform = validated_data.get("platform")
        mobile_invoice_id = validated_data.get("mobile_invoice_id")
        mobile_original_id = validated_data.get("mobile_original_id")
        currency = validated_data.get("currency", CURRENCY_USD)
        failure_reason = validated_data.get("failure_reason")

        new_payment_data = {
            "user": user,
            "description": description,
            "plan": plan,
            "duration": duration,
            "promo_code": promo_code,
            "currency": currency,
            "payment_method": PAYMENT_METHOD_MOBILE,
            "mobile_invoice_id": mobile_invoice_id,
            "metadata": {
                "platform": platform,
                "mobile_invoice_id": mobile_invoice_id,
                "mobile_original_id": mobile_original_id,
                "user_id": user.user_id,
                "scope": settings.SCOPE_PWD_MANAGER,
                "family_members": list(family_members),
                "key": validated_data.get("key"),
                "collection_name": validated_data.get("collection_name")
            }
        }

        # Create new payment
        new_payment = Payment.create(**new_payment_data)
        new_payment = self.payment_repository.set_paid(payment=new_payment)

        # Set pm mobile subscription
        pm_user_plan = self.user_repository.get_current_plan(user=new_payment.user, scope=new_payment.scope)
        pm_user_plan.pm_mobile_subscription = mobile_original_id
        pm_user_plan.save()

        # Upgrade new plan
        subscription_metadata = {
            "start_period": validated_data.get("start_period"),
            "end_period": validated_data.get("end_period"),
            "promo_code": new_payment.promo_code,
            "family_members": list(family_members),
            "key": validated_data.get("key"),
            "collection_name": validated_data.get("collection_name")
        }
        self.user_repository.update_plan(
            new_payment.user, plan_type_alias=new_payment.plan, duration=new_payment.duration,
            scope=settings.SCOPE_PWD_MANAGER,
            **subscription_metadata
        )

        # Set default payment method
        try:
            current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
            current_plan.set_default_payment_method(PAYMENT_METHOD_MOBILE)
        except ObjectDoesNotExist:
            pass

        # Send mail
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="pay_successfully", **{"payment": new_payment}
        )
        return Response(status=200, data={
            "success": True,
            "scope": new_payment.scope,
            "payment_id": new_payment.payment_id
        })

    @action(methods=["post"], detail=False)
    def mobile_renewal(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = validated_data.get("user")
        description = validated_data.get("description", "")
        promo_code = validated_data.get("promo_code")
        status = validated_data.get("status", True)
        duration = validated_data.get("duration", DURATION_MONTHLY)
        plan = validated_data.get("plan")
        platform = validated_data.get("platform")
        mobile_invoice_id = validated_data.get("mobile_invoice_id")
        mobile_original_id = validated_data.get("mobile_original_id")
        currency = validated_data.get("currency", CURRENCY_USD)
        failure_reason = validated_data.get("failure_reason")
        end_period = validated_data.get("end_period")

        new_payment_data = {
            "user": user,
            "description": description,
            "plan": plan,
            "duration": duration,
            "promo_code": promo_code,
            "currency": currency,
            "payment_method": PAYMENT_METHOD_MOBILE,
            "mobile_invoice_id": mobile_invoice_id,
            "metadata": {
                "platform": platform,
                "mobile_invoice_id": mobile_invoice_id,
                "mobile_original_id": mobile_original_id,
                "user_id": user.user_id,
                "scope": settings.SCOPE_PWD_MANAGER,
                "key": validated_data.get("key"),
                "collection_name": validated_data.get("collection_name")
            }
        }
        # Create new payment
        new_payment = Payment.create(**new_payment_data)
        # Set paid or not
        if status == PAYMENT_STATUS_PAID:
            self.payment_repository.set_paid(payment=new_payment)
            # Upgrade new plan
            subscription_metadata = {
                "end_period": end_period,
                "promo_code": new_payment.promo_code,
                "key": validated_data.get("key"),
                "collection_name": validated_data.get("collection_name")
            }
            self.user_repository.update_plan(
                new_payment.user, plan_type_alias=new_payment.plan, duration=new_payment.duration,
                scope=settings.SCOPE_PWD_MANAGER,
                **subscription_metadata
            )
            # Set default payment method
            try:
                current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
                current_plan.set_default_payment_method(PAYMENT_METHOD_MOBILE)
            except ObjectDoesNotExist:
                pass
            # Send mail
            LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                func_name="pay_successfully", **{"payment": new_payment}
            )
        elif status == PAYMENT_STATUS_PAST_DUE:
            self.payment_repository.set_past_due(payment=new_payment, failure_reason=failure_reason)
        else:
            self.payment_repository.set_failed(payment=new_payment, failure_reason=failure_reason)

        return Response(status=200, data={
            "success": True,
            "user_id": user.user_id,
            "scope": new_payment.scope,
            "status": new_payment.status,
            "failure_reason": failure_reason,
            "payment_id": new_payment.payment_id
        })

    @action(methods=["put"], detail=False)
    def mobile_cancel_subscription(self, request, *args, **kwargs):
        scope = settings.SCOPE_PWD_MANAGER
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        user = validated_data.get("user")
        payment_data = {}
        current_plan = self.user_repository.get_current_plan(user=user, scope=scope)
        old_plan = current_plan.get_plan_type_name()
        current_plan.cancel_mobile_subscription()

        # if this plan is canceled because the user is added into family plan => Not notify
        if not current_plan.user.pm_plan_family.exists():
            self.user_repository.update_plan(
                user=user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=scope
            )
            # Notify downgrade here
            LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=True).run(
                func_name="downgrade_plan", **{
                    "user_id": user.user_id, "old_plan": old_plan, "downgrade_time": now(),
                    "scope": settings.SCOPE_PWD_MANAGER, **{"payment_data": payment_data}
                }
            )
        return Response(status=200, data={"old_plan": old_plan})