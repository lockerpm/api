import json
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from shared.constants.transactions import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.payment_pwd_permission import PaymentPwdPermission
from cystack_models.models.payments.payments import Payment
from shared.utils.app import now
from v1_0.resources.serializers import PMPlanSerializer
from v1_0.payments.serializers import CalcSerializer, UpgradePlanSerializer, ListInvoiceSerializer, \
    DetailInvoiceSerializer
from v1_0.apps import PasswordManagerViewSet


class PaymentPwdViewSet(PasswordManagerViewSet):
    permission_classes = (PaymentPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "calc":
            self.serializer_class = CalcSerializer
        elif self.action == "upgrade_plan":
            self.serializer_class = UpgradePlanSerializer
        elif self.action in ["invoices", "list"]:
            self.serializer_class = ListInvoiceSerializer
        if self.action == "retrieve_invoice":
            self.serializer_class = DetailInvoiceSerializer
        
        return super(PaymentPwdViewSet, self).get_serializer_class()

    def get_invoice(self):
        try:
            invoice = self.payment_repository.get_invoice_by_user(
                user=self.request.user, invoice_id=self.kwargs.get("pk")
            )
            return invoice
        except Payment.DoesNotExist:
            raise NotFound

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
            "cancel_at_period_end": pm_current_plan.is_cancel_at_period_end(),
            "payment_method": pm_current_plan.get_default_payment_method(),
            "number_members": pm_current_plan.get_current_number_members(),
            "is_family": user.pm_plan_family.exists()
        })
        return Response(status=200, data=result)

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
            "key": validated_data.get("key"),
            "collection_name": validated_data.get("collection_name"),
        }
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        if current_plan.is_personal_trial_applied() is False:
            metadata.update({
                "trial_end": now() + TRIAL_PERSONAL_PLAN
            })
        # Calc payment price of new plan
        promo_code_value = promo_code_obj.code if promo_code_obj else None
        calc_payment = self._calc_payment(
            new_plan, duration=duration, currency=currency, number_members=number_members, promo_code=promo_code_value
        )
        immediate_payment = calc_payment.get("immediate_payment")

        if payment_method == PAYMENT_METHOD_CARD:
            if not card:
                raise ValidationError({"non_field_errors": [gen_error("7007")]})
            if not card.get("id_card"):
                raise ValidationError({"non_field_errors": [gen_error("7007")]})

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

        end_time = self.user_repository.cancel_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
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
        invoice = self.get_invoice()
        if invoice.status != PAYMENT_STATUS_PENDING or invoice.payment_method != PAYMENT_METHOD_BANKING:
            raise NotFound
        self.payment_repository.set_processing(payment=invoice)
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def invoice_cancel(self, request, *args, **kwargs):
        invoice = self.get_invoice()
        if invoice.status != PAYMENT_STATUS_PENDING:
            raise NotFound
        # Delete this invoice
        self.payment_repository.pending_cancel(payment=invoice)
        return Response(status=200, data={"success": True})

    def _calc_payment(self, plan, duration=DURATION_MONTHLY, currency=CURRENCY_USD, number_members=1, promo_code=None):
        """
        Calc total payment
        :param plan: (obj) PMPlan object
        :param duration: (str) Duration of the plan
        :param currency: (str) Currency: VND/USD
        :param number_members: (str)
        :param promo_code: (str) promo value
        :return:
        """
        current_plan = self.user_repository.get_current_plan(user=self.request.user, scope=settings.SCOPE_PWD_MANAGER)
        result = current_plan.calc_update_price(
            new_plan=plan, new_duration=duration, new_quantity=number_members, currency=currency, promo_code=promo_code
        )
        result["plan"] = PMPlanSerializer(plan, many=False).data
        return result
