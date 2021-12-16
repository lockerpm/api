from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from shared.background import *
from shared.constants.event import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.policy_pwd_permission import PolicyPwdPermission
from v1_0.enterprise.policy.serializers import PolicyDetailSerializer
from v1_0.apps import PasswordManagerViewSet


class PolicyPwdViewSet(PasswordManagerViewSet):
    permission_classes = (PolicyPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    
    def get_serializer_class(self):
        if self.action in ["retrieve", "update"]:
            self.serializer_class = PolicyDetailSerializer
        return super(PolicyPwdViewSet, self).get_serializer_class()
    
    def get_object(self):
        try:
            team = self.team_repository.get_by_id(team_id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=team)
            if self.team_repository.is_locked(team=team):
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
            policy = self.team_repository.retrieve_or_create_policy(team=team)
            return policy
        except ObjectDoesNotExist:
            raise NotFound
        
    def retrieve(self, request, *args, **kwargs):
        return super(PolicyPwdViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        ip = request.data.get("ip")
        user = request.user
        policy = self.get_object()
        team = policy.team
        serializer = self.get_serializer(policy, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
            "team_id": team.id, "user_id": user.user_id, "acting_user_id": user.user_id,
            "type": EVENT_TEAM_POLICY_UPDATED, "ip_address": ip
        })
        return Response(status=200, data=serializer.data)

