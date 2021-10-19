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
    SYNC_EVENT_CIPHER_UPDATE, SYNC_EVENT_MEMBER_INVITATION, SYNC_EVENT_CIPHER, SYNC_EVENT_VAULT
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
                    team=team, user=member_user, role_id=role, status=PM_MEMBER_STATUS_INVITED,
                    collection_ids=member_collections
                )
                PwdSync(event=SYNC_EVENT_MEMBER_INVITATION, user_ids=[member_obj.user_id]).send()
                added_members.append(member_obj.user_id)

        result = {
            "team_id": team.id,
            "team_name": team.name,
            "members": added_members
        }
        return Response(status=200, data=result)

    def update(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        user = self.request.user
        team = self.get_object()
        member_id = kwargs.get("member_id")
        try:
            member_obj = team.team_members.get(id=member_id)
        except TeamMember.DoesNotExist:
            raise NotFound
        role = request.data.get("role")
        collections = request.data.get("collections")

        team_collection_ids = list(team.collections.values_list('id', flat=True))
        valid_collection_ids = [collection_id for collection_id in collections if collection_id in team_collection_ids]
        # Validate data
        if role not in [MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER]:
            raise ValidationError(detail={"role": ["Role is not valid"]})
        # Not allow edit yourself and Not allow edit primary owner
        if member_obj.user == user or member_obj.is_primary is True:
            return Response(status=403)

        # Update role and collections
        member_collections = [] if role in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN] else valid_collection_ids
        self.team_member_repository.update_member(member=member_obj, role_id=role, collection_ids=member_collections)
        # Sync data for updated member
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[member_obj.user_id]).send()
        return Response(status=200, data={"success": True})

    def destroy(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        team = self.get_object()
        member_id = kwargs.get("member_id")
        user = self.request.user
        try:
            member = team.team_members.get(id=member_id)
        except TeamMember.DoesNotExist:
            raise NotFound
        deleted_member_user_id = member.user_id
        # Not allow delete themselves
        if member.user == user or member.role.name == MEMBER_ROLE_OWNER:
            return Response(status=403)
        member_user_id = member.user_id
        member.delete()
        # Sync data of member
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[member_user_id]).send()
        # Return response data to API Gateway to send mail
        return Response(status=200, data={
            "team_id": team.id,
            "team_name": team.name,
            "member_user_id": deleted_member_user_id
        })

    @action(methods=["post"], detail=False)
    def invitation_member(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        team = self.get_object()
        added_members = []
        members = request.data.get("members", [])
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
                # If this invitation exists => pass
                team.team_members.get(email=member["email"])
            except TeamMember.DoesNotExist:
                # Create new email invitation
                collections = member.get("collections", [])
                valid_collections = [collection_id for collection_id in collections if collection_id in collection_ids]
                role = member["role"]
                member_collections = [] if role in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN] else valid_collections
                member_obj = team.team_members.model.create_with_collections(
                    team=team, role_id=role, status=PM_MEMBER_STATUS_INVITED, email=member["email"],
                    collection_ids=member_collections
                )
                token = self.team_member_repository.create_invitation_token(member=member_obj)
                added_members.append({
                    "team_id": team.id,
                    "team_name": team.name,
                    "token": token,
                    "email": member_obj.email
                })
        return Response(status=200, data=added_members)

    @action(methods=["post"], detail=False)
    def revoke_invitation(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        team = self.get_object()
        email = request.data.get("email")
        try:
            invitation = TeamMember.objects.get(team=team, email=email)
            invitation.delete()
            return Response(status=200, data={"success": True})
        except TeamMember.DoesNotExist:
            raise NotFound

    @action(methods=["post"], detail=False)
    def reinvite(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        team = self.get_object()
        try:
            member = TeamMember.objects.get(team=team, id=kwargs.get("member_id"), status=PM_MEMBER_STATUS_INVITED)
        except TeamMember.DoesNotExist:
            raise NotFound
        # Re-invite this member
        return Response(status=200, data={"user_id": member.user_id, "email": member.email})

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
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[member.user_id]).send()
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

    @action(methods=["get"], detail=False)
    def invitation_confirmation(self, request, *args, **kwargs):
        email = self.request.query_params.get("email", None)
        user_id = self.request.query_params.get("user_id", None)
        if (email is None) or (user_id is None):
            raise NotFound
        member_user = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
        # Filter invitations of the teams
        invitations = TeamMember.objects.filter(email=email, team__key__isnull=False, status=PM_MEMBER_STATUS_INVITED)
        team_ids = invitations.values_list('team_id', flat=True)

        for invitation in invitations:
            team = invitation.team
            # Check max number members
            current_total_members = team.team_members.all().count()
            primary_user = self.team_repository.get_primary_member(team=team).user
            max_allow_members = self.user_repository.get_current_plan(
                user=primary_user, scope=settings.SCOPE_PWD_MANAGER
            ).get_max_allow_members()
            if max_allow_members and current_total_members + 1 > max_allow_members:
                continue

            invitation.email = None
            invitation.token_invitation = None
            invitation.user = member_user
            invitation.save()

        return Response(status=200, data={"success": True, "team_ids": list(team_ids)})

    @action(methods=["get", "put"], detail=False)
    def group(self, request, *args, **kwargs):
        pass
