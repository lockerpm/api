from typing import Dict, Optional, List

from django.conf import settings
from django.db.models import When, Value, Q, Case, IntegerField

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_user_model, get_enterprise_domain_model, \
    get_enterprise_member_model, get_enterprise_group_member_model
from locker_server.core.entities.enterprise.member.enterprise_member import EnterpriseMember
from locker_server.core.entities.user.user import User
from locker_server.core.repositories.enterprise_member_repository import EnterpriseMemberRepository
from locker_server.shared.constants.enterprise_members import E_MEMBER_ROLE_MEMBER, E_MEMBER_STATUS_REQUESTED, \
    E_MEMBER_STATUS_INVITED, E_MEMBER_STATUS_CONFIRMED, E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN
from locker_server.shared.constants.members import PM_MEMBER_STATUS_INVITED
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.utils.app import now
from locker_server.shared.utils.network import extract_root_domain

UserORM = get_user_model()
DomainORM = get_enterprise_domain_model()
EnterpriseMemberORM = get_enterprise_member_model()
EnterpriseGroupMemberORM = get_enterprise_group_member_model()
ModelParser = get_model_parser()


class EnterpriseMemberORMRepository(EnterpriseMemberRepository):
    @staticmethod
    def _get_user_orm(user_id: int) -> Optional[UserORM]:
        try:
            return UserORM.objects.get(user_id=user_id)
        except UserORM.DoesNotExist:
            return None

    # ------------------------ List EnterpriseMember resource ------------------- #
    def list_enterprise_members(self, **filters) -> List[EnterpriseMember]:
        enterprise_id_param = filters.get("enterprise_id")
        domain_id_param = filters.get("domain_id")
        ids_param = filters.get("ids")
        user_id_param = filters.get("user_id")
        user_ids_param = filters.get("user_ids")
        email_param = filters.get("email")
        q_param = filters.get("q")
        roles_param = filters.get("roles")
        status_param = filters.get("status")
        statuses_param = filters.get("statuses")
        is_activated_param = filters.get("is_activated")
        block_login_param = filters.get("block_login")
        sort_param = filters.get("sort")

        if enterprise_id_param:

            enterprise_members_orm = EnterpriseMemberORM.objects.filter(
                enterprise_id=enterprise_id_param
            ).select_related('user').select_related('role').select_related('domain')
        else:
            enterprise_members_orm = EnterpriseMemberORM.objects.all().select_related(
                'user'
            ).select_related('role').select_related('domain')
        # Filter by ids
        if ids_param:
            enterprise_members_orm = enterprise_members_orm.filter(id__in=ids_param)
        if domain_id_param:
            enterprise_members_orm = enterprise_members_orm.filter(domain_id=domain_id_param)

        # Filter by roles
        if roles_param:
            enterprise_members_orm = enterprise_members_orm.filter(role_id__in=roles_param)

        # Filter by q_param: search members
        if user_ids_param is not None or email_param is not None or user_id_param is not None:
            search_by_user = enterprise_members_orm.none()
            search_by_users = enterprise_members_orm.none()
            search_by_email = enterprise_members_orm.none()
            if user_id_param is not None:
                try:
                    user_id_int_param = int(user_id_param)
                    search_by_user = enterprise_members_orm.filter(user_id=user_id_int_param)
                except AttributeError:
                    pass
            if user_ids_param is not None:
                try:
                    user_ids_int_param = [int(user_id) for user_id in user_ids_param]
                    search_by_users = enterprise_members_orm.filter(user_id__in=user_ids_int_param)
                except AttributeError:
                    pass
            if email_param is not None:
                search_by_email = enterprise_members_orm.filter(email__icontains=email_param)
            enterprise_members_orm = (search_by_users | search_by_email | search_by_user).distinct()

        if q_param and settings.SELF_HOSTED:
            q = q_param.lower()
            enterprise_members_orm = enterprise_members_orm.filter(
                Q(user__full_name__icontains=q) | Q(user__email__icontains=q) | Q(email__icontains=q)
            )

        # Filter by status
        if status_param:
            enterprise_members_orm = enterprise_members_orm.filter(status=status_param)

        # Filter by statuses
        if statuses_param:
            enterprise_members_orm = enterprise_members_orm.filter(status__in=statuses_param)

        # Filter by activated or not
        if is_activated_param is not None:
            if is_activated_param == "0":
                enterprise_members_orm = enterprise_members_orm.filter(is_activated=False)
            elif is_activated_param == "1":
                enterprise_members_orm = enterprise_members_orm.filter(is_activated=True)

        # Filter by blocking login or not
        if block_login_param == "1":
            enterprise_members_orm = enterprise_members_orm.filter(user__login_block_until__isnull=False).filter(
                user__login_block_until__gt=now()
            )

        # Sorting the results
        order_whens = [
            When(Q(role__name=E_MEMBER_ROLE_PRIMARY_ADMIN, user__isnull=False), then=Value(2)),
            When(Q(role__name=E_MEMBER_ROLE_ADMIN, user__isnull=False), then=Value(3)),
            When(Q(role__name=E_MEMBER_ROLE_MEMBER, user__isnull=False), then=Value(4))
        ]
        if sort_param:
            if sort_param == "access_time_desc":
                enterprise_members_orm = enterprise_members_orm.order_by('-access_time')
            elif sort_param == "access_time_asc":
                enterprise_members_orm = enterprise_members_orm.order_by('access_time')
            elif sort_param == "role_desc":
                enterprise_members_orm = enterprise_members_orm.annotate(
                    order_field=Case(*order_whens, output_field=IntegerField(), default=Value(4))
                ).order_by("-order_field")
            elif sort_param == "role_asc":
                enterprise_members_orm = enterprise_members_orm.annotate(
                    order_field=Case(*order_whens, output_field=IntegerField(), default=Value(4))
                ).order_by("order_field")
        return [
            ModelParser.enterprise_parser().parse_enterprise_member(
                enterprise_member_orm=enterprise_member_orm
            )
            for enterprise_member_orm in enterprise_members_orm
        ]

    def list_enterprise_member_user_id_by_roles(self, enterprise_id: str, role_ids: List[str]) -> List[str]:
        user_ids = EnterpriseMemberORM.objects.filter(
            enterprise_id=enterprise_id,
            role_id__in=role_ids
        ).values_list('user_id', flat=True)
        return list(user_ids)

    def list_enterprise_member_user_id_by_members(self, enterprise_id: str, member_ids: List[str]) -> List[str]:
        user_ids = EnterpriseMemberORM.objects.filter(
            enterprise_id=enterprise_id,
            id__in=member_ids
        ).values_list('user_id', flat=True)
        return list(user_ids)

    def list_enterprise_member_user_ids(self, **filter_params) -> List[int]:
        enterprise_id_param = filter_params.get("enterprise_id")
        user_ids_params = filter_params.get("user_ids")
        if enterprise_id_param:
            members_orm = EnterpriseMemberORM.objects.filter(enterprise_id=enterprise_id_param)
            if user_ids_params is not None:
                members_orm = members_orm.filter(user_id__in=user_ids_params)
        else:
            if user_ids_params is not None:
                members_orm = EnterpriseMemberORM.objects.filter(user_id__in=user_ids_params)
            else:
                members_orm = EnterpriseMemberORM.objects.all()
        return list(members_orm.values_list('user_id', flat=True))

    def list_enterprise_members_by_emails(self, emails_param: [str]) -> List[EnterpriseMember]:
        enterprise_members_orm = EnterpriseMemberORM.objects.filter(
            email__in=emails_param
        ).select_related('user').select_related('role').select_related('domain')
        return [
            ModelParser.enterprise_parser().parse_enterprise_member(
                enterprise_member_orm=enterprise_member_orm
            )
            for enterprise_member_orm in enterprise_members_orm
        ]

    def count_enterprise_members(self, **filters) -> int:
        enterprise_id_param = filters.get("enterprise_id")
        status_param = filters.get("status")
        is_activated_param = filters.get("is_activated")

        if enterprise_id_param:
            enterprises_orm = EnterpriseMemberORM.objects.filter(
                enterprise_id=enterprise_id_param
            )
        else:
            enterprises_orm = EnterpriseMemberORM.objects.all()
        if status_param:
            enterprises_orm = enterprises_orm.filter(status=status_param)
        if is_activated_param is not None:
            if is_activated_param == "1" or is_activated_param is True:
                enterprises_orm = enterprises_orm.filter(is_activated=True)
            elif is_activated_param == "0" or is_activated_param is False:
                enterprises_orm = enterprises_orm.filter(is_activated=False)

        return enterprises_orm.count()

    # ------------------------ Get EnterpriseMember resource --------------------- #
    def get_primary_member(self, enterprise_id: str) -> Optional[EnterpriseMember]:
        try:
            enterprise_member_orm = EnterpriseMemberORM.objects.get(
                enterprise_id=enterprise_id, is_primary=True
            )
        except EnterpriseMemberORM.DoesNotExist:
            return None
        return ModelParser.enterprise_parser().parse_enterprise_member(enterprise_member_orm=enterprise_member_orm)

    def get_enterprise_member_by_id(self, member_id: str) -> Optional[EnterpriseMember]:
        try:
            enterprise_member_orm = EnterpriseMemberORM.objects.get(
                id=member_id
            )
        except EnterpriseMemberORM.DoesNotExist:
            return None
        return ModelParser.enterprise_parser().parse_enterprise_member(enterprise_member_orm=enterprise_member_orm)

    def get_enterprise_member_by_user_id(self, enterprise_id: str, user_id: int) -> Optional[EnterpriseMember]:
        try:
            enterprise_member_orm = EnterpriseMemberORM.objects.get(
                enterprise_id=enterprise_id, user_id=user_id
            )
            return ModelParser.enterprise_parser().parse_enterprise_member(enterprise_member_orm=enterprise_member_orm)
        except EnterpriseMemberORM.DoesNotExist:
            return None

    def get_enterprise_member_by_token(self, token: str) -> Optional[EnterpriseMember]:
        try:
            enterprise_member_orm = EnterpriseMemberORM.objects.get(
                token_invitation=token
            )
            return ModelParser.enterprise_parser().parse_enterprise_member(enterprise_member_orm=enterprise_member_orm)
        except EnterpriseMemberORM.DoesNotExist:
            return None

    def lock_login_account_belong_enterprise(self, user_id: int) -> bool:
        return EnterpriseMemberORM.objects.filter(
            user_id=user_id, status__in=[E_MEMBER_STATUS_REQUESTED, E_MEMBER_STATUS_INVITED], domain__isnull=False
        ).exists()

    def is_active_enterprise_member(self, user_id: int) -> bool:
        return EnterpriseMemberORM.objects.filter(
            user_id=user_id, status=E_MEMBER_STATUS_CONFIRMED, is_activated=True, enterprise__locked=False
        )

    def is_in_enterprise(self, user_id: int, enterprise_locked: bool = None) -> bool:
        if enterprise_locked is not None:
            return EnterpriseMemberORM.objects.filter(user_id=user_id, enterprise__locked=enterprise_locked).exists()
        return EnterpriseMemberORM.objects.filter(user_id=user_id).exists()

    # ------------------------ Create EnterpriseMember resource --------------------- #
    def create_member(self, member_create_data: Dict) -> EnterpriseMember:
        enterprise_member_orm = EnterpriseMemberORM.create_member(**member_create_data)
        return ModelParser.enterprise_parser().parse_enterprise_member(
            enterprise_member_orm=enterprise_member_orm
        )

    def create_multiple_member(self, members_create_data: [Dict]) -> int:
        return EnterpriseMemberORM.create_multiple_member(members_create_data)

    # ------------------------ Update EnterpriseMember resource --------------------- #
    def enterprise_invitations_confirm(self, user: User, email: str = None) -> Optional[User]:
        user_orm = self._get_user_orm(user_id=user.user_id)
        if not user_orm:
            return
        if not email:
            email = user_orm.get_from_cystack_id().get("email")
        if not email:
            return user
        # Add this user into the Enterprise if the mail domain belongs to an Enterprise
        belong_enterprise_domain = False
        try:
            email_domain = email.split("@")[1]
            root_domain = extract_root_domain(domain=email_domain)
            domain_orm = DomainORM.objects.filter(root_domain=root_domain, verification=True).first()
            if domain_orm:
                belong_enterprise_domain = True
                EnterpriseMemberORM.retrieve_or_create_by_user(
                    enterprise=domain_orm.enterprise, user=user_orm, role_id=E_MEMBER_ROLE_MEMBER,
                    **{"domain": domain_orm}
                )
                # Cancel all other invitations
                EnterpriseMemberORM.objects.filter(email=email, status=PM_MEMBER_STATUS_INVITED).delete()
        except (ValueError, IndexError, AttributeError):
            CyLog.warning(**{"message": f"[enterprise_invitations_confirm] Can not get email: {user_orm} {email}"})
            pass
        # Update existed invitations
        if belong_enterprise_domain is False:
            enterprise_invitations = EnterpriseMemberORM.objects.filter(email=email, status=PM_MEMBER_STATUS_INVITED)
            enterprise_invitations.update(email=None, token_invitation=None, user=user_orm)
        return user

    def enterprise_share_groups_confirm(self, user: User) -> Optional[User]:
        from locker_server.shared.external_services.locker_background.constants import BG_ENTERPRISE_GROUP
        from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory

        enterprise_groups_orm = EnterpriseGroupMemberORM.objects.filter(
            member__user_id=user.user_id
        ).select_related('group')
        for enterprise_group_orm in enterprise_groups_orm:
            BackgroundFactory.get_background(bg_name=BG_ENTERPRISE_GROUP).run(
                func_name="add_group_member_to_share", **{
                    "enterprise_group": ModelParser.enterprise_parser().parse_enterprise_group(
                        enterprise_group_orm=enterprise_group_orm.group
                    ),
                    "new_member_ids": [user.user_id]
                }
            )
        return user

    def update_enterprise_member(self, enterprise_member_id: str, enterprise_member_update_data: Dict) \
            -> Optional[EnterpriseMember]:
        try:
            enterprise_member_orm = EnterpriseMemberORM.objects.get(id=enterprise_member_id)
        except EnterpriseMemberORM.DoesNotExist:
            return None
        enterprise_member_orm.role_id = enterprise_member_update_data.get("role", enterprise_member_orm.role_id)
        enterprise_member_orm.status = enterprise_member_update_data.get("status", enterprise_member_orm.status)
        enterprise_member_orm.is_activated = enterprise_member_update_data.get(
            "is_activated",
            enterprise_member_orm.is_activated
        )
        enterprise_member_orm.is_primary = enterprise_member_update_data.get(
            "is_primary",
            enterprise_member_orm.is_primary
        )
        enterprise_member_orm.access_time = enterprise_member_update_data.get(
            "access_time",
            enterprise_member_orm.access_time
        )
        enterprise_member_orm.email = enterprise_member_update_data.get("email", enterprise_member_orm.email)
        enterprise_member_orm.user_id = enterprise_member_update_data.get("user_id", enterprise_member_orm.user_id)
        enterprise_member_orm.token_invitation = enterprise_member_update_data.get(
            "token_invitation",
            enterprise_member_orm.token_invitation
        )

        enterprise_member_orm.save()
        return ModelParser.enterprise_parser().parse_enterprise_member(enterprise_member_orm=enterprise_member_orm)

    def update_batch_enterprise_members(self, enterprise_member_ids: List[str], **enterprise_member_update_data):
        EnterpriseMemberORM.objects.filter(id__in=enterprise_member_ids).update(
            **enterprise_member_update_data
        )

    def update_batch_enterprise_members_by_user_ids(self, user_ids: List[str], **enterprise_member_update_data):
        return EnterpriseMemberORM.objects.filter(user__in=user_ids).update(
            **enterprise_member_update_data
        )

    # ------------------------ Delete EnterpriseMember resource --------------------- #
    def delete_enterprise_member(self, enterprise_member_id: str) -> bool:
        try:
            enterprise_member_orm = EnterpriseMemberORM.objects.get(id=enterprise_member_id)
        except EnterpriseMemberORM.DoesNotExist:
            return False
        enterprise_member_orm.delete()
        return True
