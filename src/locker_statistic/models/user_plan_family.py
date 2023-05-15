from django.db import models

from locker_statistic.models.user_statistics import UserStatistic


class UserPlanFamily(models.Model):
    created_time = models.IntegerField()
    email = models.CharField(max_length=128, null=True)
    user = models.ForeignKey(UserStatistic, on_delete=models.CASCADE, related_name="family_members", null=True)
    root_user = models.ForeignKey(UserStatistic, on_delete=models.CASCADE, related_name="family_root", null=True)

    class Meta:
        db_table = 'lk_user_plan_family'
