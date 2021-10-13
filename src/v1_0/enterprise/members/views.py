from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, When, Q, Case, IntegerField
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from shared.constants.members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.member_pwd_permission import MemberPwdPermission
from shared.permissions.locker_permissions.team_pwd_permission import TeamPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_DELETE, SYNC_EVENT_CIPHER_CREATE, \
    SYNC_EVENT_CIPHER_UPDATE
from cystack_models.models.teams.teams import Team
from cystack_models.models.members.team_members import TeamMember
from v1_0.enterprise.members.serializers import DetailMemberSerializer
from v1_0.apps import PasswordManagerViewSet


class MemberPwdViewSet(PasswordManagerViewSet):
    permission_classes = (MemberPwdPermission, )
    lookup_value_regex = r'[0-9a-z\-]+'
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action in ["group"]:
            self.serializer_class = None
        return super(MemberPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            team = self.team_repository.get_by_id(team_id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=team)
            if self.action in ["create", "update", "invitation_member", "public_key"]:
                if self.team_repository.is_locked(team):
                    raise ValidationError({"non_field_errors": [gen_error("3003")]})
            return team
        except Team.DoesNotExist:
            raise NotFound

    def list(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        team = self.get_object()
        # Filter owner param
        filter_owner_param = self.request.query_params.get("owner", "0")
        # Param to find member by user id
        user_ids_param = self.request.query_params.get("user_ids", None)
        email_param = self.request.query_params.get("email", None)

        # Get list existed members
        # `whens` query to order list members (owner => admin => member)
        order_whens = [
            When(Q(role__name=MEMBER_ROLE_OWNER, user__isnull=False), then=Value(2)),
            When(Q(role__name=MEMBER_ROLE_ADMIN, user__isnull=False), then=Value(3)),
            When(Q(role__name=MEMBER_ROLE_MEMBER, user__isnull=False), then=Value(4))
        ]

        # Get list role to filter
        list_role = []
        if filter_owner_param == "1":
            list_role.append(MEMBER_ROLE_OWNER)

        # Get all members of the team
        member_qs = team.team_members.filter()
        # Filter list role
        if list_role:
            member_qs = member_qs.filter(role__name__in=list_role)
        # Filter by q_param: search members
        if user_ids_param:
            try:
                user_ids_param = list(map(int, user_ids_param.split(",")))
                member_qs = member_qs.filter(user_id__in=user_ids_param).distinct()
            except:
                pass
        if email_param:
            member_qs = member_qs.filter(email__icontains=email_param)

        # Order by `order_whens`
        member_qs = member_qs.annotate(
            order_field=Case(*order_whens, output_field=IntegerField(), default=Value(4))
        ).order_by("order_field")
        member_serializer = DetailMemberSerializer(member_qs, many=True)
        return Response(status=200, data=member_serializer.data)

    def create(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        team = self.get_object()
        added_members = []
        members = request.data.get("members")
        # Validate members
        if not isinstance(members, list):
            raise ValidationError(detail={"members": ["Members are not valid. This field must be an array"]})
        # Check the maximum number of members
        current_total_members = team.team_members.all().count()
        primary_user = self.team_repository.get_primary_member(team=team).user
        max_allow_members = self.user_repository.get_current_plan(
            user=primary_user, scope=settings.SCOPE_PWD_MANAGER
        ).get_max_allow_members()
        if max_allow_members and current_total_members + len(members) > max_allow_members:
            raise ValidationError({"non_field_errors": [gen_error("3002")]})

        # Get list collection ids of this team
        collection_ids = list(team.collections.values_list('id', flat=True))
        # Loop list members data
        for member in members:
            try:
                team.team_members.get(user_id=member["user_id"])
            except TeamMember.DoesNotExist:
                collections = member.get("collections", [])
                valid_collections = [collection_id for collection_id in collections if collection_id in collection_ids]
                role = member["role"]
                member_collections = [] if role in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN] else valid_collections
                member_user = self.user_repository.retrieve_or_create_by_id(user_id=member["user_id"])
                member_obj = team.team_members.model.create_with_collections(
                    team=team, user=member_user, role_id=role, status=PM_MEMBER_STATUS_INVITED, *member_collections
                )
                added_members.append(member_obj.user_id)

        result = {
            "team_id": team.id,
            "team_name": team.name,
            "members": added_members
        }
        return Response(status=200, data=result)

    def update(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)

        return Response(status=200, data={})

    def destroy(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)

    @action(methods=["post"], detail=False)
    def invitation_member(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        team = self.get_object()


    @action(methods=["post"], detail=False)
    def confirm(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        team = self.get_object()
        member_id = kwargs.get("member_id")
        org_key = request.data.get("key")
        if not org_key:
            raise ValidationError(detail={"key": ["This field is required"]})
        # Retrieve member that accepted
        try:
            member = team.team_members.get(id=member_id, status=PM_MEMBER_STATUS_ACCEPTED)
        except TeamMember.DoesNotExist:
            raise NotFound
        member.email = None
        member.key = org_key
        member.status = PM_MEMBER_STATUS_CONFIRMED
        member.save()
        return Response(status=200, data={"success": True})

    @action(methods=["get"], detail=False)
    def public_key(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        team = self.get_object()
        member_id = kwargs.get("member_id")
        try:
            member = team.team_members.get(id=member_id)
        except TeamMember.DoesNotExist:
            raise NotFound
        public_key = member.user.public_key
        return Response(status=200, data={"public_key": public_key})
