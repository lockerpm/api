from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.enterprises.domains.domains import Domain
from shared.error_responses.error import gen_error, refer_error
from shared.permissions.locker_permissions.enterprise.domain_permission import DomainPwdPermission
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import ListDomainSerializer, CreateDomainSerializer, UpdateDomainSerializer


class DomainPwdViewSet(EnterpriseViewSet):
    permission_classes = (DomainPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListDomainSerializer
        elif self.action == "create":
            self.serializer_class = CreateDomainSerializer
        elif self.action == "update":
            self.serializer_class = UpdateDomainSerializer
        return super(DomainPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            enterprise = self.get_enterprise()
            domain = enterprise.domains.get(id=self.kwargs.get("domain_id"))
            return domain
        except ObjectDoesNotExist:
            raise NotFound

    def get_enterprise(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=enterprise)
            return enterprise
        except Enterprise.DoesNotExist:
            raise NotFound

    def get_queryset(self):
        enterprise = self.get_enterprise()
        domains = enterprise.domains.all().order_by('-created_time')
        return domains

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        if paging_param == "0":
            self.pagination_class = None
        return super(DomainPwdViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        domain = validated_data.get("domain")
        root_domain = validated_data.get("root_domain")

        if enterprise.domains.filter(domain=domain).exists():
            raise ValidationError(detail={"domain": ["The domain is existed"]})
        if Domain.objects.exclude(enterprise_id=enterprise.id).filter(
            root_domain=root_domain, verification=True
        ).exists():
            raise ValidationError(detail={"domain": ["This domain is verified by other enterprise"]})

        # Create new domain
        is_verified = enterprise.domains.filter(root_domain=root_domain, verification=True).exists()
        domain = enterprise.domains.model.create(
            enterprise=enterprise, domain=domain, root_domain=root_domain, verification=is_verified
        )
        return Response(status=201, data={
            "id": domain.id, "domain": domain.domain, "verification": domain.verification
        })

    def update(self, request, *args, **kwargs):
        domain = self.get_object()
        if domain.verification is False:
            raise ValidationError({"non_field_errors": [gen_error("3005")]})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        auto_approve = validated_data.get("auto_approve")
        domain.auto_approve = auto_approve
        domain.save()
        return Response(status=200, data={"id": domain.id})

    def destroy(self, request, *args, **kwargs):
        domain = self.get_object()
        domain.delete()
        return Response(status=204)

    @action(methods=["get", "post"], detail=False)
    def verification(self, request, *args, **kwargs):
        domain = self.get_object()
        if request.method == "GET":
            ownerships = domain.get_verifications()
            return Response(status=200, data=ownerships)

        elif request.method == "POST":
            if domain.verification is True:
                return Response(status=200, data={
                    "success": True,
                    "domain": domain.domain,
                })
            if Domain.objects.exclude(enterprise_id=domain.enterprise_id).filter(
                root_domain=domain.root_domain, verification=True
            ).exists():
                raise ValidationError(detail={"domain": ["This domain is verified by other enterprise"]})
            is_verify = domain.check_verification()
            if is_verify is True:
                return Response(status=200, data={
                    "success": True,
                    "domain": domain.domain,
                    "organization_name": domain.enterprise.name
                })
            return Response(status=200, data=refer_error(gen_error("3005")))
