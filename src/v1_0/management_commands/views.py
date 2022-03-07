from django.conf import settings
from django.db import close_old_connections
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from shared.background.i_background import BackgroundThread
from v1_0.apps import PasswordManagerViewSet


class ManagementCommandPwdViewSet(PasswordManagerViewSet):
    authentication_classes = ()
    permission_classes = ()
    http_method_names = ["head", "options", "post"]

    def check_perms(self):
        token = self.request.META.get("HTTP_TOKEN", None)
        if token != settings.MANAGEMENT_COMMAND_TOKEN:
            raise PermissionDenied
        return True

    @action(methods=["post"], detail=False)
    def commands(self, request, *args, **kwargs):
        self.check_perms()
        command_name = kwargs.get("pk")
        if not command_name:
            raise NotFound
        try:
            func = getattr(self, command_name)
        except AttributeError:
            raise ValidationError(detail={"pk": ["This is not a func command"]})
        if not func:
            raise ValidationError(detail={"pk": ["This is not a func command"]})
        if not callable(func):
            raise ValidationError(detail={"pk": ["This is not callable"]})
        close_old_connections()
        func_data = request.data.get("data", {})
        background = request.data.get("background", True)
        # Run background or not this function
        try:
            if background:
                BackgroundThread(task=func, **func_data)
            else:
                result = func(**func_data)
                if result:
                    return Response(status=200, data=result)
        except TypeError as e:
            raise ValidationError(detail={"err": e.__str__()})
        return Response(status=200, data={"id": command_name})

    def set_user_plan(self, user_id, start_period, end_period, cancel_at_period_end, default_payment_method, plan_id,
                      pm_mobile_subscription):
        user = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
        pm_user_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        pm_user_plan.start_period = start_period
        pm_user_plan.end_period = end_period
        if cancel_at_period_end is not None:
            pm_user_plan.cancel_at_period_end = cancel_at_period_end
        if default_payment_method is not None:
            pm_user_plan.default_payment_method = default_payment_method
        if plan_id is not None:
            pm_user_plan.pm_plan_id = plan_id
        if pm_mobile_subscription is not None:
            pm_user_plan.pm_mobile_subscription = pm_mobile_subscription
        pm_user_plan.save()
        return {
            "user_id":  pm_user_plan.user_id,
            "start_period": pm_user_plan.start_period,
            "end_period": pm_user_plan.end_period,
            "cancel_at_period": pm_user_plan.cancel_at_period_end,
            "default_payment_method": pm_user_plan.default_payment_method,
            "plan_id": pm_user_plan.pm_plan_id,
            "pm_mobile_subscription": pm_user_plan.pm_mobile_subscription
        }
