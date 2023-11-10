from typing import Dict, Optional, List
from django.db.models import Count

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_enterprise_group_model, get_team_member_model
from locker_server.core.entities.enterprise.group.group import EnterpriseGroup
from locker_server.core.repositories.enterprise_group_repository import EnterpriseGroupRepository
from locker_server.shared.constants.members import MEMBER_ROLE_OWNER
from locker_server.shared.utils.app import now

EnterpriseGroupORM = get_enterprise_group_model()
TeamMemberORM = get_team_member_model()
ModelParser = get_model_parser()


class EnterpriseGroupORMRepository(EnterpriseGroupRepository):
    # ------------------------ List EnterpriseGroup resource ------------------- #
    def list_active_user_enterprise_group_ids(self, user_id: int) -> List[str]:
        return list(
            EnterpriseGroupORM.objects.filter(
                enterprise__locked=False,
                enterprise__enterprise_members__user_id=user_id,
                enterprise__enterprise_members__is_activated=True
            ).values_list('id', flat=True)
        )

    def list_enterprise_groups(self, **filters) -> List[EnterpriseGroup]:
        enterprise_id_param = filters.get("enterprise_id")
        name_param = filters.get("name")
        user_id_param = filters.get("user_id")

        if enterprise_id_param:
            enterprise_groups_orm = EnterpriseGroupORM.objects.filter(
                enterprise_id=enterprise_id_param
            ).order_by("creation_date").select_related("created_by").select_related("enterprise")
        else:
            enterprise_groups_orm = EnterpriseGroupORM.objects.all().order_by(
                "creation_date"
            ).select_related("created_by").select_related("enterprise")

        if name_param:
            enterprise_groups_orm = enterprise_groups_orm.filter(
                name__icontains=name_param.lower()
            )

        if user_id_param:
            enterprise_groups_orm = enterprise_groups_orm.filter(
                groups_members__member__user_id=user_id_param
            )
        return [
            ModelParser.enterprise_parser().parse_enterprise_group(enterprise_group_orm=enterprise_group_orm)
            for enterprise_group_orm in enterprise_groups_orm
        ]

    # ------------------------ Get EnterpriseGroup resource --------------------- #
    def get_by_id(self, enterprise_group_id: str) -> Optional[EnterpriseGroup]:
        try:
            enterprise_group_orm = EnterpriseGroupORM.objects.get(id=enterprise_group_id)
        except EnterpriseGroupORM.DoesNotExist:
            return None
        return ModelParser.enterprise_parser().parse_enterprise_group(enterprise_group_orm=enterprise_group_orm)

    # ------------------------ Create EnterpriseGroup resource --------------------- #
    def create_enterprise_group(self, enterprise_group_create_data: Dict) -> EnterpriseGroup:
        enterprise_group_orm = EnterpriseGroupORM.create(**enterprise_group_create_data)
        return ModelParser.enterprise_parser().parse_enterprise_group(enterprise_group_orm=enterprise_group_orm)

    # ------------------------ Update EnterpriseGroup resource --------------------- #
    def update_enterprise_group(self, enterprise_group_id: str, enterprise_group_update_data: Dict) \
            -> Optional[EnterpriseGroup]:
        try:
            enterprise_group_orm = EnterpriseGroupORM.objects.get(
                id=enterprise_group_id
            )
        except EnterpriseGroupORM.DoesNotExist:
            return None
        enterprise_group_orm.name = enterprise_group_update_data.get("name", enterprise_group_orm.name)
        enterprise_group_orm.revision_date = enterprise_group_update_data.get("revision_date", now())
        enterprise_group_orm.save()
        return ModelParser.enterprise_parser().parse_enterprise_group(
            enterprise_group_orm=enterprise_group_orm
        )

    # ------------------------ Delete EnterpriseGroup resource --------------------- #
    def delete_enterprise_group_by_id(self, enterprise_group_id: str) -> bool:
        try:
            enterprise_group_orm = EnterpriseGroupORM.objects.get(id=enterprise_group_id)
        except EnterpriseGroupORM.DoesNotExist:
            return False

        sharing_group_members = enterprise_group_orm.sharing_groups.values_list('groups_members__member_id', flat=True)
        team_members_orm = TeamMemberORM.objects.filter(
            id__in=list(sharing_group_members), is_added_by_group=True
        ).exclude(role_id=MEMBER_ROLE_OWNER).annotate(
            group_count=Count('groups_members')
        )
        # Filter list members have only one group. Then delete them
        team_members_orm.filter(group_count=1).delete()

        #  Filter list members have other groups => Set role_id by other groups
        more_one_groups_orm = team_members_orm.filter(group_count__gt=1)
        for m in more_one_groups_orm:
            first_group_orm = m.groups_members.select_related('group').exclude(
                group__enterprise_group_id=enterprise_group_orm.id
            ).order_by('group_id').first()
            if first_group_orm:
                m.role_id = first_group_orm.group.role_id
                m.save()

        # Delete this group objects
        enterprise_group_orm.delete()
        return True
