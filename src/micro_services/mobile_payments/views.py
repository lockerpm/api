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
from micro_services.mobile_payments.serializers import UpgradePlanSerializer


class MobilePaymentViewSet(MicroServiceViewSet):
    permission_classes = (MobilePaymentPermission,)
    http_method_names = ["head", "options", "post", "put"]

    def get_serializer_class(self):
        if self.action == "upgrade_plan":
            self.serializer_class = UpgradePlanSerializer
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
        mobile_transaction_id = validated_data.get("mobile_transaction_id")
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
            "metadata": {
                "platform": platform,
                "mobile_transaction_id": mobile_transaction_id,
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

        # Upgrade new plan
        subscription_metadata = {
            # "start_period": start_period,
            # "end_period": end_period,
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
