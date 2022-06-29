from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from shared.permissions.locker_permissions.domain_pwd_permission import DomainPwdPermission
from v1_0.apps import PasswordManagerViewSet
from v1_0.enterprise.domains.serializers import ListDomainSerializer


class DomainPwdViewSet(PasswordManagerViewSet):
    permission_classes = (DomainPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListDomainSerializer
        return super(DomainPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            team = self.get_team()
            domain = team.domains.get(id=self.kwargs.get("domain_id"))
            return domain
        except ObjectDoesNotExist:
            raise NotFound

    def get_team(self):
        try:
            team = self.team_repository.get_by_id(team_id=self.kwargs.get("pk"))
            if team.personal_share:
                raise NotFound
            self.check_object_permissions(request=self.request, obj=team)
            return team
        except ObjectDoesNotExist:
            raise NotFound

    def get_queryset(self):
        team = self.get_team()
        domains = team.domains.all().order_by('-created_time')
        return domains

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        if paging_param == "0":
            self.pagination_class = None
        return super(DomainPwdViewSet, self).list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        domain = self.get_object()
        domain.delete()
        return Response(status=204)
