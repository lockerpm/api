from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, When, Q, Case, IntegerField
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models.enterprises.enterprises import Enterprise
from shared.constants.enterprise_members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.enterprise_permission import EnterprisePwdPermission
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import ListEnterpriseSerializer, UpdateEnterpriseSerializer


class EnterprisePwdViewSet(EnterpriseViewSet):
    permission_classes = (EnterprisePwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            self.serializer_class = ListEnterpriseSerializer
        elif self.action in ["update"]:
            self.serializer_class = UpdateEnterpriseSerializer

        return super(EnterprisePwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
        except ObjectDoesNotExist:
            raise NotFound
        self.check_object_permissions(request=self.request, obj=enterprise)
        if self.action in ["update", "dashboard"]:
            if enterprise.locked:
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
        return enterprise

    def get_queryset(self):
        order_whens = [
            When(Q(enterprise_members__is_default=True), then=Value(1))
        ]
        user = self.request.user
        enterprises = Enterprise.objects.filter(
            enterprise_members__user=user, enterprise_members__status=E_MEMBER_STATUS_CONFIRMED
        ).annotate(
            is_default=Case(*order_whens, output_field=IntegerField(), default=Value(0))
        ).order_by('-is_default', '-creation_date')
        return enterprises

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        if paging_param == "0":
            self.pagination_class = None
        return super(EnterprisePwdViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super(EnterprisePwdViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        enterprise = self.get_object()
        # TODO: Log update activity here

        return super(EnterprisePwdViewSet, self).update(request, *args, **kwargs)

    @action(methods=["get"], detail=True)
    def dashboard(self, request, *args, **kwargs):
        # ----------- [COMING SOON] ------- #
        raise NotFound

