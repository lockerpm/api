import os
import stripe
import stripe.error
from rest_framework import status

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.decorators import action

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.user_reward_mission_pwd_permission import \
    UserRewardMissionPwdPermission
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.exceptions.user_reward_mission_exception import UserRewardMissionDoesNotExistException, \
    UserRewardPromoCodeInvalidException
from locker_server.shared.constants.missions import USER_MISSION_STATUS_NOT_STARTED, \
    USER_MISSION_STATUS_UNDER_VERIFICATION, USER_MISSION_STATUS_REWARD_SENT, REWARD_TYPE_PREMIUM
from locker_server.shared.constants.transactions import PLAN_TYPE_PM_FREE, PLAN_TYPE_PM_PREMIUM
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.utils.app import now
from locker_server.shared.utils.factory import factory

from .serializers import *


class UserRewardMissionPwdViewSet(APIBaseViewSet):
    permission_classes = (UserRewardMissionPwdPermission,)
    http_method_names = ["head", "options", "get", "post"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListUserRewardMissionSerializer
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
            user_reward_mission = self.user_reward_mission_service.get_user_reward_by_mission_id(
                user_id=user.user_id,
                mission_id=self.kwargs.get("pk"),
                available=True
            )
            # self.check_object_permissions(obj=user_reward_mission, request=self.request)
            return user_reward_mission
        except UserRewardMissionDoesNotExistException:
            raise NotFound

    def get_queryset(self):
        user = self.request.user
        self.gen_default_missions()
        user_reward_missions = self.user_reward_mission_service.list_user_reward_mission(
            user_id=user.user_id,
            **{
                "available": True
            }
        )
        return user_reward_missions

    def get_user_promo_code_queryset(self):
        user = self.request.user
        user_promo_codes = self.user_reward_mission_service.list_user_promo_codes(
            user_id=user.user_id
        )
        return user_promo_codes

    def gen_default_missions(self):
        user = self.request.user
        try:
            self.user_reward_mission_service.gen_user_default_missions(
                user_id=user.user_id
            )
        except UserDoesNotExistException:
            raise NotFound

    def list(self, request, *args, **kwargs):
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
        module_name = f'locker_server.shared.external_services.user_reward_mission.missions.' \
                      f'{user_reward_mission.mission_id}_mission'
        mission_factory = factory(module_name, mission_type, extra_requirements)
        if not mission_factory:
            return Response(status=status.HTTP_200_OK, data={"claim": False})
        input_data = {"user": user, "user_identifier": user_identifier}
        mission_check = mission_factory.check_mission_completion(input_data)
        answer = json.dumps(answer)
        if not mission_check:
            user_reward_mission.status = USER_MISSION_STATUS_UNDER_VERIFICATION
            self.user_reward_mission_service.update_user_reward_mission(
                user_reward_mission_id=user_reward_mission.user_reward_mission_id,
                user_reward_mission_update_data={
                    "answer": answer,
                    "status": USER_MISSION_STATUS_UNDER_VERIFICATION
                }
            )
            return Response(status=status.HTTP_200_OK, data={"claim": False})
        self.user_reward_mission_service.update_user_reward_mission(
            user_reward_mission_id=user_reward_mission.user_reward_mission_id,
            user_reward_mission_update_data={
                "answer": answer,
                "status": USER_MISSION_STATUS_REWARD_SENT
            }
        )

        # If the reward is premium time, upgrade the user plan immediately
        if user_reward_mission.mission.reward_type == REWARD_TYPE_PREMIUM:
            user_plan = self.user_service.get_current_plan(user=user)
            # Upgrade plan of the referred user if the plan is Free
            if user_plan.get_plan_type_alias() == PLAN_TYPE_PM_FREE:
                self.user_service.update_plan(user=user, plan_type_alias=PLAN_TYPE_PM_PREMIUM, **{
                    "start_period": now(),
                    "end_period": now() + user_reward_mission.mission.reward_value,
                })
            # Else, update extra time
            else:
                extra_time = user_reward_mission.mission.reward_value
                extra_plan = user_plan.extra_plan
                if not user_plan.extra_plan:
                    extra_plan = user_plan.pm_plan.alias
                self.user_service.update_user_plan_by_id(
                    user_plan_id=user_plan.pm_user_plan_id,
                    user_plan_update_data={
                        "extra_time": extra_time,
                        "extra_plan": extra_plan
                    }
                )

        return Response(status=status.HTTP_200_OK, data={"claim": True})

    @action(methods=["get"], detail=False)
    def claim(self, request, *args, **kwargs):
        user = self.request.user
        generated_promo_codes = self.user_reward_mission_service.list_user_generated_promo_codes(user_id=user.user_id)
        generated_promo_codes_srl = ListRewardPromoCodeSerializer(generated_promo_codes, many=True)
        result = self.user_reward_mission_service.get_claim(user_id=user.user_id)
        result.update({
            "generated_available_promo_codes": generated_promo_codes_srl.data
        })
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def list_promo_codes(self, request, *args, **kwargs):
        user_promo_codes = self.get_user_promo_code_queryset()
        serializer = self.get_serializer(user_promo_codes, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["post"], detail=False)
    def claim_promo_code(self, request, *args, **kwargs):

        user = self.request.user
        try:
            new_promo_code = self.user_reward_mission_service.claim_promo_code(
                user_id=user.user_id
            )
        except UserDoesNotExistException:
            raise NotFound
        except UserRewardPromoCodeInvalidException:
            raise ValidationError(detail={"promo_code": ["The available promo code value is not valid"]})
        # Create on Stripe
        if os.getenv("PROD_ENV") in ["prod", "staging"]:
            try:
                stripe.Coupon.create(
                    duration='once',
                    id="{}_yearly".format(new_promo_code.promo_code_id),
                    percent_off=new_promo_code.value,
                    name=new_promo_code.code,
                    redeem_by=new_promo_code.expired_time
                )
                stripe.Coupon.create(
                    duration='once',
                    id="{}_monthly".format(new_promo_code.promo_code_id),
                    percent_off=new_promo_code.value,
                    name=new_promo_code.code,
                    redeem_by=new_promo_code.expired_time
                )
            except stripe.error.StripeError:
                self.user_reward_mission_service.delete_promo_code_by_id(
                    promo_code_id=new_promo_code.promo_code_id
                )
            raise ValidationError({"non_field_errors": [gen_error("0008")]})

        return Response(status=status.HTTP_200_OK, data={
            "id": new_promo_code.promo_code_id,
            "code": new_promo_code.code
        })
