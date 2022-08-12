from datetime import timedelta, datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, When, Q, Case, IntegerField, Count, CharField, Max
from django.db.models.expressions import RawSQL
from django.db.models.functions import Concat
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.users.users import User
from cystack_models.models.events.events import Event
from shared.constants.ciphers import CIPHER_TYPE_LOGIN
from shared.constants.enterprise_members import *
from shared.constants.event import EVENT_USER_LOGIN_FAILED, EVENT_USER_LOGIN, EVENT_USER_BLOCK_LOGIN
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.enterprise.enterprise_permission import EnterprisePwdPermission
from shared.utils.app import now
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import ListEnterpriseSerializer, UpdateEnterpriseSerializer


class EnterprisePwdViewSet(EnterpriseViewSet):
    permission_classes = (EnterprisePwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            self.serializer_class = ListEnterpriseSerializer
        elif self.action in ["update"]:
            self.serializer_class = UpdateEnterpriseSerializer

        return super(EnterprisePwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
        except ObjectDoesNotExist:
            raise NotFound
        self.check_object_permissions(request=self.request, obj=enterprise)
        if self.action in ["update", "dashboard"]:
            if enterprise.locked:
                raise ValidationError({"non_field_errors": [gen_error("3003")]})
        return enterprise

    def get_queryset(self):
        order_whens = [
            When(Q(enterprise_members__is_default=True), then=Value(1))
        ]
        user = self.request.user
        enterprises = Enterprise.objects.filter(
            enterprise_members__user=user, enterprise_members__status=E_MEMBER_STATUS_CONFIRMED
        ).annotate(
            is_default=Case(*order_whens, output_field=IntegerField(), default=Value(0))
        ).order_by('-is_default', '-creation_date')
        return enterprises

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        if paging_param == "0":
            self.pagination_class = None
        return super(EnterprisePwdViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super(EnterprisePwdViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        enterprise = self.get_object()
        # TODO: Log update activity here

        return super(EnterprisePwdViewSet, self).update(request, *args, **kwargs)

    @action(methods=["get"], detail=True)
    def dashboard(self, request, *args, **kwargs):
        enterprise = self.get_object()
        from_param = self.check_int_param(self.request.query_params.get("from", now() - 7 * 86400))
        to_param = self.check_int_param(self.request.query_params.get("to", now()))

        # Member statistic
        members = enterprise.enterprise_members.all()
        members_status_count = members.values('status').annotate(count=Count('status'))
        members_status_statistic = {
            E_MEMBER_STATUS_CONFIRMED: 0,
            E_MEMBER_STATUS_REQUESTED: 0,
            E_MEMBER_STATUS_INVITED: 0,
        }
        for mem in members_status_count:
            members_status_statistic.update({mem["status"]: mem["count"]})
        members_activated_count = members.filter(status=E_MEMBER_STATUS_CONFIRMED, is_activated=True).count()

        # Master Password statistic
        weak_master_password_count = members.filter(
            status=E_MEMBER_STATUS_CONFIRMED, user__master_password_score__lte=1
        ).count()

        # Cipher Password statistic
        confirmed_user_ids = members.filter(status=E_MEMBER_STATUS_CONFIRMED).values_list('user_id', flat=True)
        weak_cipher_password_count = User.objects.filter(user_id__in=list(confirmed_user_ids)).annotate(
            weak_ciphers=Count(
                Case(
                    When(Q(ciphers__score__lte=1, ciphers__type=CIPHER_TYPE_LOGIN), then=Value(1)),
                    output_field=IntegerField()
                )
            )
        ).values('user_id', 'weak_ciphers').filter(weak_ciphers__gte=10).count()
        leaked_account_count = User.objects.filter(is_leaked=True, user_id__in=list(confirmed_user_ids)).count()

        # Failed login
        failed_login_events = Event.objects.filter(
            type=EVENT_USER_BLOCK_LOGIN, team_id=enterprise.id, user_id__in=confirmed_user_ids
        ).values('user_id').annotate(blocked_time=Max('creation_date')).order_by('-blocked_time')[:5]

        blocking_login = User.objects.filter(user_id__in=list(confirmed_user_ids)).exclude(
            login_block_until__isnull=True
        ).filter(login_block_until__gt=now()).count()

        # Un-verified domain
        unverified_domain_count = enterprise.domains.filter(verification=False).count()

        return Response(status=200, data={
            "members": {
                "total": members.count(),
                "status": members_status_statistic,
                "billing_members": members_activated_count,
            },
            "login_statistic": self._statistic_login_by_time(
                enterprise_id=enterprise.id, user_ids=confirmed_user_ids, from_param=from_param, to_param=to_param
            ),
            "password_security": {
                "weak_master_password": weak_master_password_count,
                "weak_password": weak_cipher_password_count,
                "leaked_account": leaked_account_count
            },
            "block_failed_login": list(failed_login_events),
            "blocking_login": blocking_login,
            "unverified_domain": unverified_domain_count
        })

    def _statistic_login_by_time(self, enterprise_id, user_ids, from_param, to_param):
        start_date = datetime.fromtimestamp(from_param)
        end_date = datetime.fromtimestamp(to_param)
        durations_list = []
        for i in range((end_date - start_date).days + 1):
            date = start_date + timedelta(days=i)
            d = "{}-{:02}-{:02}".format(date.year, date.month, date.day)
            durations_list.append(d)

        data = dict()
        for d in sorted(set(durations_list), reverse=True):
            data[d] = 0
        duration_query = "CONCAT(YEAR(FROM_UNIXTIME(creation_date)), '-', " \
                         "LPAD(MONTH(FROM_UNIXTIME(creation_date)), 2, '0'), '-', " \
                         "LPAD(DAY(FROM_UNIXTIME(creation_date)), 2, '0') )"
        events = Event.objects.filter(
            type__in=[EVENT_USER_LOGIN_FAILED, EVENT_USER_LOGIN],
            creation_date__gte=from_param, creation_date__lte=to_param,
            team_id=enterprise_id, user_id__in=user_ids
        ).annotate(
            duration=RawSQL(duration_query, [], output_field=CharField())
        ).values('duration').annotate(
            count=Count(Concat('duration', 'user_id'), distinct=True)
        )
        for event in events:
            duration_string = event.get("duration")
            duration_count = event.get("count")
            if duration_string:
                data.update({duration_string: duration_count})

        return data
