from django.conf import settings
from django.db.models import Value, When, Q, Case, IntegerField
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError


from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.enterprises.members.enterprise_members import EnterpriseMember
from shared.constants.enterprise_members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.enterprise.member_permission import MemberPwdPermission
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import DetailMemberSerializer, UpdateMemberSerializer


class MemberPwdViewSet(EnterpriseViewSet):
    permission_classes = (MemberPwdPermission, )
    lookup_value_regex = r'[0-9a-z\-]+'
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = DetailMemberSerializer
        elif self.action == "update":
            self.serializer_class = UpdateMemberSerializer
        return super(MemberPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=enterprise)
            if self.action in ["create", "update"]:
                if enterprise.locked:
                    raise ValidationError({"non_field_errors": [gen_error("3003")]})
            return enterprise
        except Enterprise.DoesNotExist:
            raise NotFound

    def get_enterprise_member(self, enterprise: Enterprise, member_id):
        try:
            member_obj = enterprise.enterprise_members.get(id=member_id)
            return member_obj
        except EnterpriseMember.DoesNotExist:
            raise NotFound

    def get_queryset(self):
        enterprise = self.get_object()
        # Param to find member by user id
        user_ids_param = self.request.query_params.get("user_ids", None)
        email_param = self.request.query_params.get("email", None)

        # Get list role to filter
        list_filter_roles = []

        # Get all members of the enterprise
        members_qs = enterprise.enterprise_members.filter()
        # Filter list role
        if list_filter_roles:
            members_qs = members_qs.filter(role__name__in=list_filter_roles)
        # filter by q_param: search members
        if user_ids_param:
            try:
                user_ids_param = list(map(int, user_ids_param.split(",")))
                members_qs = members_qs.filter(user_id__in=user_ids_param).distinct()
            except AttributeError:
                pass
        if email_param:
            members_qs = members_qs.filter(email__icontains=email_param)

        # `whens` query to order list members (primary_admin => admin => member)
        order_whens = [
            When(Q(role__name=E_MEMBER_ROLE_PRIMARY_ADMIN, user__isnull=False), then=Value(2)),
            When(Q(role__name=E_MEMBER_ROLE_PRIMARY_ADMIN, user__isnull=False), then=Value(3)),
            When(Q(role__name=E_MEMBER_ROLE_MEMBER, user__isnull=False), then=Value(4))
        ]
        # Order by `order_whens`
        members_qs = members_qs.annotate(
            order_field=Case(*order_whens, output_field=IntegerField(), default=Value(4))
        ).order_by("order_field")

        return members_qs

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10

        return super(MemberPwdViewSet, self).list(request, *args, **kwargs)

    @action(methods=["post"], detail=False)
    def create_multiple(self, request, *args, **kwargs):
        ip = request.data.get("ip")
        members = request.data.get("members")
        if not isinstance(members, list):
            raise ValidationError(detail={"members": ["Members are not valid. This field must be an array"]})

        user = self.request.user
        enterprise = self.get_object()
        added_members = []

        # TODO: Check the maximum number of members
        current_total_members = enterprise.enterprise_members.all().count()
        primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        max_allow_members = self.user_repository.get_current_plan(
            user=primary_admin, scope=settings.SCOPE_PWD_MANAGER
        ).get_max_allow_members()
        if max_allow_members and current_total_members + len(members) > max_allow_members:
            raise ValidationError({"non_field_errors": [gen_error("3002")]})

        # Loop list members data
        for member in members:
            try:
                enterprise.enterprise_members.get(user_id=member["user_id"])
            except EnterpriseMember.DoesNotExist:
                role = member["role"]
                member_user = self.user_repository.retrieve_or_create_by_id(user_id=member["user_id"])
                member_obj = enterprise.enterprise_members.model.create(
                    enterprise, role_id=role, user=member_user, status=E_MEMBER_STATUS_INVITED
                )

                # TODO: Log activity create new members

                added_members.append(member_obj.user_id)

        return Response(status=200, data={
            "enterprise_id": enterprise.id,
            "enterprise_name": enterprise.name,
            "members": added_members
        })

    @action(methods=["post"], detail=False)
    def invitation_multiple(self, request, *args, **kwargs):
        """
        Create members obj for non-exist users
        """
        ip = request.data.get("ip")
        user = self.request.user
        members = request.data.get("members", [])
        if not isinstance(members, list):
            raise ValidationError(detail={"members": ["Members are not valid. This field must be an array"]})
        enterprise = self.get_object()
        added_members = []

        # TODO: Check the maximum number of members
        current_total_members = enterprise.enterprise_members.all().count()
        primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        max_allow_members = self.user_repository.get_current_plan(
            user=primary_admin, scope=settings.SCOPE_PWD_MANAGER
        ).get_max_allow_members()
        if max_allow_members and current_total_members + len(members) > max_allow_members:
            raise ValidationError({"non_field_errors": [gen_error("3002")]})

        # Loop list members data
        for member in members:
            try:
                enterprise.enterprise_members.get(email=member["email"])
            except EnterpriseMember.DoesNotExist:
                role = member["role"]
                member_obj = enterprise.enterprise_members.model.create(
                    enterprise, role_id=role, email=member["email"], status=E_MEMBER_STATUS_INVITED
                )
                token = member_obj.create_invitation_token()
                added_members.append({
                    "enterprise_id": enterprise.id,
                    "enterprise_name": enterprise.name,
                    "token": token,
                    "email": member_obj.email
                })

                # TODO: Log activity create new members

        return Response(status=200, data=added_members)

    def update(self, request, *args, **kwargs):
        ip = request.data.get("ip")
        user = self.request.user
        enterprise = self.get_object()
        member_id = kwargs.get("member_id")
        member_obj = self.get_enterprise_member(enterprise=enterprise, member_id=member_id)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        role = validated_data.get("role")

        # Not allow edit yourself and Not allow edit primary owner
        if member_obj.user == user or member_obj.is_primary is True:
            return Response(status=403)

        member_obj.role_id = role
        member_obj.save()

        # TODO: Log activity update role of the member HERE

        return Response(status=200, data={"success": True})

    def destroy(self, request, *args, **kwargs):
        ip = request.data.get("ip")
        user = self.request.user
        enterprise = self.get_object()
        member_obj = self.get_enterprise_member(enterprise=enterprise, member_id=kwargs.get("member_id"))
        member_user = member_obj.user
        deleted_member_user_id = member_obj.user_id
        # Not allow delete themselves
        if member_obj.user == user or member_obj.role.name == E_MEMBER_ROLE_PRIMARY_ADMIN:
            return Response(status=403)
        member_obj.delete()

        # TODO: Log activity delete member here

        return Response(status=200, data={
            "enterprise_id": enterprise.id,
            "enterprise_": enterprise.name,
            "member_user_id": deleted_member_user_id
        })

    @action(methods=["get"], detail=False)
    def invitation_confirmation(self, request, *args, **kwargs):
        email = self.request.query_params.get("email")
        user_id = self.request.query_params.get("user_id")
        if not email or not user_id:
            raise NotFound
        member_user = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
        # Filter invitations of the teams
        invitations = EnterpriseMember.objects.filter(email=email, status=E_MEMBER_STATUS_INVITED)
        enterprise_ids = invitations.values_list('enterprise_id', flat=True)

        for invitation in invitations:
            enterprise = invitation.enterprise
            # TODO: Check the maximum number of members
            current_total_members = enterprise.enterprise_members.all().count()
            primary_admin = enterprise.enterprise_members.get(is_primary=True).user
            max_allow_members = self.user_repository.get_current_plan(
                user=primary_admin, scope=settings.SCOPE_PWD_MANAGER
            ).get_max_allow_members()
            if max_allow_members and current_total_members + 1 > max_allow_members:
                continue

            invitation.email = None
            invitation.user = member_user
            invitation.token_invitation = None
            invitation.save()

        return Response(status=200, data={"enterprise_ids": list(enterprise_ids)})
