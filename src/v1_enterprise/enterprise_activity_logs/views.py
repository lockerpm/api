from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.events.events import Event
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.enterprise.activity_log_permission import ActivityLogPwdPermission
from shared.utils.app import now
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import ActivityLogSerializer


class ActivityLogPwdViewSet(EnterpriseViewSet):
    permission_classes = (ActivityLogPwdPermission, )
    http_method_names = ["head", "options", "get"]
    serializer_class = ActivityLogSerializer

    def get_serializer_class(self):
        return super(ActivityLogPwdViewSet, self).get_serializer_class()

    def get_enterprise(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=enterprise)
            if enterprise.locked:
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
            enterprise = self.check_allow_plan(enterprise=enterprise)
            return enterprise
        except Enterprise.DoesNotExist:
            raise NotFound

    def check_allow_plan(self, enterprise):
        primary_user = enterprise.enterprise_members.get(is_primary=True).user
        current_plan = self.user_repository.get_current_plan(user=primary_user)
        plan_obj = current_plan.get_plan_obj()
        if plan_obj.allow_team_activity_log() is False:
            raise ValidationError({"non_field_errors": [gen_error("7002")]})
        return enterprise

    def get_queryset(self):
        enterprise = self.get_enterprise()
        to_param = self.check_int_param(self.request.query_params.get("to")) or now()
        from_param = self.check_int_param(self.request.query_params.get("from")) or now() - 30 * 86400

        events = Event.objects.filter(team_id=enterprise.id).order_by('-creation_date').filter(
            creation_date__lte=to_param,
            creation_date__gte=from_param
        )
        return events

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 50))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 50
        return super(ActivityLogPwdViewSet, self).list(request, *args, **kwargs)
