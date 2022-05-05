from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import F
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action

from shared.constants.transactions import PLAN_TYPE_PM_PREMIUM, PLAN_TYPE_PM_FREE, REFERRAL_EXTRA_TIME
from shared.log.cylog import CyLog
from shared.permissions.locker_permissions.referral_pwd_permission import ReferralPwdPermission
from shared.utils.app import now
from v1_0.referrals.serializers import ClaimSerializer
from v1_0.apps import PasswordManagerViewSet


class ReferralPwdViewSet(PasswordManagerViewSet):
    permission_classes = (ReferralPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "claim":
            self.serializer_class = ClaimSerializer
        return super(ReferralPwdViewSet, self).get_serializer_class()

    @action(methods=["post"], detail=False)
    def claim(self, request, *args, **kwargs):
        current_time = now()
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        referred_by = validated_data.get("referred_by")
        CyLog.info(**{"message": "Claim referral code: {} {}".format(user, validated_data)})
        try:
            referred_by_user = self.user_repository.get_by_id(user_id=referred_by)
        except ObjectDoesNotExist:
            raise ValidationError(detail={"referred_by": ["The referred_by id does not exist"]})

        # Upgrade current user to Premium
        self.user_repository.update_plan(user=user, plan_type_alias=PLAN_TYPE_PM_PREMIUM, **{
            "start_period": current_time,
            "end_period": current_time + 30 * 86400,
            "cancel_at_period_end": True
        })
        # Get current plan of the referred user
        referred_user_plan = self.user_repository.get_current_plan(
            user=referred_by_user, scope=settings.SCOPE_PWD_MANAGER
        )
        # Upgrade plan of the referred user if the plan is Free
        if referred_user_plan.get_plan_type_alias() == PLAN_TYPE_PM_FREE:
            self.user_repository.update_plan(user=referred_by_user, plan_type_alias=PLAN_TYPE_PM_PREMIUM, **{
                "start_period": current_time,
                "end_period": current_time + 30 * 86400,
                "cancel_at_period_end": True
            })
        # Else, update extra time
        else:
            referred_user_plan.extra_time = F('extra_time') + REFERRAL_EXTRA_TIME
            referred_user_plan.save()
        return Response(status=200, data={"success": True})
