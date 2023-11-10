from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.utils.app import now


class PMUserPlanFamilyORM(models.Model):
    created_time = models.IntegerField()
    email = models.CharField(max_length=128, null=True)
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="pm_plan_family", null=True
    )
    root_user_plan = models.ForeignKey(
        locker_server_settings.LS_USER_PLAN_MODEL, on_delete=models.CASCADE, related_name="pm_plan_family"
    )

    class Meta:
        db_table = 'cs_pm_user_plan_family'

    @classmethod
    def create(cls, root_user_plan_id, user_id, email):
        new_pm_user_plan_family = cls(
            root_user_plan_id=root_user_plan_id, email=email, user_id=user_id, created_time=now()
        )
        new_pm_user_plan_family.save()
        return new_pm_user_plan_family

    @classmethod
    def create_multiple_by_email(cls, root_user_plan, *emails):
        pm_user_plan_family = []
        for email in emails:
            pm_user_plan_family.append(
                cls(email=email, user=None, root_user_plan=root_user_plan, created_time=now())
            )
        cls.objects.bulk_create(pm_user_plan_family, ignore_conflicts=True)
