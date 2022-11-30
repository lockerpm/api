from django.db import models


class UserStatisticDate(models.Model):
    id = models.AutoField(primary_key=True)
    created_time = models.FloatField()
    completed_time = models.FloatField()
    latest_user_id = models.IntegerField(null=True)

    class Meta:
        db_table = 'lk_user_statistics_date'
