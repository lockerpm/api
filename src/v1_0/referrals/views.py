from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action

from shared.log.cylog import CyLog
from shared.permissions.locker_permissions.referral_pwd_permission import ReferralPwdPermission
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

        # Add 1 month Premium here
        # TODO: Add referral reward

        return Response(status=200, data={"success": True})
