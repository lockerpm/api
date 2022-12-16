from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, When, Q, Case, IntegerField
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory, \
    PaymentMethodNotSupportException
from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.enterprises.members.enterprise_members import EnterpriseMember
from shared.background import LockerBackgroundFactory, BG_EVENT
from shared.constants.enterprise_members import *
from shared.constants.event import EVENT_E_MEMBER_CONFIRMED, EVENT_E_MEMBER_UPDATED_ROLE, EVENT_E_MEMBER_REMOVED, \
    EVENT_E_MEMBER_DISABLED, EVENT_E_MEMBER_ENABLED
from shared.constants.transactions import PAYMENT_METHOD_CARD
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.enterprise.member_permission import MemberPwdPermission
from shared.utils.app import now
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import DetailMemberSerializer, UpdateMemberSerializer, UserInvitationSerializer, \
    EnabledMemberSerializer, ShortDetailMemberSerializer, DetailActiveMemberSerializer, SearchMemberGroupSerializer, \
    EnterpriseGroupSerializer


class MemberPwdViewSet(EnterpriseViewSet):
    permission_classes = (MemberPwdPermission, )
    lookup_value_regex = r'[0-9a-z\-]+'
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            shortly_param = self.request.query_params.get("shortly", "0")
            if shortly_param == "1":
                self.serializer_class = ShortDetailMemberSerializer
            else:
                self.serializer_class = DetailMemberSerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailActiveMemberSerializer
        elif self.action == "update":
            self.serializer_class = UpdateMemberSerializer
        elif self.action == "user_invitations":
            self.serializer_class = UserInvitationSerializer
        elif self.action == "activated":
            self.serializer_class = EnabledMemberSerializer
        elif self.action == "search_members_groups":
            self.serializer_class = SearchMemberGroupSerializer
        return super(MemberPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=enterprise)
            # if self.action in ["create", "update", "create_multiple", "activated", ]:
            if self.request.method in ["POST", "PUT", "DELETE"] and enterprise.locked:
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
        filter_primary_admin_param = self.request.query_params.get("primary_admin", "0")
        filter_admin_param = self.request.query_params.get("admin", "0")
        filter_member_param = self.request.query_params.get("member", "0")
        list_filter_roles = []
        if filter_primary_admin_param == "1":
            list_filter_roles.append(E_MEMBER_ROLE_PRIMARY_ADMIN)
        if filter_admin_param == "1":
            list_filter_roles.append(E_MEMBER_ROLE_ADMIN)
        if filter_member_param == "1":
            list_filter_roles.append(E_MEMBER_ROLE_MEMBER)

        # Get all members of the enterprise
        members_qs = enterprise.enterprise_members.filter()
        # Filter list role
        if list_filter_roles:
            members_qs = members_qs.filter(role__name__in=list_filter_roles)
        # filter by q_param: search members
        if user_ids_param or email_param:
            search_by_users = enterprise.enterprise_members.none()
            search_by_email = enterprise.enterprise_members.none()
            if user_ids_param:
                try:
                    user_ids_param = list(map(int, user_ids_param.split(",")))
                    search_by_users = members_qs.filter(user_id__in=user_ids_param)
                except AttributeError:
                    pass
            if email_param:
                search_by_email = members_qs.filter(email__icontains=email_param)
            members_qs = (search_by_users | search_by_email).distinct()

        # Filter by status
        status_param = self.request.query_params.get("status")
        if status_param:
            members_qs = members_qs.filter(status=status_param)

        # Filter by multiple statuses
        statuses_param = self.request.query_params.get("statuses")
        if statuses_param:
            members_qs = members_qs.filter(status__in=statuses_param.split(","))

        # Filter by activated or not
        is_activated_param = self.request.query_params.get("is_activated")
        if is_activated_param:
            if is_activated_param == "0":
                members_qs = members_qs.filter(is_activated=False)
            elif is_activated_param == "1":
                members_qs = members_qs.filter(is_activated=True)

        # Filter by Blocking login or not
        block_login_param = self.request.query_params.get("block_login")
        if block_login_param == "1":
            members_qs = members_qs.filter(user__login_block_until__isnull=False).filter(
                user__login_block_until__gt=now()
            )

        # Sorting the results
        sort_param = self.request.query_params.get("sort", None)
        order_whens = [
            When(Q(role__name=E_MEMBER_ROLE_PRIMARY_ADMIN, user__isnull=False), then=Value(2)),
            When(Q(role__name=E_MEMBER_ROLE_ADMIN, user__isnull=False), then=Value(3)),
            When(Q(role__name=E_MEMBER_ROLE_MEMBER, user__isnull=False), then=Value(4))
        ]
        if sort_param:
            if sort_param == "access_time_desc":
                members_qs = members_qs.order_by('-access_time')
            elif sort_param == "access_time_asc":
                members_qs = members_qs.order_by('access_time')
            elif sort_param == "role_desc":
                members_qs = members_qs.annotate(
                    order_field=Case(*order_whens, output_field=IntegerField(), default=Value(4))
                ).order_by("-order_field")
            elif sort_param == "role_asc":
                members_qs = members_qs.annotate(
                    order_field=Case(*order_whens, output_field=IntegerField(), default=Value(4))
                ).order_by("order_field")
        else:
            members_qs = members_qs.order_by('-access_time')
        members_qs = members_qs.select_related('user').select_related('role')
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
        non_added_members = []

        # TODO: Check the maximum number of members
        # current_total_members = enterprise.enterprise_members.all().count()
        # primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        # max_allow_members = self.user_repository.get_current_plan(
        #     user=primary_admin, scope=settings.SCOPE_PWD_MANAGER
        # ).get_max_allow_members()
        # if max_allow_members and current_total_members + len(members) > max_allow_members:
        #     raise ValidationError({"non_field_errors": [gen_error("3002")]})

        # Loop list members data
        for member in members:
            # If this member is in other enterprise
            if EnterpriseMember.objects.filter(user_id=member["user_id"]).exists():
                non_added_members.append(member["user_id"])
                continue
            try:
                enterprise.enterprise_members.get(user_id=member["user_id"])
                non_added_members.append(member["user_id"])
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
            "members": added_members,
            "non_added_members": list(set(non_added_members))
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
        non_added_members = []

        # # TODO: Check the maximum number of members
        # current_total_members = enterprise.enterprise_members.all().count()
        # primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        # max_allow_members = self.user_repository.get_current_plan(
        #     user=primary_admin, scope=settings.SCOPE_PWD_MANAGER
        # ).get_max_allow_members()
        # if max_allow_members and current_total_members + len(members) > max_allow_members:
        #     raise ValidationError({"non_field_errors": [gen_error("3002")]})

        # Loop list members data
        for member in members:
            # If this member is in other enterprise
            if EnterpriseMember.objects.filter(email=member["email"]).exists():
                non_added_members.append(member["email"])
                continue
            try:
                enterprise.enterprise_members.get(email=member["email"])
                non_added_members.append(member["email"])
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

        return Response(status=200, data={
            "members": added_members,
            "non_added_members": non_added_members
        })

    def retrieve(self, request, *args, **kwargs):
        enterprise = self.get_object()
        member_id = kwargs.get("member_id")
        member_obj = self.get_enterprise_member(enterprise=enterprise, member_id=member_id)
        serializer = self.get_serializer(member_obj)
        return Response(status=200, data=serializer.data)

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
        status = validated_data.get("status")
        change_status = False
        change_role = False

        if role:
            # Not allow edit yourself and Not allow edit primary owner
            if member_obj.user == user or member_obj.is_primary is True:
                return Response(status=403)
            old_role = member_obj.role_id
            member_obj.role_id = role
            member_obj.save()
            change_role = True
            LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                "enterprise_ids": [enterprise.id], "acting_user_id": user.user_id,
                "user_id": member_obj.user_id, "team_member_id": member_obj.id,
                "type": EVENT_E_MEMBER_UPDATED_ROLE, "ip_address": ip,
                "metadata": {"old_role": old_role, "new_role": role}
            })

        if status and member_obj.status == E_MEMBER_STATUS_REQUESTED:
            member_obj.status = status
            member_obj.save()
            change_status = True
            # Update subscription quantity here
            if enterprise.is_billing_members_added(member_user_id=member_obj.user_id) is True:
                try:
                    PaymentMethodFactory.get_method(
                        user=enterprise.get_primary_admin_user(), scope=settings.SCOPE_PWD_MANAGER,
                        payment_method=PAYMENT_METHOD_CARD
                    ).update_quantity_subscription(amount=1)
                except (PaymentMethodNotSupportException, ObjectDoesNotExist):
                    pass

            LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                "enterprise_ids": [enterprise.id], "acting_user_id": user.user_id,
                "user_id": member_obj.user_id, "team_member_id": member_obj.id,
                "type": EVENT_E_MEMBER_CONFIRMED, "ip_address": ip
            })

        return Response(status=200, data={
            "success": True,
            "change_status": change_status,
            "change_role": change_role,
            "member_id": member_obj.id,
            "member_user_id": member_obj.user_id,
            "enterprise_name": member_obj.enterprise.name,
            "status": member_obj.status,
            "role": member_obj.role_id
        })

    def destroy(self, request, *args, **kwargs):
        ip = request.data.get("ip")
        user = self.request.user
        enterprise = self.get_object()
        member_obj = self.get_enterprise_member(enterprise=enterprise, member_id=kwargs.get("member_id"))
        deleted_member_user_id = member_obj.user_id
        deleted_member_status = member_obj.status
        # Not allow delete themselves
        if member_obj.user == user or member_obj.role.name == E_MEMBER_ROLE_PRIMARY_ADMIN:
            return Response(status=403)

        try:
            PaymentMethodFactory.get_method(
                user=enterprise.get_primary_admin_user(), scope=settings.SCOPE_PWD_MANAGER,
                payment_method=PAYMENT_METHOD_CARD
            ).update_quantity_subscription(amount=-1)
        except (PaymentMethodNotSupportException, ObjectDoesNotExist):
            pass

        # Log activity delete member here
        LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
            "enterprise_ids": [enterprise.id], "acting_user_id": user.user_id,
            "user_id": member_obj.user_id, "team_member_id": member_obj.id,
            "type": EVENT_E_MEMBER_REMOVED, "ip_address": ip,
        })
        # Delete member obj
        member_obj.delete()
        return Response(status=200, data={
            "enterprise_id": enterprise.id,
            "enterprise_name": enterprise.name,
            "member_user_id": deleted_member_user_id,
            "member_status": deleted_member_status,
        })

    @action(methods=["post"], detail=False)
    def reinvite(self, request, *args, **kwargs):
        enterprise = self.get_object()
        enterprise_member = self.get_enterprise_member(enterprise=enterprise, member_id=kwargs.get("member_id"))
        if enterprise_member.status != E_MEMBER_STATUS_INVITED or enterprise_member.domain:
            raise NotFound
        return Response(status=200, data={
            "user_id": enterprise_member.user_id,
            "email": enterprise_member.email,
            "token_invitation": enterprise_member.token_invitation,
            "enterprise_id": enterprise.id,
            "enterprise_name": enterprise.name
        })

    @action(methods=["put"], detail=False)
    def activated(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        enterprise = self.get_object()
        enterprise_member = self.get_enterprise_member(enterprise=enterprise, member_id=kwargs.get("member_id"))
        if enterprise_member.status != E_MEMBER_STATUS_CONFIRMED:
            raise NotFound
        if enterprise_member.user_id == user.user_id:
            raise PermissionDenied
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        activated = validated_data.get("activated")
        if enterprise_member.is_activated != activated:
            enterprise_member.is_activated = activated
            enterprise_member.save()
            # Remove this member from all groups
            if activated is False:
                enterprise_member.groups_members.all().delete()
            #  Update billing here - Check the user is a new activated user in billing period
            if activated is True and enterprise.is_billing_members_added(member_user_id=enterprise_member.user_id):
                try:
                    PaymentMethodFactory.get_method(
                        user=enterprise.get_primary_admin_user(), scope=settings.SCOPE_PWD_MANAGER,
                        payment_method=PAYMENT_METHOD_CARD
                    ).update_quantity_subscription(amount=1)
                except (PaymentMethodNotSupportException, ObjectDoesNotExist):
                    pass
            if activated is False and enterprise.is_billing_members_removed(member_user_id=enterprise_member.user_id):
                try:
                    PaymentMethodFactory.get_method(
                        user=enterprise.get_primary_admin_user(), scope=settings.SCOPE_PWD_MANAGER,
                        payment_method=PAYMENT_METHOD_CARD
                    ).update_quantity_subscription(amount=-1)
                except (PaymentMethodNotSupportException, ObjectDoesNotExist):
                    pass
            LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                "enterprise_ids": [enterprise.id], "acting_user_id": user.user_id,
                "user_id": enterprise_member.user_id, "team_member_id": enterprise_member.id,
                "type": EVENT_E_MEMBER_ENABLED if activated is True else EVENT_E_MEMBER_DISABLED, "ip_address": ip
            })

        return Response(status=200, data={"success": True})

    @action(methods=["put"], detail=False)
    def unblock(self, request, *args, **kwargs):
        user = self.request.user
        enterprise = self.get_object()
        enterprise_member = self.get_enterprise_member(enterprise=enterprise, member_id=kwargs.get("member_id"))
        if enterprise_member.status != E_MEMBER_STATUS_CONFIRMED:
            raise NotFound
        if enterprise_member.user_id == user.user_id:
            raise PermissionDenied
        enterprise_member.user.login_failed_attempts = 0
        enterprise_member.user.login_block_until = None
        enterprise_member.user.save()
        return Response(status=200, data={"success": True})

    @action(methods=["get"], detail=False)
    def user_invitations(self, request, *args, **kwargs):
        user = self.request.user
        member_invitations = user.enterprise_members.filter(
            status__in=[E_MEMBER_STATUS_INVITED, E_MEMBER_STATUS_REQUESTED]
        ).select_related('enterprise').order_by('access_time')
        serializer = self.get_serializer(member_invitations, many=True)
        return Response(status=200, data=serializer.data)

    @action(methods=["put"], detail=False)
    def user_invitation_update(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        status = request.data.get("status")
        if status not in ["confirmed", "reject"]:
            raise ValidationError(detail={"status": ["This status is not valid"]})
        try:
            member_invitation = user.enterprise_members.get(
                id=kwargs.get("pk"), status=E_MEMBER_STATUS_INVITED, user__activated=True
            )
        except EnterpriseMember.DoesNotExist:
            raise NotFound
        enterprise = member_invitation.enterprise
        # If the member has a domain => Not allow reject
        if member_invitation.domain:
            if status == "reject":
                raise ValidationError(detail={"status": ["You cannot reject this enterprise"]})
            if member_invitation.domain.auto_approve is True:
                member_invitation.status = E_MEMBER_STATUS_CONFIRMED
            else:
                member_invitation.status = E_MEMBER_STATUS_REQUESTED
            member_invitation.save()
        else:
            if status == "confirmed":
                member_invitation.status = E_MEMBER_STATUS_CONFIRMED
                member_invitation.save()
            else:
                member_invitation.delete()
        try:
            primary_admin_user = enterprise.get_primary_admin_user()
            primary_admin_user_id = primary_admin_user.user_id
        except EnterpriseMember.DoesNotExist:
            primary_admin_user = None
            primary_admin_user_id = None

        admin_user_ids = list(enterprise.enterprise_members.filter(
            role_id=E_MEMBER_ROLE_ADMIN, status=E_MEMBER_STATUS_CONFIRMED
        ).values_list('user_id', flat=True))

        member_status = member_invitation.status if status != "reject" else None
        if member_status == E_MEMBER_STATUS_CONFIRMED:
            # Log event
            LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                "enterprise_ids": [enterprise.id], "acting_user_id": user.user_id,
                "user_id": user.user_id, "team_member_id": member_invitation.id,
                "type": EVENT_E_MEMBER_CONFIRMED, "ip_address": ip
            })
            # Update subscription quantity here
            if enterprise.is_billing_members_added(member_user_id=user.user_id) is True and primary_admin_user:
                try:
                    PaymentMethodFactory.get_method(
                        user=primary_admin_user, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
                    ).update_quantity_subscription(amount=1)
                except PaymentMethodNotSupportException:
                    pass

        return Response(status=200, data={
            "success": True,
            "member_status": member_status,
            "primary_owner": primary_admin_user_id,
            "admin": admin_user_ids,
            "enterprise_name": enterprise.name,
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

    @action(methods=["post"], detail=False)
    def search_members_groups(self, request, *args, **kwargs):
        user = self.request.user
        enterprise = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        query = validated_data.get("query")
        user_ids = validated_data.get("user_ids") or []
        status = validated_data.get("status", E_MEMBER_STATUS_CONFIRMED)

        members = enterprise.enterprise_members.filter(status=status).filter(
            user_id__in=user_ids
        ).order_by('-access_time')[:5]
        groups = enterprise.groups.filter(name__icontains=query.lower()).order_by('-id')[:5]

        members_serializer = ShortDetailMemberSerializer(members, many=True)
        groups_serializer = EnterpriseGroupSerializer(groups, many=True)
        return Response(status=200, data={
            "members": members_serializer.data,
            "groups": groups_serializer.data
        })
