from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from django.db.models import Q, CharField, Count
from django.db.models.expressions import RawSQL
from django.db.models.functions import Concat

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_user_model, get_enterprise_domain_model, \
    get_enterprise_member_model, get_enterprise_group_member_model, get_enterprise_model, get_event_model, \
    get_enterprise_group_model
from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.event.event import Event
from locker_server.core.entities.user.user import User
from locker_server.core.repositories.enterprise_member_repository import EnterpriseMemberRepository
from locker_server.core.repositories.enterprise_repository import EnterpriseRepository
from locker_server.core.repositories.event_repository import EventRepository
from locker_server.shared.constants.enterprise_members import E_MEMBER_ROLE_MEMBER, E_MEMBER_STATUS_CONFIRMED, \
    E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN
from locker_server.shared.constants.event import *
from locker_server.shared.constants.members import PM_MEMBER_STATUS_INVITED
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.utils.app import now
from locker_server.shared.utils.network import extract_root_domain

EventORM = get_event_model()
EnterpriseMemberORM = get_enterprise_member_model()
EnterpriseGroupORM = get_enterprise_group_model()
ModelParser = get_model_parser()


class EventORMRepository(EventRepository):
    # ------------------------ List Enterprise resource ------------------- #
    def list_events(self, **filters) -> List[Event]:
        team_id_param = filters.get("team_id")
        to_param = filters.get("to") or now()
        from_param = filters.get("from") or now() - 30 * 86400
        admin_only_param = filters.get("admin_only", "0")
        member_only_param = filters.get("member_only", "0")
        group_param = filters.get("group")
        member_ids_param = filters.get("member_ids")
        acting_member_ids_param = filters.get("acting_member_ids")
        member_user_ids_param = filters.get("member_user_ids")
        action_param = filters.get("action")
        types_param = filters.get("types")
        user_id_param = filters.get("user_id")

        if team_id_param:
            events_orm = EventORM.objects.filter(team_id=team_id_param).order_by("-creation_date").filter(
                creation_date__lte=to_param, creation_date__gte=from_param
            )
        else:
            events_orm = EventORM.objects.filter(
                creation_date__lte=to_param, creation_date__gte=from_param
            ).order_by("-creation_date")
        if admin_only_param == "1":
            admin_user_ids = list(EnterpriseMemberORM.objects.filter(
                enterprise_id=team_id_param, role_id__in=[E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN]
            ).values_list('user_id', flat=True))
            events_orm = events_orm.filter(
                Q(acting_user_id__in=admin_user_ids) | Q(user_id__in=admin_user_ids)
            ).distinct()
        if member_only_param == "1":
            member_user_ids = list(EnterpriseMemberORM.objects.filter(
                enterprise_id=team_id_param, role_id__in=[E_MEMBER_ROLE_MEMBER]
            ).values_list('user_id', flat=True))
            events_orm = events_orm.filter(
                Q(acting_user_id__in=member_user_ids) | Q(user_id__in=member_user_ids)
            ).distinct()
        if member_ids_param:
            if isinstance(member_ids_param, str):
                member_ids_param = member_ids_param.split(",")
            member_user_ids = list(EnterpriseMemberORM.objects.filter(
                enterprise_id=team_id_param, id__in=member_ids_param
            ).values_list('user_id', flat=True))
            events_orm = events_orm.filter(
                Q(acting_user_id__in=member_user_ids) | Q(user_id__in=member_user_ids)
            ).distinct()
        if acting_member_ids_param:
            if isinstance(acting_member_ids_param, str):
                acting_member_ids_param = acting_member_ids_param.split(",")
            member_user_ids = list(EnterpriseMemberORM.objects.filter(
                enterprise_id=team_id_param, id__in=acting_member_ids_param
            ).values_list('user_id', flat=True))
            events_orm = events_orm.filter(acting_user_id__in=member_user_ids).distinct()
        if group_param:
            member_user_ids = list(EnterpriseGroupORM.objects.filter(
                enterprise_id=team_id_param
            ).values_list('groups_members__member__user_id', flat=True))
            events_orm = events_orm.filter(
                Q(acting_user_id__in=member_user_ids) | Q(user_id__in=member_user_ids)
            ).distinct()
        if member_user_ids_param:
            if isinstance(member_user_ids_param, str):
                member_user_ids_param = member_user_ids_param.split(",")
            events_orm = events_orm.filter(
                Q(acting_user_id__in=member_user_ids_param) | Q(user_id__in=member_user_ids_param)
            ).distinct()
        if action_param:
            if action_param == "member_changes":
                events_orm = events_orm.filter(
                    type__in=[
                        EVENT_E_MEMBER_INVITED, EVENT_E_MEMBER_CONFIRMED, EVENT_E_MEMBER_REMOVED,
                        EVENT_E_MEMBER_UPDATED_GROUP, EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_DISABLED
                    ]
                )
            elif action_param == "role_changes":
                events_orm = events_orm.filter(
                    type__in=[EVENT_E_MEMBER_UPDATED_ROLE]
                )
            elif action_param == "policy_violations":
                events_orm = events_orm.filter(type__in=[EVENT_USER_BLOCK_LOGIN])
            elif action_param == "user_login":
                events_orm = events_orm.filter(
                    type__in=[EVENT_USER_LOGIN, EVENT_USER_LOGIN_FAILED]
                )
            elif action_param == "member_billing_changes":
                events_orm = events_orm.filter(
                    type__in=[
                        EVENT_E_MEMBER_CONFIRMED, EVENT_E_MEMBER_REMOVED, EVENT_E_MEMBER_ENABLED,
                        EVENT_E_MEMBER_DISABLED
                    ]
                )
            elif action_param == "share":
                events_orm = events_orm.filter(type__in=[EVENT_ITEM_SHARE_CREATED, EVENT_ITEM_QUICK_SHARE_CREATED])
        if team_id_param:
            events_orm = events_orm.filter(team_id=team_id_param)
        if types_param:
            events_orm = events_orm.filter(type__in=types_param)
        if user_id_param:
            events_orm = events_orm.filter(user_id=user_id_param)
        return [
            ModelParser.event_parser().parse_event(event_orm=event_orm) for event_orm in events_orm
        ]

    def statistic_login_by_time(self, team_id: str, user_ids: List[int], from_param: float, to_param: float) -> Dict:
        duration_query = "CONCAT(YEAR(FROM_UNIXTIME(creation_date)), '-', " \
                         "LPAD(MONTH(FROM_UNIXTIME(creation_date)), 2, '0'), '-', " \
                         "LPAD(DAY(FROM_UNIXTIME(creation_date)), 2, '0') )"
        events_orm = EventORM.objects.filter(
            type__in=[EVENT_USER_LOGIN_FAILED, EVENT_USER_LOGIN],
            creation_date__gte=from_param, creation_date__lte=to_param,
            team_id=team_id, user_id__in=user_ids
        ).annotate(
            duration=RawSQL(duration_query, [], output_field=CharField())
        ).values('duration').annotate(
            count=Count(Concat('duration', 'user_id'), distinct=True)
        )
        data = {}
        for event_orm in events_orm:
            duration_string = event_orm.get("duration")
            duration_count = event_orm.get("count")
            if duration_string:
                data.update({duration_string: duration_count})
        return data

    # ------------------------ Get Enterprise resource --------------------- #

    # ------------------------ Create Enterprise resource --------------------- #
    def create_new_event(self, **data) -> Event:
        event_orm = EventORM.create(**data)
        return ModelParser.event_parser().parse_event(event_orm=event_orm)

    def create_new_event_by_multiple_teams(self, team_ids: list, **data):
        return EventORM.create_multiple_by_team_ids(team_ids, **data)

    def create_new_event_by_ciphers(self, ciphers, **data):
        return EventORM.create_multiple_by_ciphers(ciphers, **data)

    def create_multiple_by_enterprise_members(self, member_events_data):
        return EventORM.create_multiple_by_enterprise_members(member_events_data)

    # ------------------------ Update Enterprise resource --------------------- #

    # ------------------------ Delete Enterprise resource --------------------- #
    def delete_old_events(self, creation_date_pivot: float):
        EventORM.objects.filter(creation_date__lte=creation_date_pivot).delete()
