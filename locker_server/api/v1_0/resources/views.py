from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.shared.constants.market_banner import LIST_MARKETS
from .serializers import PMPlanSerializer, ListMailProviderSerializer


class ResourcePwdViewSet(APIBaseViewSet):
    permission_classes = ()
    http_method_names = ["head", "options", "get"]

    def get_serializer_class(self):
        if self.action in ["plans", "enterprise_plans"]:
            self.serializer_class = PMPlanSerializer
        elif self.action == "mail_providers":
            self.serializer_class = ListMailProviderSerializer
        return super(ResourcePwdViewSet, self).get_serializer_class()

    @action(methods=["get"], detail=False)
    def plans(self, request, *args, **kwargs):
        personal_plan = self.resource_service.list_personal_plans()
        serializer = self.get_serializer(personal_plan, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["get"], detail=False)
    def enterprise_plans(self, request, *args, **kwargs):
        enterprise_plans = self.resource_service.list_enterprise_plans()
        serializer = self.get_serializer(enterprise_plans, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["get"], detail=False)
    def mail_providers(self, request, *args, **kwargs):
        mail_providers = self.resource_service.list_mail_providers()
        serializer = self.get_serializer(mail_providers, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(methods=["get"], detail=False)
    def market_banners(self, request, *args, **kwargs):
        market_banners = LIST_MARKETS
        available_market_banners = [
            market_banner for market_banner in market_banners
            if market_banner.get("available") is True
        ]

        return Response(status=status.HTTP_200_OK, data=available_market_banners)
