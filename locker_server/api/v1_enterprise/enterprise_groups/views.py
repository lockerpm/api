from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.v1_enterprise.enterprise_members.serializers import DetailMemberSerializer
from locker_server.api.permissions.locker_permissions.enterprise_permissions.group_pwd_permission import \
    GroupPwdPermission
from locker_server.core.exceptions.enterprise_exception import EnterpriseDoesNotExistException
from locker_server.core.exceptions.enterprise_group_exception import EnterpriseGroupDoesNotExistException
from locker_server.shared.constants.event import EVENT_E_GROUP_CREATED, EVENT_E_GROUP_UPDATED, EVENT_E_GROUP_DELETED
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_EVENT, BG_ENTERPRISE_GROUP
from .serializers import *


class GroupPwdViewSet(APIBaseViewSet):
    permission_classes = (GroupPwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListEnterpriseGroupSerializer
        elif self.action == "retrieve":
            self.serializer_class = ShortDetailEnterpriseGroupSerializer
        elif self.action == "update":
            self.serializer_class = UpdateEnterpriseGroupSerializer
        elif self.action == "create":
            self.serializer_class = CreateEnterpriseGroupSerializer

        elif self.action == "members":
            if self.request.method == "GET":
                self.serializer_class = DetailMemberSerializer
            elif self.request.method == "PUT":
                self.serializer_class = UpdateMemberGroupSerializer
        return super(GroupPwdViewSet, self).get_serializer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action in ["list", "retrieve"]:
            context["count_group_members_func"] = self.enterprise_group_service.count_group_members
        elif self.action == "members":
            context["list_group_member_func"] = self.enterprise_member_service.list_groups_name_by_enterprise_member_id
        return context

    def get_queryset(self):
        enterprise = self.get_enterprise()
        groups = self.enterprise_group_service.list_enterprise_groups(**{
            "enterprise_id": enterprise.enterprise_id,
            "name": self.request.query_params.get("q")
        })
        return groups

    def get_object(self):
        enterprise = self.get_enterprise()
        try:
            group = self.enterprise_group_service.get_group_by_id(
                enterprise_group_id=self.kwargs.get("group_id")
            )
            if group.enterprise.enterprise_id != enterprise.enterprise_id:
                raise NotFound
            return group
        except EnterpriseGroupDoesNotExistException:
            raise NotFound

    def get_enterprise_group(self):
        try:
            group = self.enterprise_group_service.get_group_by_id(enterprise_group_id=self.kwargs.get("group_id"))
            self.check_object_permissions(request=self.request, obj=group.enterprise)
            return group
        except EnterpriseGroupDoesNotExistException:
            raise NotFound

    def get_enterprise(self):
        try:
            enterprise = self.enterprise_service.get_enterprise_by_id(enterprise_id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=enterprise)
            if enterprise.locked:
                raise ValidationError({"non_field_errors": [gen_error("3003")]})

            return enterprise
        except EnterpriseDoesNotExistException:
            raise NotFound

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        enterprise_group = self.get_object()
        serializer = self.get_serializer(enterprise_group)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        ip = self.get_ip()
        enterprise = self.get_enterprise()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        new_group = self.enterprise_group_service.create_group(
            enterprise=enterprise,
            user=user,
            enterprise_group_create_data=validated_data
        )
        BackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
            "enterprise_ids": [enterprise.enterprise_id], "acting_user_id": user.user_id, "user_id": user.user_id,
            "group_id": new_group.enterprise_group_id, "type": EVENT_E_GROUP_CREATED,
            "ip_address": ip, "metadata": {"group_name": new_group.name}
        })
        return Response(status=status.HTTP_201_CREATED, data={"id": new_group.enterprise_group_id})

    def update(self, request, *args, **kwargs):
        user = self.request.user
        ip = self.get_ip()
        enterprise_group = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            updated_group = self.enterprise_group_service.update_group(
                group_id=enterprise_group.enterprise_group_id,
                group_update_data=validated_data
            )
        except EnterpriseGroupDoesNotExistException:
            raise NotFound

        BackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
            "enterprise_ids": [enterprise_group.enterprise.enterprise_id], "acting_user_id": user.user_id,
            "user_id": user.user_id,
            "group_id": enterprise_group.enterprise_group_id, "type": EVENT_E_GROUP_UPDATED,
            "ip_address": ip, "metadata": {"old_name": enterprise_group.name, "new_name": updated_group.name}
        })
        return Response(status=status.HTTP_200_OK, data={"id": enterprise_group.enterprise_group_id})

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        ip = self.get_ip()
        enterprise_group = self.get_object()
        enterprise_id = enterprise_group.enterprise.enterprise_id
        enterprise_group_id = enterprise_group.enterprise_group_id
        enterprise_group_name = enterprise_group.name
        self.enterprise_group_service.delete_group_by_id(
            enterprise_group_id=enterprise_group_id
        )
        BackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
            "enterprise_ids": [enterprise_id], "acting_user_id": user.user_id, "user_id": user.user_id,
            "group_id": enterprise_group_id, "type": EVENT_E_GROUP_DELETED,
            "ip_address": ip, "metadata": {"group_name": enterprise_group_name}
        })
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["get", "put"], detail=False)
    def members(self, request, *args, **kwargs):
        enterprise_group = self.get_object()

        if request.method == "GET":
            group_members = self.enterprise_group_service.list_group_members(**{
                "enterprise_group_id": enterprise_group.enterprise_group_id
            })
            members = [group_member.member for group_member in group_members]
            serializer = self.get_serializer(members, many=True)
            return Response(status=status.HTTP_200_OK, data=serializer.data)

        elif request.method == "PUT":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            members = validated_data.get("members", [])
            new_member_ids = self.enterprise_group_service.update_members(
                enterprise_group=enterprise_group,
                enterprise_member_ids=members
            )
            if new_member_ids:
                BackgroundFactory.get_background(bg_name=BG_ENTERPRISE_GROUP).run(
                    func_name="add_group_member_to_share", **{
                        "enterprise_group": enterprise_group,
                        "new_member_ids": new_member_ids
                    }
                )
            return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["get"], detail=False)
    def user_groups(self, request, *args, **kwargs):
        user = self.request.user
        groups = self.enterprise_group_service.list_enterprise_groups(**{
            "user_id": user.user_id,
            "name": self.request.query_params.get("q")
        })
        groups_data = []
        for group in groups:
            groups_data.append({
                "id": group.enterprise_group_id,
                "name": group.name,
                "creation_date": group.creation_date,
                "revision_date": group.revision_date,
                "enterprise_id": group.enterprise.enterprise_id,
            })

        return Response(status=status.HTTP_200_OK, data=groups_data)

    @action(methods=["get"], detail=False)
    def members_list(self, request, *args, **kwargs):
        enterprise_group = self.get_enterprise_group()
        data = {
            "id": enterprise_group.enterprise_group_id,
            "creation_date": enterprise_group.creation_date,
            "revision_date": enterprise_group.revision_date,
            "name": enterprise_group.name,

        }
        group_members = self.enterprise_group_service.list_group_members(**{
            "enterprise_group_id": enterprise_group.enterprise_group_id
        })
        members_data = []
        for group_member in group_members:
            member = group_member.member
            member_data = {
                "email": member.email,
                "status": member.status,
                "role": member.role.name,
                "domain_id": member.domain.domain_id if member.domain else None,
                "is_activated": member.is_activated,
                "public_key": member.user.public_key if member.user else None
            }
            if member.user:
                member_data.update({
                    "email": member.user.email,
                    "full_name": member.user.full_name,
                    "username": member.user.username,
                    "avatar": member.user.get_avatar()
                })
            members_data.append(member_data)
        data["members"] = members_data
        return Response(status=status.HTTP_200_OK, data=data)
