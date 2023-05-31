import json
import os
import stripe
import stripe.error
from django.conf import settings

from django.db.models import Sum, Q, F
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.decorators import action

from cystack_models.models import UserRewardMission, Mission, PromoCode
from shared.constants.missions import *
from shared.constants.transactions import PROMO_PERCENTAGE, MISSION_REWARD_PROMO_PREFIX, DURATION_YEARLY, \
    PLAN_TYPE_PM_PREMIUM, PLAN_TYPE_PM_FREE
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.user_reward_mission_pwd_permission import UserRewardMissionPwdPermission
from shared.utils.app import now, random_n_digit
from shared.utils.factory import factory
from v1_0.user_rewards.serializers import UserRewardMissionSerializer, UserRewardCheckCompletedSerializer, \
    ListRewardPromoCodeSerializer, UserExtensionInstallCheckCompletedSerializer
from v1_0.general_view import PasswordManagerViewSet


class UserRewardMissionPwdViewSet(PasswordManagerViewSet):
    permission_classes = (UserRewardMissionPwdPermission,)
    http_method_names = ["head", "options", "get", "post"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = UserRewardMissionSerializer
        elif self.action == "completed":
            if self.kwargs.get("pk") == "extension_installation_and_review":
                self.serializer_class = UserExtensionInstallCheckCompletedSerializer
            else:
                self.serializer_class = UserRewardCheckCompletedSerializer
        elif self.action == "list_promo_codes":
            self.serializer_class = ListRewardPromoCodeSerializer
        return super().get_serializer_class()

    def get_object(self):
        user = self.request.user
        try:
            user_reward_mission = UserRewardMission.objects.get(
                user_id=user.user_id, mission_id=self.kwargs.get("pk"), mission__available=True
            )
            # self.check_object_permissions(obj=user_reward_mission, request=self.request)
            return user_reward_mission
        except UserRewardMission.DoesNotExist:
            raise NotFound

    def get_queryset(self):
        user = self.request.user
        self.gen_default_missions()
        user_reward_missions = user.user_reward_missions.filter(
            mission__available=True
        ).select_related('mission').order_by('mission__order_index')

        return user_reward_missions

    def gen_default_missions(self):
        user = self.request.user
        mission_ids = list(Mission.objects.filter(available=True).order_by('order_index').values_list('id', flat=True))
        user.user_reward_missions.model.create_multiple_user_reward_missions(user, mission_ids)

    def list(self, request, *args, **kwargs):
        # self.check_pwd_session_auth(request)
        paging_param = self.request.query_params.get("paging", "0")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 50))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 50
        return super().list(request, *args, **kwargs)

    @action(methods=["post"], detail=True)
    def completed(self, request, *args, **kwargs):
        user = self.request.user
        user_reward_mission = self.get_object()
        if user_reward_mission.status not in [USER_MISSION_STATUS_NOT_STARTED, USER_MISSION_STATUS_UNDER_VERIFICATION]:
            raise NotFound

        if kwargs.get("pk") == "extension_installation_and_review":
            extension_user_identifier = []
            for d in request.data:
                serializer = self.get_serializer(data=d)
                serializer.is_valid(raise_exception=True)
                extension_user_identifier.append(serializer.validated_data)
            user_identifier = extension_user_identifier
            answer = user_identifier
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            user_identifier = validated_data.get("user_identifier")
            answer = validated_data

        mission_type = user_reward_mission.mission.mission_type
        extra_requirements = user_reward_mission.mission.get_extra_requirements()
        module_name = f'cystack_models.factory.user_reward_mission.missions.{user_reward_mission.mission_id}_mission'
        mission_factory = factory(module_name, mission_type, extra_requirements)
        if not mission_factory:
            return Response(status=200, data={"claim": False})
        input_data = {"user": user, "user_identifier": user_identifier}
        mission_check = mission_factory.check_mission_completion(input_data)
        user_reward_mission.answer = json.dumps(answer)
        if not mission_check:
            user_reward_mission.status = USER_MISSION_STATUS_UNDER_VERIFICATION
            user_reward_mission.save()
            return Response(status=200, data={"claim": False})
        user_reward_mission.status = USER_MISSION_STATUS_REWARD_SENT
        user_reward_mission.save()

        # If the reward is premium time, upgrade the user plan immediately
        if user_reward_mission.mission.reward_type == REWARD_TYPE_PREMIUM:
            user_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
            # Upgrade plan of the referred user if the plan is Free
            if user_plan.get_plan_type_alias() == PLAN_TYPE_PM_FREE:
                self.user_repository.update_plan(user=user_plan, plan_type_alias=PLAN_TYPE_PM_PREMIUM, **{
                    "start_period": now(),
                    "end_period": now() + user_reward_mission.mission.reward_value,
                })
            # Else, update extra time
            else:
                user_plan.extra_time = F('extra_time') + user_reward_mission.mission.reward_value
                if not user_plan.extra_plan:
                    user_plan.extra_plan = user_plan.get_plan_type_alias()
                user_plan.save()

        return Response(status=200, data={"claim": True})

    @action(methods=["get"], detail=False)
    def claim(self, request, *args, **kwargs):
        user = self.request.user
        user_reward_missions = self.get_queryset()
        promo_code_reward_missions = user_reward_missions.filter(mission__reward_type=REWARD_TYPE_PROMO_CODE)
        total_promo_code_value = promo_code_reward_missions.aggregate(
            Sum('mission__reward_value')
        ).get("mission__reward_value__sum") or 0

        max_available_promo_code_value = promo_code_reward_missions.filter(
            status=USER_MISSION_STATUS_REWARD_SENT,
        ).aggregate(Sum('mission__reward_value')).get("mission__reward_value__sum") or 0
        # The used promo codes are expire codes or zero-remaining times
        used_promo_code_value = user.only_promo_codes.filter(code__startswith=MISSION_REWARD_PROMO_PREFIX).filter(
            Q(expired_time__isnull=True) | Q(expired_time__lt=now()) | Q(remaining_times=0)
        ).aggregate(Sum('value')).get("value__sum") or 0

        available_promo_code_value = max(max_available_promo_code_value - used_promo_code_value, 0)

        generated_promo_codes = user.only_promo_codes.filter(code__startswith=MISSION_REWARD_PROMO_PREFIX).filter(
            valid=True, remaining_times__gt=0
        ).filter(
            Q(expired_time__isnull=True) | Q(expired_time__gt=now())
        ).order_by('-created_time')
        generated_promo_codes_srl = ListRewardPromoCodeSerializer(generated_promo_codes, many=True)

        result = {
            "total_promo_code": promo_code_reward_missions.count(),
            "completed_promo_code_missions": promo_code_reward_missions.filter(
                status=USER_MISSION_STATUS_REWARD_SENT
            ).count(),
            "total_promo_code_value": total_promo_code_value,
            "max_available_promo_code_value": max_available_promo_code_value,
            "used_promo_code_value": used_promo_code_value,
            "available_promo_code_value": available_promo_code_value,
            "generated_available_promo_codes": generated_promo_codes_srl.data

            # "claimed_promo_code": promo_code_reward_missions.filter(status=USER_MISSION_STATUS_REWARD_SENT).count(),
            # "available_promo_code": promo_code_reward_missions.filter(status=USER_MISSION_STATUS_REWARD_SENT).count(),
            # "available_promo_code_value": promo_code_reward_missions.filter(
            #     status=USER_MISSION_STATUS_REWARD_SENT,
            # ).aggregate(Sum('mission__reward_value'))['mission__reward_value__sum']
        }
        return Response(status=200, data=result)

    @action(methods=["get"], detail=False)
    def list_promo_codes(self, request, *args, **kwargs):
        user = self.request.user
        promo_codes = user.only_promo_codes.filter(valid=True, remaining_times__gt=0).filter(
            Q(expired_time__isnull=True) | Q(expired_time__gt=now())
        ).order_by('-created_time')
        serializer = self.get_serializer(promo_codes, many=True)
        return Response(status=200, data=serializer.data)

    @action(methods=["post"], detail=False)
    def claim_promo_code(self, request, *args, **kwargs):
        user = self.request.user
        user_reward_missions = self.get_queryset()
        max_available_promo_code_value = user_reward_missions.filter(
            mission__reward_type=REWARD_TYPE_PROMO_CODE,
            status=USER_MISSION_STATUS_REWARD_SENT,
        ).aggregate(Sum('mission__reward_value')).get("mission__reward_value__sum") or 0

        used_promo_code_value = user.only_promo_codes.filter(code__startswith=MISSION_REWARD_PROMO_PREFIX).filter(
            Q(expired_time__isnull=True) | Q(expired_time__lt=now()) | Q(remaining_times=0)
        ).aggregate(Sum('value')).get("value__sum") or 0

        available_promo_code_value = max(max_available_promo_code_value - used_promo_code_value, 0)
        if available_promo_code_value <= 0:
            raise ValidationError(detail={"promo_code": ["The available promo code value is not valid"]})
        code = f"{MISSION_REWARD_PROMO_PREFIX}{random_n_digit(n=8)}".upper()
        # This code is expired in a week
        expired_time = int(now() + 7 * 86400)
        promo_code_data = {
            "type": PROMO_PERCENTAGE,
            "expired_time": expired_time,
            "code": code,
            "value": available_promo_code_value,
            "duration": 1,
            "number_code": 1,
            "description_en": "Locker PromoCode Reward",
            "description_vi": "Locker PromoCode Reward",
            "only_user_id": user.user_id
        }
        promo_code_obj = PromoCode.create(**promo_code_data)

        # Create on Stripe
        if os.getenv("PROD_ENV") in ["prod", "staging"]:
            try:
                stripe.Coupon.create(
                    duration='once',
                    id="{}_yearly".format(promo_code_obj.id),
                    percent_off=available_promo_code_value,
                    name=code,
                    redeem_by=expired_time
                )
                stripe.Coupon.create(
                    duration='once',
                    id="{}_monthly".format(promo_code_obj.id),
                    percent_off=available_promo_code_value,
                    name=code,
                    redeem_by=expired_time
                )
            except stripe.error.StripeError:
                promo_code_obj.delete()
                raise ValidationError({"non_field_errors": [gen_error("0008")]})

        # Delete all old promo codes - Delete all valid tokens
        user.only_promo_codes.filter(code__startswith=MISSION_REWARD_PROMO_PREFIX).filter(
            expired_time__gt=now(), remaining_times__gt=0
        ).exclude(id=promo_code_obj.id).delete()

        # user.only_promo_codes.filter(code__startswith=MISSION_REWARD_PROMO_PREFIX).filter(
        #     Q(expired_time__gt=now()) | Q(remaining_times__gt=0)
        # ).exclude(id=promo_code_obj.id).delete()

        return Response(status=200, data={
            "id": promo_code_obj.id,
            "code": promo_code_obj.code
        })
