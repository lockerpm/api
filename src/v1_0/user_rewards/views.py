from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.decorators import action

from cystack_models.models import UserRewardMission, Mission
from shared.permissions.locker_permissions.user_reward_mission_pwd_permission import UserRewardMissionPwdPermission
from v1_0.user_rewards.serializers import UserRewardMissionSerializer
from v1_0.general_view import PasswordManagerViewSet


class UserRewardMissionPwdViewSet(PasswordManagerViewSet):
    permission_classes = (UserRewardMissionPwdPermission,)
    http_method_names = ["head", "options", "get", "post"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = UserRewardMissionSerializer
        return super().get_serializer_class()

    def get_object(self):
        user = self.request.user
        try:
            user_reward_mission = UserRewardMission.objects.get(
                user_id=user.user_id, mission_id=self.kwargs.get("pk")
            )
            self.check_object_permissions(obj=user_reward_mission, request=self.request)
            return user_reward_mission
        except UserRewardMission.DoesNotExist:
            raise NotFound

    def get_queryset(self):
        user = self.request.user
        self.gen_default_missions()
        user_reward_missions = user.user_reward_missions.all().select_related(
            'mission'
        ).order_by('mission__order_index')

        return user_reward_missions

    def gen_default_missions(self):
        user = self.request.user
        mission_ids = list(Mission.objects.all().order_by('order_index').values_list('id', flat=True))
        user.user_reward_missions.model.create_multiple_user_reward_missions(user, mission_ids)

    def list(self, request, *args, **kwargs):
        # self.check_pwd_session_auth(request)
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 50))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 50
        return super().list(request, *args, **kwargs)


