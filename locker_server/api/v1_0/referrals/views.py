from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action

from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.shared.constants.transactions import PLAN_TYPE_PM_PREMIUM, REFERRAL_LIMIT, REFERRAL_EXTRA_TIME, \
    PLAN_TYPE_PM_FREE
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.utils.app import now
from .serializers import ClaimSerializer
from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.referral_pwd_permisison import ReferralPwdPermission


class ReferralPwdViewSet(APIBaseViewSet):
    permission_classes = (ReferralPwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "claim":
            self.serializer_class = ClaimSerializer
        return super().get_serializer_class()

    @action(methods=["post"], detail=False)
    def claim(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        referred_by = validated_data.get("referred_by")
        count = validated_data.get("count")
        CyLog.info(**{"message": "Claim referral code: {} {}".format(user, validated_data)})
        try:
            referred_by_user = self.user_service.retrieve_by_id(user_id=referred_by)
        except UserDoesNotExistException:
            raise ValidationError(detail={"referred_by": ["The referred_by id does not exist"]})

        # Upgrade current user to Premium
        current_time = now()
        self.user_service.update_plan(user=user, plan_type_alias=PLAN_TYPE_PM_PREMIUM, **{
            "start_period": current_time,
            "end_period": current_time + 30 * 86400,
            "cancel_at_period_end": True
        })
        # Get current plan of the referred user
        if count < REFERRAL_LIMIT:
            referred_user_plan = self.user_service.get_current_plan(
                user=referred_by_user
            )
            # Upgrade plan of the referred user if the plan is Free
            if referred_user_plan.get_plan_type_alias() == PLAN_TYPE_PM_FREE:
                self.user_service.update_plan(
                    user=referred_by_user,
                    plan_type_alias=PLAN_TYPE_PM_PREMIUM,
                    **{
                        "start_period": current_time,
                        "end_period": current_time + REFERRAL_EXTRA_TIME,
                        "cancel_at_period_end": True
                    }
                )
            # Else, update extra time
            else:
                user_plan_update_data = {
                    "extra_time": REFERRAL_EXTRA_TIME
                }
                self.user_service.update_user_plan_by_id(
                    user_plan_id=referred_user_plan.pm_user_plan_id,
                    user_plan_update_data=user_plan_update_data
                )
        return Response(status=status.HTTP_200_OK, data={"success": True})
