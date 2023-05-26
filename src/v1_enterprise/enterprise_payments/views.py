import traceback

import stripe
import stripe.error

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory
from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.payments.payments import Payment
from cystack_models.models.payments.promo_codes import PromoCode
from cystack_models.models.user_plans.pm_plans import PMPlan
from shared.constants.enterprise_members import *
from shared.constants.transactions import *
from shared.error_responses.error import gen_error
from shared.log.cylog import CyLog
from shared.permissions.locker_permissions.enterprise.payment_permission import PaymentPwdPermission
from shared.utils.app import now
from v1_0.resources.serializers import PMPlanSerializer
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import InvoiceSerializer, CalcSerializer, UpgradePlanSerializer, BillingAddressSerializer, \
    DetailInvoiceSerializer, CalcPublicSerializer, UpgradePlanPublicSerializer


class PaymentPwdViewSet(EnterpriseViewSet):
    permission_classes = (PaymentPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = InvoiceSerializer
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
        return super(PaymentPwdViewSet, self).get_serializer_class()

    def get_enterprise(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=enterprise)
            return enterprise
        except Enterprise.DoesNotExist:
            raise NotFound

    def get_queryset(self):
        enterprise = self.get_enterprise()
        invoices = Payment.objects.filter(enterprise_id=enterprise.id).order_by('-created_time')
        status_param = self.request.query_params.get("status")
        payment_method_param = self.request.query_params.get("payment_method")
        from_param = self.check_int_param(self.request.query_params.get("from"))
        to_param = self.check_int_param(self.request.query_params.get("to"))
        if to_param:
            invoices = invoices.filter(created_time__gt=to_param)
        if from_param:
            invoices = invoices.filter(created_time__lte=from_param)
        if status_param:
            invoices = invoices.filter(status=status_param)
        if payment_method_param:
            invoices = invoices.filter(payment_method=payment_method_param)
        return invoices

    def get_object(self):
        enterprise = self.get_enterprise()
        try:
            invoice = Payment.objects.get(enterprise_id=enterprise.id, payment_id=self.kwargs.get("payment_id"))
            return invoice
        except Payment.DoesNotExist:
            raise NotFound

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10
        return super(PaymentPwdViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super(PaymentPwdViewSet, self).retrieve(request, *args, **kwargs)

    @action(methods=["get"], detail=False)
    def current_plan(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        enterprise_plan = PMPlan.objects.get(alias=PLAN_TYPE_PM_ENTERPRISE)
        current_plan = self.user_repository.get_current_plan(user=primary_admin)
        result = PMPlanSerializer(enterprise_plan, many=False).data
        result.update({
            "start_period": current_plan.start_period,
            "next_billing_time": current_plan.get_next_billing_time(),
            "duration": current_plan.duration,
            "is_trailing": current_plan.is_trailing(),
            "cancel_at_period_end": current_plan.is_cancel_at_period_end(),
            "payment_method": current_plan.get_default_payment_method(),
            "enterprise": {
                "current_members": enterprise.get_activated_members_count()
            },
            "stripe_subscription": current_plan.pm_stripe_subscription,
            "primary_admin": primary_admin.user_id,
        })
        return Response(status=200, data=result)

    @action(methods=["get"], detail=False)
    def next_attempt(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        current_plan = self.user_repository.get_current_plan(user=primary_admin)
        return Response(status=200, data={
            "next_payment_attempt": current_plan.get_next_retry_payment_date(),
        })

    @action(methods=["get", "post"], detail=False)
    def cards(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        primary_admin_plan = self.user_repository.get_current_plan(user=primary_admin, scope=settings.SCOPE_PWD_MANAGER)
        stripe_subscription = primary_admin_plan.get_stripe_subscription()
        stripe_default_payment_method = stripe_subscription.default_payment_method if stripe_subscription else None
        return Response(status=200, data={
            "primary_admin": primary_admin.user_id,
            "stripe_default_payment_method": stripe_default_payment_method
        })

    @action(methods=["get"], detail=False)
    def add_card_subscription(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        primary_admin = enterprise.get_primary_admin_user()
        primary_admin_plan = self.user_repository.get_current_plan(user=primary_admin, scope=settings.SCOPE_PWD_MANAGER)
        stripe_subscription = primary_admin_plan.get_stripe_subscription()
        # If the Enterprise plan doesn't have Stripe Subscription => Subscribe with stripe
        if primary_admin_plan.get_plan_obj().is_team_plan and stripe_subscription is None and \
                primary_admin_plan.end_period and primary_admin_plan.end_period > now():
            number_members = enterprise.get_activated_members_count()
            metadata = {
                "currency": CURRENCY_USD,
                "promo_code": None,
                "card": request.data.get("card"),
                "number_members": number_members,
                "enterprise_id": enterprise.id,
                "billing_cycle_anchor": int(primary_admin_plan.end_period),
                "billing_cycle_anchor_action": "set"
            }
            PaymentMethodFactory.get_method(
                user=primary_admin, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
            ).upgrade_recurring_subscription(
                amount=0, plan_type=PLAN_TYPE_PM_ENTERPRISE, coupon=None, duration=primary_admin_plan.duration,
                **metadata
            )

        stripe_default_payment_method = stripe_subscription.default_payment_method if stripe_subscription else None
        return Response(status=200, data={
            "primary_admin": primary_admin.user_id,
            "stripe_default_payment_method": stripe_default_payment_method
        })

    @action(methods=["put"], detail=False)
    def card_set_default(self, request, *args, **kwargs):
        card_id = kwargs.get("card_id")
        enterprise = self.get_enterprise()
        primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        primary_admin_plan = self.user_repository.get_current_plan(user=primary_admin, scope=settings.SCOPE_PWD_MANAGER)
        stripe_subscription = primary_admin_plan.get_stripe_subscription()
        if not stripe_subscription:
            return Response(status=200, data={"stripe_payment_method": None})
        payment = PaymentMethodFactory.get_method(
            user=primary_admin, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
        )
        new_source = payment.update_default_payment(new_source=card_id)
        return Response(status=200, data={"stripe_payment_method": new_source})

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
        return Response(status=200, data=result)

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
        return Response(status=200, data=result)

    @action(methods=["post"], detail=False)
    def upgrade_plan_public(self, request, *args, **kwargs):
        user = self.request.user
        if user.enterprise_members.filter(role_id__in=[E_MEMBER_ROLE_MEMBER, E_MEMBER_ROLE_ADMIN]).exists():
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
        card = request.data.get("card")
        enterprise = self.user_repository.get_default_enterprise(
            user=user, enterprise_name=organization, create_if_not_exist=True
        )
        # Update billing infor
        enterprise.enterprise_address1 = validated_data.get("enterprise_address1", enterprise.enterprise_address1)
        enterprise.enterprise_address2 = validated_data.get("enterprise_address2", enterprise.enterprise_address2)
        enterprise.enterprise_phone = validated_data.get("enterprise_phone", enterprise.enterprise_phone)
        enterprise.enterprise_country = validated_data.get("enterprise_country", enterprise.enterprise_country)
        enterprise.enterprise_postal_code = validated_data.get(
            "enterprise_postal_code", enterprise.enterprise_postal_code
        )
        enterprise.revision_date = now()
        enterprise.save()

        # Upgrade to Enterprise Plan
        update_result = self._upgrade_plan(
            user=user, enterprise=enterprise, card=card, promo_code_obj=promo_code_obj,
            duration=duration, number_members=quantity, currency=currency
        )
        # Saving the init seats of the enterprise
        stripe_subscription_id = update_result.get("stripe_subscription_id")
        if quantity > 1 and update_result.get("success") is True and stripe_subscription_id:
            try:
                stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                if stripe_subscription.status in ["trialing", "active"]:
                    enterprise.init_seats = quantity
                    enterprise.init_seats_expired_time = stripe_subscription.current_period_end
                    enterprise.save()
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
            "enterprise_id": enterprise.id,
        }
        # current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        # if current_plan.get_plan_obj().is_team_plan is False:
        #     raise ValidationError(detail={"non_field_errors": [gen_error("7014")]})
        # Calc payment price of new plan
        promo_code_value = promo_code_obj.code if promo_code_obj else None
        calc_payment = self._calc_payment(
            enterprise=enterprise, duration=duration, currency=currency, promo_code=promo_code_value
        )
        immediate_payment = calc_payment.get("immediate_payment")

        payment = PaymentMethodFactory.get_method(
            user=user, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
        )
        payment_result = payment.upgrade_recurring_subscription(
            amount=immediate_payment, plan_type=PLAN_TYPE_PM_ENTERPRISE, coupon=promo_code_obj, duration=duration,
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
        promo_code_obj = validated_data.get("promo_code_obj", None)
        duration = validated_data.get("duration", DURATION_MONTHLY)
        number_members = enterprise.get_activated_members_count()
        currency = validated_data.get("currency")
        self._upgrade_plan(user=user, enterprise=enterprise, card=card, promo_code_obj=promo_code_obj,
                           duration=duration, number_members=number_members, currency=currency)

        # metadata = {
        #     "currency": currency,
        #     "promo_code": promo_code_obj,
        #     "card": card,
        #     "number_members": number_members,
        #     "enterprise_id": enterprise.id,
        # }
        # current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        # if current_plan.get_plan_obj().is_team_plan is False:
        #     raise ValidationError(detail={"non_field_errors": [gen_error("7014")]})
        # # if current_plan.end_period and current_plan.end_period > now():
        # #     metadata.update({
        # #         "trial_end": int(current_plan.end_period)
        # #     })
        # # Calc payment price of new plan
        # promo_code_value = promo_code_obj.code if promo_code_obj else None
        # calc_payment = self._calc_payment(
        #     enterprise=enterprise, duration=duration, currency=currency, promo_code=promo_code_value
        # )
        # immediate_payment = calc_payment.get("immediate_payment")
        #
        # payment = PaymentMethodFactory.get_method(
        #     user=user, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
        # )
        # payment_result = payment.upgrade_recurring_subscription(
        #     amount=immediate_payment, plan_type=PLAN_TYPE_PM_ENTERPRISE, coupon=promo_code_obj, duration=duration,
        #     **metadata
        # )
        # update_result = payment_result.get("success")
        # if update_result is False:
        #     if payment_result.get("stripe_error"):
        #         return Response(status=400, data={
        #             "code": "7009",
        #             "message": "Your card was declined (insufficient funds, etc...)",
        #             "details": payment_result.get("error_details")
        #         })
        #     raise ValidationError({"non_field_errors": [gen_error("7009")]})
        #
        # # Set default payment method
        # try:
        #     current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        #     current_plan.set_default_payment_method(PAYMENT_METHOD_CARD)
        # except ObjectDoesNotExist:
        #     pass
        return Response(status=200, data={"success": True})

    @action(methods=["get", "put"], detail=False)
    def billing_address(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        if request.method == "GET":
            return Response(status=200, data=self.get_serializer(enterprise).data)

        elif request.method == "PUT":
            partial = kwargs.pop('partial', False)
            serializer = self.get_serializer(enterprise, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if getattr(enterprise, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                enterprise._prefetched_objects_cache = {}
            return Response(status=200, data=serializer.data)

    def _calc_payment(self, enterprise: Enterprise, duration=DURATION_MONTHLY, currency=CURRENCY_USD, promo_code=None):
        current_plan = self.user_repository.get_current_plan(user=self.request.user, scope=settings.SCOPE_PWD_MANAGER)
        plan = PMPlan.objects.get(alias=PLAN_TYPE_PM_ENTERPRISE)
        quantity = enterprise.get_activated_members_count()
        result = current_plan.calc_update_price(
            new_plan=plan, new_duration=duration,
            new_quantity=quantity,
            currency=currency, promo_code=promo_code
        )
        result["quantity"] = quantity
        result["plan"] = PMPlanSerializer(plan, many=False).data
        return result

    @staticmethod
    def _calc_payment_public(quantity: int, duration=DURATION_MONTHLY, currency=CURRENCY_USD, promo_code=None):
        plan = PMPlan.objects.get(alias=PLAN_TYPE_PM_ENTERPRISE)
        current_time = now()
        # Get new plan price
        new_plan_price = plan.get_price(duration=duration, currency=currency)
        # Number of month duration billing by new duration
        duration_next_billing_month = Payment.get_duration_month_number(duration)
        # Calc discount
        error_promo = None
        promo_code_obj = None
        promo_description_en = None
        promo_description_vi = None
        if promo_code is not None and promo_code != "":
            promo_code_obj = PromoCode.check_valid(value=promo_code, current_user=None, new_duration=duration)
            if not promo_code_obj:
                error_promo = {"promo_code": ["This coupon is expired or incorrect"]}
            else:
                # if not (new_duration == DURATION_YEARLY and promo_code_obj.duration < 12):
                #     duration_next_billing_month = promo_code_obj.duration
                promo_description_en = promo_code_obj.description_en
                promo_description_vi = promo_code_obj.description_vi

        total_amount = new_plan_price * quantity
        next_billing_time = current_time + duration_next_billing_month * 30 * 86400

        # Discount and immediate payment
        total_amount = max(total_amount, 0)
        discount = promo_code_obj.get_discount(total_amount, duration=duration) if promo_code_obj else 0.0
        immediate_amount = max(round(total_amount - discount, 2), 0)

        result = {
            "alias": plan.get_alias(),
            "price": round(new_plan_price, 2),
            "total_price": total_amount,
            "discount": discount,
            "duration": duration,
            "currency": currency,
            "immediate_payment": immediate_amount,
            "next_billing_time": next_billing_time,
            "promo_description": {
                "en": promo_description_en,
                "vi": promo_description_vi
            },
            "error_promo": error_promo,
            "quantity": quantity,
            "plan": PMPlanSerializer(plan, many=False).data
        }
        return result
