from typing import List

from rest_framework import status
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.enterprise_permissions.team_permission import TeamPwdPermission
from locker_server.core.entities.member.team_member import TeamMember
from locker_server.shared.constants.members import PM_MEMBER_STATUS_CONFIRMED


class TeamPwdViewSet(APIBaseViewSet):
    permission_classes = (TeamPwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_queryset(self):
        user_team_memberships = self.team_member_service.list_member_by_user(
            user_id=self.request.user.user_id,
            status=PM_MEMBER_STATUS_CONFIRMED,
            personal_share=False
        )
        return user_team_memberships

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
            normalize_page = self.normalize_team_memberships(
                team_memberships=page
            )
            return self.get_paginated_response(normalize_page)
        team_memberships_data = self.normalize_team_memberships(
            team_memberships=queryset
        )
        return Response(status=status.HTTP_200_OK, data=team_memberships_data)

    def normalize_team_memberships(self, team_memberships: List[TeamMember]):
        team_members_data = []
        for team_member in team_memberships:
            team = team_member.team
            data = {
                "id": team.team_id,
                "name": team.name,
                "description": team.description,
                "creation_date": team.creation_date,
                "revision_date": team.revision_date,
                "locked": team.locked,
                "organization_id": team.team_id,
                "is_default": team_member.is_default,
                "role": team_member.role.name,
            }
            primary_member = self.team_member_service.get_primary_member(
                team_id=team.team_id
            )
            if not primary_member:
                data["is_business"] = None
                data["plan_name"] = None
            current_plan = self.user_service.get_current_plan(user=primary_member.user)
            pm_plan_name = current_plan.pm_plan.name
            data["is_business"] = current_plan.pm_plan.is_team_plan
            data["plan_name"] = pm_plan_name
            team_members_data.append(data)
        return team_members_data
