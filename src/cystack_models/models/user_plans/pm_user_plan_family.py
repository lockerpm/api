import stripe

from django.db import models

from shared.utils.app import now
from cystack_models.models.user_plans.pm_user_plan import PMUserPlan
from cystack_models.models.users.users import User


class PMUserPlanFamily(models.Model):
    created_time = models.IntegerField()
    email = models.CharField(max_length=128, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pm_plan_family")
    root_user_plan = models.ForeignKey(PMUserPlan, on_delete=models.CASCADE, related_name="pm_plan_family")

    class Meta:
        db_table = 'cs_pm_user_plan_family'

    @classmethod
    def create_multiple_by_email(cls, root_user_plan: PMUserPlan, *emails):
        pm_user_plan_family = []
        for email in emails:
            pm_user_plan_family.append(
                cls(email=email, user=None, root_user_plan=root_user_plan, created_time=now())
            )
        cls.objects.bulk_create(pm_user_plan_family, ignore_conflicts=True)
