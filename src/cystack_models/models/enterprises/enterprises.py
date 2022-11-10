from django.db import models

from cystack_models.models.events.events import Event
from shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from shared.constants.event import EVENT_E_MEMBER_CONFIRMED, EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_REMOVED, \
    EVENT_E_MEMBER_DISABLED
from shared.utils.app import now, random_n_digit


class Enterprise(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=128, default="My Enterprise")
    description = models.CharField(max_length=255, blank=True, default="")
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    locked = models.BooleanField(default=False)
    enterprise_name = models.CharField(max_length=128, blank=True, default="")
    enterprise_address1 = models.CharField(max_length=255, blank=True, default="")
    enterprise_address2 = models.CharField(max_length=255, blank=True, default="")
    enterprise_phone = models.CharField(max_length=128, blank=True, default="")
    enterprise_country = models.CharField(max_length=128, blank=True, default="")
    enterprise_postal_code = models.CharField(max_length=16, blank=True, default="")

    # Init members seats
    init_seats = models.IntegerField(null=True, default=None)
    init_seats_expired_time = models.FloatField(null=True, default=None)

    class Meta:
        db_table = 'e_enterprises'

    @classmethod
    def create(cls, **data):
        name = data.get("name")
        description = data.get("description", "")
        creation_date = data.get("creation_date", now())
        enterprise_id = data.get("id")
        if not enterprise_id:
            # Create new team id
            while True:
                enterprise_id = random_n_digit(n=6)
                if cls.objects.filter(id=enterprise_id).exists() is False:
                    break
        new_enterprise = cls(
            id=enterprise_id, name=name, description=description, creation_date=creation_date,
            enterprise_name=name,
            enterprise_address1=data.get("enterprise_address1") or "",
            enterprise_address2=data.get("enterprise_address2") or "",
            enterprise_phone=data.get("enterprise_phone") or "",
            enterprise_country=data.get("enterprise_country") or "",
            enterprise_postal_code=data.get("enterprise_postal_code") or ""
        )
        new_enterprise.save()

        # Create team members
        members = data.get("members", [])
        new_enterprise.enterprise_members.model.create_multiple(new_enterprise, *members)

        return new_enterprise

    def lock_enterprise(self, lock: bool):
        self.locked = lock
        if lock is True:
            self.init_seats = None
            self.init_seats_expired_time = None
        self.save()

    def get_activated_members_count(self):
        return self.enterprise_members.filter(
            status=E_MEMBER_STATUS_CONFIRMED, is_activated=True
        ).count()

    def get_primary_admin(self):
        return self.enterprise_members.get(is_primary=True)

    def get_primary_admin_user(self):
        return self.enterprise_members.get(is_primary=True).user

    def is_billing_members_added(self, member_user_id, from_param=None, to_param=None):
        if from_param is None or to_param is None:
            primary_admin_user = self.get_primary_admin_user()
            user_plan = primary_admin_user.pm_user_plan
            from_param = user_plan.start_period if user_plan.start_period else self.creation_date
            to_param = user_plan.end_period if user_plan.end_period else now()
        if Event.objects.filter(
            team_id=self.id, type__in=[EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_CONFIRMED],
            user_id=member_user_id, creation_date__range=(from_param, to_param)
        ).exists() is False:
            return True
        return False

    def is_billing_members_removed(self, member_user_id):
        primary_admin_user = self.get_primary_admin_user()
        user_plan = primary_admin_user.pm_user_plan
        from_param = user_plan.start_period if user_plan.start_period else self.creation_date
        to_param = user_plan.end_period if user_plan.end_period else now()
        if Event.objects.filter(
            team_id=self.id, type__in=[EVENT_E_MEMBER_DISABLED, EVENT_E_MEMBER_REMOVED],
            user_id=member_user_id, creation_date__range=(from_param, to_param)
        ).exists() is False:
            return True
        return False
