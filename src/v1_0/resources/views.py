from rest_framework.response import Response
from rest_framework.decorators import action

from cystack_models.models.user_plans.pm_plans import PMPlan
from shared.constants.transactions import PLAN_TYPE_PM_LIFETIME
from v1_0.resources.serializers import PMPlanSerializer
from v1_0.general_view import PasswordManagerViewSet


class ResourcePwdViewSet(PasswordManagerViewSet):
    permission_classes = ()
    http_method_names = ["head", "options", "get"]

    def get_serializer_class(self):
        if self.action in ["plans", "enterprise_plans"]:
            self.serializer_class = PMPlanSerializer
        return super(ResourcePwdViewSet, self).get_serializer_class()

    @action(methods=["get"], detail=False)
    def plans(self, request, *args, **kwargs):
        all_plans = PMPlan.objects.all().exclude(
            alias=PLAN_TYPE_PM_LIFETIME
        ).exclude(is_team_plan=True).order_by('id')
        serializer = self.get_serializer(all_plans, many=True)
        return Response(status=200, data=serializer.data)

    @action(methods=["get"], detail=False)
    def enterprise_plans(self, request, *args, **kwargs):
        all_plans = PMPlan.objects.all().filter(is_team_plan=True).order_by('id')
        serializer = self.get_serializer(all_plans, many=True)
        return Response(status=200, data=serializer.data)
