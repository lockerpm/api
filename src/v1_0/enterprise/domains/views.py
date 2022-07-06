from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from shared.constants.domain_ownership import TYPE_DNS_TXT
from shared.error_responses.error import gen_error, refer_error
from shared.permissions.locker_permissions.domain_pwd_permission import DomainPwdPermission
from v1_0.apps import PasswordManagerViewSet
from v1_0.enterprise.domains.serializers import ListDomainSerializer, CreateDomainSerializer


class DomainPwdViewSet(PasswordManagerViewSet):
    permission_classes = (DomainPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListDomainSerializer
        elif self.action == "create":
            self.serializer_class = CreateDomainSerializer
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

    def create(self, request, *args, **kwargs):
        team = self.get_team()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        domain = validated_data.get("domain")
        root_domain = validated_data.get("root_domain")

        is_verified = team.domains.filter(root_domain=root_domain, verification=True).exists()
        domain = team.domains.model.create(team=team, domain=domain, root_domain=root_domain, verification=is_verified)
        return Response(status=201, data={"id": domain.id, "domain": domain.domain})

    def destroy(self, request, *args, **kwargs):
        domain = self.get_object()
        domain.delete()
        return Response(status=204)

    @action(methods=["get", "post"], detail=False)
    def verification(self, request, *args, **kwargs):
        user = self.request.user
        domain = self.get_object()

        if request.method == "GET":
            ownerships = domain.get_verifications()
            # ownership = ownerships[0] if ownerships else {}
            return Response(status=200, data=ownerships)

        elif request.method == "POST":
            if domain.verification is True:
                return Response(status=200, data={
                    "success": True,
                    "domain": domain.domain,
                })

            is_verify = domain.check_verification()
            if is_verify is True:
                return Response(status=200, data={
                    "success": True,
                    "domain": domain.domain,
                    "organization_name": domain.team.name
                })
            return Response(status=200, data=refer_error(gen_error("3005")))
