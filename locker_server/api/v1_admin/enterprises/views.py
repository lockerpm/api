from typing import List

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from locker_server.api.api_base_view import APIBaseViewSet

from locker_server.core.exceptions.country_exception import CountryDoesNotExistException
from locker_server.core.exceptions.enterprise_exception import EnterpriseDoesNotExistException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.shared.constants.enterprise_members import E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN
from .serializers import *
from locker_server.api.permissions.admin_permissions.admin_enterprise_permission import AdminEnterprisePermission


class AdminEnterpriseViewSet(APIBaseViewSet):
    permission_classes = (AdminEnterprisePermission,)
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    lookup_value_regex = r'[0-9a-z-]+'

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListEnterpriseSerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailEnterpriseSerializer
        elif self.action == "create":
            self.serializer_class = CreateEnterpriseSerializer
        return super().get_serializer_class()

    def get_object(self):
        try:
            enterprise = self.enterprise_service.get_enterprise_by_id(
                enterprise_id=self.kwargs.get("pk")
            )
        except EnterpriseDoesNotExistException:
            raise NotFound
        self.check_object_permissions(request=self.request, obj=enterprise)
        return enterprise

    def get_queryset(self):
        enterprises = self.enterprise_service.list_enterprises()
        return enterprises

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            normalize_data = self.normalize_enterprises(serializer.data)
            return self.get_paginated_response(normalize_data)

        serializer = self.get_serializer(queryset, many=True)
        normalize_data = self.normalize_enterprises(serializer.data)
        return Response(status=status.HTTP_200_OK, data=normalize_data)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            primary_user = self.user_service.retrieve_by_email(
                email=validated_data.get("primary_admin")
            )
        except UserDoesNotExistException:
            primary_user = user
        try:
            new_enterprise = self.enterprise_service.create_enterprise(
                primary_user=primary_user,
                enterprise_create_data=validated_data
            )
        except CountryDoesNotExistException:
            raise ValidationError(detail={"enterprise_country": ["The country does not exist"]})

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                "id": new_enterprise.enterprise_id
            }
        )

    def normalize_enterprises(self, enterprises_data: List):
        normalize_datas = []
        for enterprise_data in enterprises_data:
            enterprise_id = enterprise_data.get("id")
            enterprise_admin_members = self.enterprise_member_service.list_enterprise_members(**{
                "enterprise_id": enterprise_id,
                "roles": [E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN]
            })
            enterprise_admin_datas = [
                {
                    "id": enterprise_admin_member.enterprise_member_id,
                    "role": enterprise_admin_member.role.name,
                    "user_id": enterprise_admin_member.user.user_id if enterprise_admin_member.user else None,
                    "email": enterprise_admin_member.email,
                    "status": enterprise_admin_member.status,
                    "is_activated": enterprise_admin_member.is_activated,
                }
                for enterprise_admin_member in enterprise_admin_members
            ]
            enterprise_data.update({
                "admins": enterprise_admin_datas
            })
            normalize_datas.append(enterprise_data)
        return normalize_datas
