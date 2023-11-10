import traceback

import stripe
import stripe.error

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.exceptions.country_exception import CountryDoesNotExistException
from locker_server.core.exceptions.enterprise_exception import EnterpriseDoesNotExistException
from locker_server.core.exceptions.payment_exception import PaymentInvoiceDoesNotExistException
from locker_server.core.exceptions.plan_repository import PlanDoesNotExistException
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED, E_MEMBER_ROLE_MEMBER, \
    E_MEMBER_ROLE_ADMIN
from locker_server.shared.constants.transactions import PLAN_TYPE_PM_ENTERPRISE, PAYMENT_METHOD_CARD
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.external_services.payment_method.payment_method_factory import PaymentMethodFactory
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.utils.app import now
from .serializers import *
from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.enterprise_permissions.payment_pwd_permission import \
    EnterprisePaymentPwdPermission


class PaymentPwdViewSet(APIBaseViewSet):
    permission_classes = (EnterprisePaymentPwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListInvoiceSerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailInvoiceSerializer
        elif self.action == "calc":
            self.serializer_class = CalcSerializer
        elif self.action == "calc_public":
            self.serializer_class = CalcPublicSerializer
        elif self.action == "upgrade_plan":
            self.serializer_class = UpgradePlanSerializer
        elif self.action == "upgrade_plan_public":
            self.serializer_class = UpgradePlanPublicSerializer
        elif self.action == "billing_address":
            self.serializer_class = BillingAddressSerializer
        return super().get_serializer_class()

    def get_enterprise(self):
        try:
            enterprise = self.enterprise_service.get_enterprise_by_id(
                enterprise_id=self.kwargs.get("pk")
            )
            self.check_object_permissions(request=self.request, obj=enterprise)
            return enterprise
        except EnterpriseDoesNotExistException:
            raise NotFound

    def get_queryset(self):
        enterprise = self.get_enterprise()
        query_params = self.request.query_params
        invoices = self.payment_service.list_all_invoices(**{
            "enterprise_id": enterprise.enterprise_id,
            "status": query_params.get("status"),
            "from": self.check_int_param(query_params.get("from")),
            "to": self.check_int_param(query_params.get("to")),
            "payment_method": query_params.get("payment_method")
        })
        return invoices

    def get_object(self):
        enterprise = self.get_enterprise()
        try:
            invoice = self.payment_service.get_by_payment_id(
                payment_id=self.kwargs.get("payment_id")
            )
            if invoice.enterprise_id != enterprise.enterprise_id:
                raise NotFound

            return invoice
        except PaymentInvoiceDoesNotExistException:
            raise NotFound

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(methods=["get"], detail=False)
    def current_plan(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        primary_admin = self.enterprise_service.get_primary_member(enterprise_id=enterprise.enterprise_id).user
        enterprise_plan = self.payment_service.get_pm_plan_by_alias(alias=PLAN_TYPE_PM_ENTERPRISE)
        current_plan = self.user_service.get_current_plan(user=primary_admin)
        result = enterprise_plan.to_json()
        result.update({
            "start_period": current_plan.start_period,
            "next_billing_time": current_plan.get_next_billing_time(),
            "duration": current_plan.duration,
            "is_trailing": current_plan.is_trialing(),
            "cancel_at_period_end": current_plan.is_cancel_at_period_end(),
            "payment_method": current_plan.get_default_payment_method(),
            "enterprise": {
                "current_members": self.enterprise_member_service.count_enterprise_members(**{
                    "enterprise_id": enterprise.enterprise_id,
                    "status": E_MEMBER_STATUS_CONFIRMED,
                    "is_activated": True
                })
            },
            "stripe_subscription": current_plan.pm_stripe_subscription,
            "primary_admin": primary_admin.user_id,
        })
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def next_attempt(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        primary_admin = self.enterprise_service.get_primary_member(
            enterprise_id=enterprise.enterprise_id
        ).user
        current_plan = self.user_service.get_current_plan(user=primary_admin)
        return Response(
            status=status.HTTP_200_OK,
            data={
                "next_payment_attempt": current_plan.get_next_retry_payment_date(),
            }
        )

    @action(methods=["get", "post"], detail=False)
    def cards(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        primary_admin = self.enterprise_service.get_primary_member(
            enterprise_id=enterprise.enterprise_id
        ).user
        primary_admin_plan = self.user_service.get_current_plan(user=primary_admin)
        stripe_subscription = primary_admin_plan.get_stripe_subscription()
        stripe_default_payment_method = stripe_subscription.default_payment_method if stripe_subscription else None
        return Response(
            status=status.HTTP_200_OK,
            data={
                "primary_admin": primary_admin.user_id,
                "stripe_default_payment_method": stripe_default_payment_method
            }
        )

    @action(methods=["get"], detail=False)
    def add_card_subscription(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        primary_admin = self.enterprise_service.get_primary_member(
            enterprise_id=enterprise.enterprise_id
        ).user
        primary_admin_plan = self.user_service.get_current_plan(user=primary_admin)
        stripe_subscription = primary_admin_plan.get_stripe_subscription()
        # If the Enterprise plan doesn't have Stripe Subscription => Subscribe with stripe
        if primary_admin_plan.pm_plan.is_team_plan and stripe_subscription is None and \
                primary_admin_plan.end_period and primary_admin_plan.end_period > now():
            number_members = self.enterprise_member_service.count_enterprise_members(**{
                "enterprise_id": enterprise.enterprise_id,
                "status": E_MEMBER_STATUS_CONFIRMED,
                "is_activated": True
            })
            metadata = {
                "currency": CURRENCY_USD,
                "promo_code": None,
                "card": request.data.get("card"),
                "number_members": number_members,
                "enterprise_id": enterprise.enterprise_id,
                "billing_cycle_anchor": int(primary_admin_plan.end_period),
                "billing_cycle_anchor_action": "set"
            }
            PaymentMethodFactory.get_method(
                user_plan=primary_admin_plan, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
            ).upgrade_recurring_subscription(
                amount=0, plan_type=PLAN_TYPE_PM_ENTERPRISE, coupon=None, duration=primary_admin_plan.duration,
                **metadata
            )

        stripe_default_payment_method = stripe_subscription.default_payment_method if stripe_subscription else None
        return Response(
            status=status.HTTP_200_OK,
            data={
                "primary_admin": primary_admin.user_id,
                "stripe_default_payment_method": stripe_default_payment_method
            }
        )

    @action(methods=["put"], detail=False)
    def card_set_default(self, request, *args, **kwargs):
        card_id = kwargs.get("card_id")
        enterprise = self.get_enterprise()
        primary_admin = self.enterprise_service.get_primary_member(
            enterprise_id=enterprise.enterprise_id
        ).user
        primary_admin_plan = self.user_service.get_current_plan(user=primary_admin)
        stripe_subscription = primary_admin_plan.get_stripe_subscription()
        if not stripe_subscription:
            return Response(status=status.HTTP_200_OK, data={"stripe_payment_method": None})
        payment = PaymentMethodFactory.get_method(
            user_plan=primary_admin_plan, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
        )
        new_source = payment.update_default_payment(new_source=card_id)
        return Response(status=status, data={"stripe_payment_method": new_source})

    @action(methods=["post"], detail=False)
    def calc(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        promo_code = validated_data.get("promo_code")
        duration = validated_data.get("duration", DURATION_MONTHLY)
        currency = validated_data.get("currency", CURRENCY_USD)
        # Calc payment
        result = self._calc_payment(
            enterprise=enterprise, duration=duration, currency=currency, promo_code=promo_code
        )
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["post"], detail=False)
    def calc_public(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        promo_code = validated_data.get("promo_code")
        duration = validated_data.get("duration", DURATION_MONTHLY)
        currency = validated_data.get("currency", CURRENCY_USD)
        quantity = validated_data.get("quantity", 1)
        result = self._calc_payment_public(
            quantity=quantity, duration=duration, currency=currency, promo_code=promo_code
        )
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["post"], detail=False)
    def upgrade_plan_public(self, request, *args, **kwargs):
        user = self.request.user
        user_memberships = self.enterprise_member_service.list_enterprise_members(**{
            "user_id": user.user_id,
            "roles": [E_MEMBER_ROLE_MEMBER, E_MEMBER_ROLE_ADMIN]
        })
        if user_memberships:
            raise ValidationError({"non_field_errors": [gen_error("7015")]})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = request.data.get("card")
        if not card:
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        if not card.get("id_card"):
            raise ValidationError({"non_field_errors": [gen_error("7007")]})

        validated_data = serializer.validated_data
        promo_code_obj = validated_data.get("promo_code_obj", None)
        duration = validated_data.get("duration", DURATION_MONTHLY)
        currency = validated_data.get("currency")
        quantity = validated_data.get("quantity")
        organization = validated_data.get("organization")
        enterprise = self.user_service.get_default_enterprise(
            user=user, enterprise_name=organization, create_if_not_exist=True
        )
        # Update billing infor
        try:
            updated_enterprise = self.enterprise_service.update_enterprise(
                enterprise_id=enterprise.enterprise_id,
                enterprise_update_data={
                    "enterprise_address1": validated_data.get("enterprise_address1"),
                    "enterprise_address2": validated_data.get("enterprise_address2"),
                    "enterprise_phone": validated_data.get("enterprise_phone"),
                    "enterprise_country": validated_data.get("enterprise_country"),
                    "enterprise_postal_code": validated_data.get("enterprise_postal_code"),
                }
            )
        except CountryDoesNotExistException:
            raise ValidationError(detail={"enterprise_country": ["The country does not exist"]})
        update_result = self._upgrade_plan(
            user=user, enterprise=updated_enterprise, card=card, promo_code_obj=promo_code_obj,
            duration=duration, number_members=quantity, currency=currency
        )
        # Saving the init seats of the enterprise
        stripe_subscription_id = update_result.get("stripe_subscription_id")
        if quantity > 1 and update_result.get("success") is True and stripe_subscription_id:
            try:
                stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                if stripe_subscription.status in ["trialing", "active"]:
                    self.enterprise_service.update_enterprise(
                        enterprise_id=updated_enterprise.enterprise_id,
                        enterprise_update_data={
                            "init_seats": quantity,
                            "init_seats_expired_time": stripe_subscription.current_period_end,

                        }
                    )
                    # Then, set the quantity to 1
                    items = stripe_subscription.get("items").get("data")
                    if items:
                        si = items[0].get("id")
                        plans = [{"id": si, "quantity": 1}]
                        stripe.Subscription.modify(stripe_subscription.id, items=plans, proration_behavior='none')
            except stripe.error.StripeError:
                tb = traceback.format_exc()
                CyLog.error(**{"message": f"Set init seat error: {user} {stripe_subscription_id}: \n{tb}"})

        return Response(status=200, data={"success": True})

    def _upgrade_plan(self, user, enterprise, card, promo_code_obj=None,
                      duration=DURATION_MONTHLY, number_members=None, currency=CURRENCY_USD):
        if not card:
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        if not card.get("id_card"):
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        metadata = {
            "currency": currency,
            "promo_code": promo_code_obj,
            "card": card,
            "number_members": number_members,
            "enterprise_id": enterprise.enterprise_id,
        }
        # Calc payment price of new plan
        promo_code_value = promo_code_obj.code if promo_code_obj else None
        calc_payment = self._calc_payment(
            enterprise=enterprise, duration=duration, currency=currency, promo_code=promo_code_value
        )
        immediate_payment = calc_payment.get("immediate_payment")
        current_plan = self.user_service.get_current_plan(user=user)
        payment = PaymentMethodFactory.get_method(
            user_plan=current_plan, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
        )
        payment_result = payment.upgrade_recurring_subscription(
            amount=immediate_payment, plan_type=PLAN_TYPE_PM_ENTERPRISE, coupon=promo_code_obj, duration=duration,
            **metadata
        )
        update_result = payment_result.get("success")
        if update_result is False:
            if payment_result.get("stripe_error"):
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        "code": "7009",
                        "message": "Your card was declined (insufficient funds, etc...)",
                        "details": payment_result.get("error_details")
                    }
                )
            raise ValidationError({"non_field_errors": [gen_error("7009")]})

        self.user_service.update_user_plan_by_id(
            user_plan_id=current_plan.pm_user_plan_id,
            user_plan_update_data={
                "default_payment_method": PAYMENT_METHOD_CARD
            }
        )
        return payment_result

    @action(methods=["post"], detail=False)
    def upgrade_plan(self, request, *args, **kwargs):
        user = self.request.user
        enterprise = self.get_enterprise()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = request.data.get("card")
        if not card:
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        if not card.get("id_card"):
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        validated_data = serializer.validated_data
        plan = self.payment_service.get_pm_plan_by_alias(PLAN_TYPE_PM_ENTERPRISE)
        promo_code = validated_data.get("promo_code")
        promo_code_obj = None
        if promo_code:
            promo_code_obj = self.payment_service.check_valid_promo_code(
                promo_code=promo_code,
                current_user=request.user
            )
            if not promo_code_obj:
                raise ValidationError(detail={"promo_code": ["This coupon is expired or invalid"]})
        duration = validated_data.get("duration", DURATION_MONTHLY)
        number_members = self.enterprise_member_service.count_enterprise_members(**{
            "status": E_MEMBER_STATUS_CONFIRMED,
            "is_activated": True,
            "enterprise_id": enterprise.enterprise_id
        })
        currency = validated_data.get("currency")
        self._upgrade_plan(
            user=user, enterprise=enterprise, card=card, promo_code_obj=promo_code_obj,
            duration=duration, number_members=number_members, currency=currency
        )
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["get", "put"], detail=False)
    def billing_address(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        if request.method == "GET":
            return Response(status=status.HTTP_200_OK, data=self.get_serializer(enterprise).data)

        elif request.method == "PUT":
            serializer = self.get_serializer(enterprise, data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            try:
                self.enterprise_service.update_enterprise(
                    enterprise_id=enterprise.enterprise_id,
                    enterprise_update_data=validated_data
                )
            except CountryDoesNotExistException:
                raise ValidationError(detail={"enterprise_country": ["The country does not exist"]})
            return Response(status=status.HTTP_200_OK, data=serializer.data)

    def _calc_payment(self, enterprise: Enterprise, duration=DURATION_MONTHLY, currency=CURRENCY_USD, promo_code=None):
        number_members = self.enterprise_member_service.count_enterprise_members(**{
            "enterprise_id": enterprise.enterprise_id,
            "status": E_MEMBER_STATUS_CONFIRMED,
            "is_activated": True
        })
        try:
            result = self.payment_service.calc_payment(
                user_id=self.request.user.user_id,
                plan_alias=PLAN_TYPE_PM_ENTERPRISE,
                currency=currency,
                duration=duration,
                number_members=number_members,
                promo_code=promo_code

            )
            result["quantity"] = number_members
        except PlanDoesNotExistException:
            raise ValidationError(detail={"plan_alias": ["This plan alias does not exist"]})
        return result

    def _calc_payment_public(self, quantity: int, duration=DURATION_MONTHLY, currency=CURRENCY_USD, promo_code=None):
        try:
            result = self.payment_service.calc_payment_public(
                plan_alias=PLAN_TYPE_PM_ENTERPRISE,
                quantity=quantity,
                duration=duration,
                currency=currency,
                promo_code=promo_code,
            )
        except PlanDoesNotExistException:
            raise ValidationError(detail={"plan_alias": ["This plan alias does not exist"]})
        return result
