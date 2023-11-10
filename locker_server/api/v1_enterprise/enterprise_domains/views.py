from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from locker_server.core.exceptions.enterprise_domain_exception import *
from locker_server.core.exceptions.enterprise_exception import EnterpriseDoesNotExistException
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_DOMAIN
from .serializers import *
from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.enterprise_permissions.domain_pwd_permission import \
    DomainPwdPermission


class DomainPwdViewSet(APIBaseViewSet):
    permission_classes = (DomainPwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListDomainSerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailDomainSerializer
        elif self.action == "create":
            self.serializer_class = CreateDomainSerializer
        elif self.action == "update":
            self.serializer_class = UpdateDomainSerializer
        return super().get_serializer_class()

    def get_object(self):
        try:
            enterprise = self.get_enterprise()
            domain = self.enterprise_domain_service.get_domain_by_id(
                domain_id=self.kwargs.get("domain_id")
            )
            if domain.enterprise.enterprise_id != enterprise.enterprise_id:
                raise NotFound
            return domain
        except DomainDoesNotExistException:
            raise NotFound

    def get_enterprise(self):
        try:
            enterprise = self.enterprise_service.get_enterprise_by_id(
                enterprise_id=self.kwargs.get("pk")
            )
            self.check_object_permissions(request=self.request, obj=enterprise)
            if enterprise.locked:
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
            return enterprise
        except EnterpriseDoesNotExistException:
            raise NotFound

    def get_queryset(self):
        enterprise = self.get_enterprise()
        domains = self.enterprise_domain_service.list_enterprise_domains(
            enterprise_id=enterprise.enterprise_id
        )
        return domains

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        size_param = self.request.query_params.get("size", 10)
        page_size_param = self.check_int_param(size_param)
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param or 10
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            new_domain = self.enterprise_domain_service.create_domain(
                domain_create_data={
                    "enterprise_id": enterprise.enterprise_id,
                    "domain": validated_data.get("domain"),
                    "root_domain": validated_data.get("root_domain")
                }
            )
        except EnterpriseDoesNotExistException:
            raise NotFound
        except DomainExistedException:
            raise ValidationError(detail={"domain": ["The domain is existed"]})
        except DomainVerifiedByOtherException:
            raise ValidationError(detail={"domain": ["This domain is verified by other enterprise"]})

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                "id": new_domain.domain_id,
                "domain": new_domain.domain,
                "verification": new_domain.verification
            }
        )

    def update(self, request, *args, **kwargs):
        ip_address = self.get_ip()
        domain = self.get_object()
        if domain.verification is False:
            raise ValidationError({"non_field_errors": [gen_error("3005")]})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        auto_approve = validated_data.get("auto_approve")
        try:
            updated_domain = self.enterprise_domain_service.update_domain(
                domain_id=domain.domain,
                domain_update_data={
                    "auto_approve": auto_approve
                }
            )
        except DomainDoesNotExistException:
            raise NotFound
        # Accept all requested members if the auto_approve is True
        if updated_domain.auto_approve is True:
            BackgroundFactory.get_background(bg_name=BG_DOMAIN, background=False).run(
                func_name="domain_auto_approve", **{
                    "user_id_update_domain": self.request.user.user_id,
                    "domain": updated_domain,
                    "ip_address": ip_address
                }
            )

        return Response(status=status.HTTP_200_OK, data={"id": updated_domain.domain_id})

    def destroy(self, request, *args, **kwargs):
        domain = self.get_object()
        try:
            self.enterprise_domain_service.delete_domain(
                domain_id=domain.domain_id
            )
        except DomainDoesNotExistException:
            raise NotFound
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["get", "post"], detail=False)
    def verification(self, request, *args, **kwargs):
        user = request.user
        domain = self.get_object()
        if request.method == "GET":
            ownerships = self.enterprise_domain_service.get_ownerships_by_domain_id(
                domain_id=domain.domain_id
            )
            return Response(status=status.HTTP_200_OK, data=ownerships)

        elif request.method == "POST":
            if domain.verification is True:
                return Response(
                    status=status.HTTP_200_OK,
                    data={
                        "success": True,
                        "domain": domain.domain,
                    }
                )
            try:
                self.enterprise_domain_service.verify_domain(domain=domain)
            except DomainVerifiedByOtherException:
                raise ValidationError(detail={"domain": ["This domain is verified by other enterprise"]})
            except DomainVerifiedErrorException:
                raise ValidationError({"non_field_errors": [gen_error("3005")]})

            invited_number = BackgroundFactory.get_background(bg_name=BG_DOMAIN, background=False).run(
                func_name="domain_verified", **{
                    "owner_user_id": user.user_id,
                    "domain": domain
                }
            )
            return Response(
                status=status.HTTP_200_OK,
                data={
                    "success": True,
                    "domain": domain.domain,
                    "enterprise_name": domain.enterprise.name,
                    "organization_name": domain.enterprise.name,
                    "invited_number": invited_number
                }
            )
