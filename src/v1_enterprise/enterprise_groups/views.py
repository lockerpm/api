from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.enterprises.groups.groups import EnterpriseGroup
from shared.background import LockerBackgroundFactory, BG_EVENT
from shared.constants.event import EVENT_E_MEMBER_UPDATED_ROLE, EVENT_E_GROUP_CREATED, EVENT_E_GROUP_UPDATED, \
    EVENT_E_GROUP_DELETED
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.enterprise.group_permission import GroupPwdPermission
from shared.utils.app import now
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import EnterpriseGroupSerializer


class GroupPwdViewSet(EnterpriseViewSet):
    permission_classes = (GroupPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    serializer_class = EnterpriseGroupSerializer

    def get_serializer_class(self):
        return super(GroupPwdViewSet, self).get_serializer_class()

    def get_queryset(self):
        enterprise = self.get_enterprise()
        groups = enterprise.groups.all().order_by('-creation_date')
        q_param = self.request.query_params.get("q")
        if q_param:
            groups = groups.filter(name__icontains=q_param.lower())
        return groups

    def get_object(self):
        enterprise = self.get_enterprise()
        try:
            group = enterprise.groups.get(id=self.kwargs.get("group_id"))
            return group
        except EnterpriseGroup.DoesNotExist:
            raise NotFound

    def get_enterprise(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=enterprise)
            if enterprise.locked:
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
            return enterprise
        except Enterprise.DoesNotExist:
            raise NotFound

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10
        return super(GroupPwdViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        enterprise = self.get_enterprise()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        name = validated_data.get("name")

        new_group = EnterpriseGroup.create(enterprise, name)

        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
            "enterprise_ids": [enterprise.id], "acting_user_id": user.user_id, "user_id": user.user_id,
            "group_id": new_group.id, "type": EVENT_E_GROUP_CREATED,
            "ip_address": ip, "metadata": {"group_name": new_group.name}
        })
        return Response(status=200, data={"id": new_group.id})

    def update(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        enterprise_group = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        name = validated_data.get("name")
        old_name = enterprise_group.name
        enterprise_group.name = name
        enterprise_group.revision_date = now()
        enterprise_group.save()
        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
            "enterprise_ids": [enterprise_group.enterprise_id], "acting_user_id": user.user_id, "user_id": user.user_id,
            "group_id": enterprise_group.id, "type": EVENT_E_GROUP_UPDATED,
            "ip_address": ip, "metadata": {"old_name": old_name, "new_name": name}
        })
        return Response(status=200, data={"id": enterprise_group.id})

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        enterprise_group = self.get_object()
        enterprise_id = enterprise_group.enterprise_id
        enterprise_group_id = enterprise_group.id
        enterprise_group_name = enterprise_group.name
        enterprise_group.delete()
        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
            "enterprise_ids": [enterprise_id], "acting_user_id": user.user_id, "user_id": user.user_id,
            "group_id": enterprise_group_id, "type": EVENT_E_GROUP_DELETED,
            "ip_address": ip, "metadata": {"group_name": enterprise_group_name}
        })
        return Response(status=204)

