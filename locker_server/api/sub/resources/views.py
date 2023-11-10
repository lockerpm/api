from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from locker_server.api.v1_0.resources.views import ResourcePwdViewSet as ResourceV1PwdViewSet
from .serializers import CountrySerializer


class ResourcePwdViewSet(ResourceV1PwdViewSet):
    """
    Resource ViewSet
    """

    def get_serializer_class(self):
        if self.action == "countries":
            self.serializer_class = CountrySerializer
        return super(ResourcePwdViewSet, self).get_serializer_class()

    @action(methods=["get"], detail=False)
    def countries(self, request, *args, **kwargs):
        countries = self.resource_service.list_countries()
        serializer = self.get_serializer(countries, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)
