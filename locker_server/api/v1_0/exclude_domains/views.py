from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.exclude_domain_pwd_permission import ExcludeDomainPwdPermission
from locker_server.core.exceptions.exclude_domain_exception import ExcludeDomainNotExistException
from .serializers import ExcludeDomainSerializer


class ExcludeDomainPwdViewSet(APIBaseViewSet):
    permission_classes = (ExcludeDomainPwdPermission,)
    http_method_names = ["options", "head", "get", "post", "delete"]
    lookup_value_regex = r'[0-9a-z-]+'
    serializer_class = ExcludeDomainSerializer

    def get_throttles(self):
        return super().get_throttles()

    def get_serializer_class(self):
        return super().get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        exclude_domains = self.exclude_domain_service.list_user_exclude_domains(
            user_id=user.user_id,
            **{
                "q": self.request.query_params.get("q")
            }
        )
        return exclude_domains

    def get_object(self):
        user = self.request.user
        try:
            exclude_domain = self.exclude_domain_service.get_user_exclude_domain(
                user_id=user.user_id, exclude_domain_id=self.kwargs.get("pk")
            )
            return exclude_domain
        except ExcludeDomainNotExistException:
            raise NotFound

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 50))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 50
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        domain = validated_data.get("domain")
        exclude_domain = self.exclude_domain_service.create_exclude_domain(user_id=user.user_id, domain=domain)
        return Response(status=status.HTTP_201_CREATED, data={"id": exclude_domain.exclude_domain_id})

    def destroy(self, request, *args, **kwargs):
        exclude_domain = self.get_object()
        self.exclude_domain_service.delete_exclude_domain(exclude_domain_id=exclude_domain.exclude_domain_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
