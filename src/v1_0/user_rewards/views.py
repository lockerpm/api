import stripe
import stripe.error

from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.decorators import action

from cystack_models.models import UserRewardMission, Mission, PromoCode
from shared.constants.missions import *
from shared.constants.transactions import PROMO_PERCENTAGE
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.user_reward_mission_pwd_permission import UserRewardMissionPwdPermission
from shared.utils.app import now, random_n_digit
from shared.utils.factory import factory
from v1_0.user_rewards.serializers import UserRewardMissionSerializer, UserRewardCheckCompletedSerializer
from v1_0.general_view import PasswordManagerViewSet


class UserRewardMissionPwdViewSet(PasswordManagerViewSet):
    permission_classes = (UserRewardMissionPwdPermission,)
    http_method_names = ["head", "options", "get", "post"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = UserRewardMissionSerializer
        elif self.action == "completed":
            self.serializer_class = UserRewardCheckCompletedSerializer
        return super().get_serializer_class()

    def get_object(self):
        user = self.request.user
        try:
            user_reward_mission = UserRewardMission.objects.get(
                user_id=user.user_id, mission_id=self.kwargs.get("pk"), mission__available=True
            )
            self.check_object_permissions(obj=user_reward_mission, request=self.request)
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
        paging_param = self.request.query_params.get("paging", "1")
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
        if user_reward_mission.status not in [USER_MISSION_STATUS_NOT_STARTED]:
            raise NotFound

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        user_identifier = validated_data.get("user_identifier")

        mission_type = user_reward_mission.mission.mission_type
        extra_requirements = user_reward_mission.mission.get_extra_requirements()
        module_name = f'src.cystack_models.factory.user_reward_mission.{user_reward_mission.mission_id}_mission'
        mission_factory = factory(module_name, mission_type, extra_requirements)
        if not mission_factory:
            return Response(status=200, data={"claim": False})
        input_data = {"user": user, "user_identifier": user_identifier}
        mission_check = mission_factory.check_mission_completion(input_data)
        if not mission_check:
            return Response(status=200, data={"claim": False})
        user_reward_mission.status = USER_MISSION_STATUS_COMPLETED
        user_reward_mission.save()

        return Response(status=200, data={"claim": True})

    @action(methods=["get"], detail=False)
    def claim(self, request, *args, **kwargs):
        user_reward_missions = self.get_queryset()
        promo_code_reward_missions = user_reward_missions.filter(mission__reward_type=REWARD_TYPE_PROMO_CODE)
        result = {
            "total_promo_code": promo_code_reward_missions.count(),
            "claimed_promo_code": promo_code_reward_missions.filter(status=USER_MISSION_STATUS_REWARD_SENT).count(),
            "available_promo_code": promo_code_reward_missions.filter(status=USER_MISSION_STATUS_COMPLETED).count(),
            "available_promo_code_value": promo_code_reward_missions.filter(
                status=USER_MISSION_STATUS_COMPLETED,
            ).aggregate(Sum('mission__reward_value'))['mission__reward_value__sum']
        }
        return Response(status=200, data=result)

    @action(methods=["post"], detail=False)
    def claim_promo_code(self, request, *args, **kwargs):
        user_reward_missions = self.get_queryset()
        available_promo_code_value = user_reward_missions.filter(
            mission__reward_type=REWARD_TYPE_PROMO_CODE,
            status=USER_MISSION_STATUS_COMPLETED,
        ).aggregate(Sum('mission__reward_value'))['mission__reward_value__sum']
        if available_promo_code_value <= 0:
            raise ValidationError(detail={"promo_code": ["The available promo code value is not valid"]})
        code = f"LKMR-{random_n_digit(n=8)}".upper()
        promo_code_data = {
            "promo_type": PROMO_PERCENTAGE,
            "expired_time": now() + 365 * 86400,    # 1 year
            "code": code,
            "value": available_promo_code_value,
            "duration": 1,
            "number_code": 1,
            "description_en": "Locker PromoCode Reward",
            "description_vi": "Locker PromoCode Reward",
        }
        promo_code_obj = PromoCode.create(**promo_code_data)
        # Create on Stripe
        try:
            stripe.Coupon.create(
                duration='repeating',
                duration_in_months=12,
                id="{}_yearly".format(promo_code_obj.id),
                percent_off=available_promo_code_value,
                name=code
            )
        except stripe.error.StripeError:
            promo_code_obj.delete()
            raise ValidationError({"non_field_errors": [gen_error("0008")]})
        # Change the reward status
        user_reward_missions.filter(
            mission__reward_type=REWARD_TYPE_PROMO_CODE,
            status=USER_MISSION_STATUS_COMPLETED,
        ).update(status=USER_MISSION_STATUS_REWARD_SENT)

        return Response(status=200, data={
            "id": promo_code_obj.id,
            "code": promo_code_obj.code
        })
