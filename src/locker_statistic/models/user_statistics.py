from django.db import models

from shared.constants.transactions import PLAN_TYPE_PM_FREE


class UserStatistic(models.Model):
    user_id = models.IntegerField(primary_key=True)
    country = models.CharField(max_length=32)
    verified = models.BooleanField(default=True)
    created_master_password = models.BooleanField(default=False)
    cs_created_date = models.DateTimeField()
    lk_created_date = models.DateTimeField(null=True)
    # Used platforms?
    use_web_app = models.BooleanField(default=False)
    use_android = models.BooleanField(default=False)
    use_ios = models.BooleanField(default=False)
    use_extension = models.BooleanField(default=False)
    use_desktop = models.BooleanField(default=False)
    # Item statistics
    total_items = models.IntegerField(default=0)
    num_password_items = models.IntegerField(default=0)
    num_note_items = models.IntegerField(default=0)
    num_card_items = models.IntegerField(default=0)
    num_identity_items = models.IntegerField(default=0)
    num_crypto_backup_items = models.IntegerField(default=0)
    num_totp_items = models.IntegerField(default=0)
    # Private email
    num_private_emails = models.IntegerField(default=0)

    deleted_account = models.BooleanField(default=False)
    lk_plan = models.CharField(max_length=64, default=PLAN_TYPE_PM_FREE)
    utm_source = models.CharField(max_length=64, blank=True, null=True, default=None)
    paid_money = models.FloatField(default=0)

    class Meta:
        db_table = 'lk_user_statistics'
