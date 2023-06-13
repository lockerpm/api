from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from shared.permissions.locker_permissions.exclude_domain_pwd_permission import ExcludeDomainPwdPermission
from v1_0.exclude_domains.serializers import ExcludeDomainSerializer
from v1_0.general_view import PasswordManagerViewSet


class ExcludeDomainPwdViewSet(PasswordManagerViewSet):
    permission_classes = (ExcludeDomainPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "delete"]
    serializer_class = ExcludeDomainSerializer

    def get_serializer_class(self):
        return super().get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        exclude_domains = user.exclude_domains.all().order_by('-created_time')
        q_param = self.request.query_params.get("q")
        if q_param:
            exclude_domains = exclude_domains.filter(q__icontains=q_param)
        return exclude_domains

    def get_object(self):
        user = self.request.user
        try:
            exclude_domain = user.exclude_domains.get(id=self.kwargs.get("pk"))
            return exclude_domain
        except ObjectDoesNotExist:
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
        exclude_domain = user.exclude_domains.model.retrieve_or_create(domain, user)
        return Response(status=201, data={"id": exclude_domain.id})

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
