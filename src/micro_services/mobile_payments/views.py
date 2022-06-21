import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from micro_services.apps import MicroServiceViewSet
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from shared.constants.transactions import *
from shared.error_responses.error import gen_error
from shared.permissions.micro_service_permissions.mobile_payment_permissions import MobilePaymentPermission
from shared.utils.app import now
from cystack_models.models.payments.payments import Payment
from micro_services.mobile_payments.serializers import UpgradePlanSerializer, MobileRenewalSerializer, \
    MobileDestroySubscriptionSerializer, MobileCancelSubscriptionSerializer


class MobilePaymentViewSet(MicroServiceViewSet):
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
        confirm_original_id = validated_data.get("confirm_original_id")
        currency = validated_data.get("currency", CURRENCY_USD)
        failure_reason = validated_data.get("failure_reason")
        is_trial_period = validated_data.get("is_trial_period", False)

        # Check confirm original id
        if confirm_original_id:
            mobile_original_id_registered = self.user_repository.get_mobile_user_plan(
                pm_mobile_subscription=confirm_original_id
            )
            # Downgrade plan of the existed mobile original id
            if mobile_original_id_registered and mobile_original_id_registered.user_id != user.user_id:
                self.user_repository.update_plan(
                    user=mobile_original_id_registered.user, plan_type_alias=PLAN_TYPE_PM_FREE,
                    scope=settings.SCOPE_PWD_MANAGER
                )

            # if self.user_repository.get_mobile_user_plan(pm_mobile_subscription=confirm_original_id):
            #     raise ValidationError(detail={"non_field_errors": [gen_error("7011")]})

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
        send_trial_mail = False
        try:
            current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
            current_plan.set_default_payment_method(PAYMENT_METHOD_MOBILE)
            if current_plan.is_personal_trial_applied() is False and is_trial_period is True:
                current_plan.personal_trial_applied = True
                current_plan.save()
                send_trial_mail = True
        except ObjectDoesNotExist:
            pass

        # Send mail
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="pay_successfully", **{"payment": new_payment}
        )
        if send_trial_mail is True:
            LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                func_name="trial_successfully", **{"payment": new_payment}
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

        # Check the invoice with mobile_invoice_id exists or not?
        mobile_invoice_exist = False
        if mobile_invoice_id:
            mobile_invoice_exist = Payment.objects.filter(mobile_invoice_id=mobile_invoice_id).exists()

        # If we done have any payment with mobile_invoice_id => Create new onew
        if mobile_invoice_exist is False:
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
        # Else, retrieving the payment with mobile_invoice_id
        else:
            new_payment = Payment.objects.filter(mobile_invoice_id=mobile_invoice_id).first()

        # Set paid or not
        if status == PAYMENT_STATUS_PAID:
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

            if new_payment.status != PAYMENT_STATUS_PAID:
                self.payment_repository.set_paid(payment=new_payment)
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
        cancel_at_period_end = validated_data.get("cancel_at_period_end")
        user = validated_data.get("user")
        current_plan = self.user_repository.get_current_plan(user=user, scope=scope)
        current_plan.cancel_at_period_end = cancel_at_period_end
        current_plan.save()
        if cancel_at_period_end is True:
            # Notify cancel plan here
            # CHANGE LATER ...
            # LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=True).run(
            #     func_name="cancel_plan", **{
            #         "user_id": user.user_id, "old_plan": current_plan.get_plan_type_name(),
            #         "expired_date": current_plan.end_period,
            #     }
            # )
            pass
        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def mobile_destroy_subscription(self, request, *args, **kwargs):
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