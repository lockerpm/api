from django.db import models, transaction

from shared.constants.transactions import PLAN_TYPE_PM_FREE


class UserStatistic(models.Model):
    user_id = models.IntegerField(primary_key=True)
    country = models.CharField(max_length=32, null=True)
    verified = models.BooleanField(default=True)
    created_master_password = models.BooleanField(default=False)
    cs_created_date = models.DateTimeField(null=True)
    lk_created_date = models.DateTimeField(null=True)
    lk_last_login = models.DateTimeField(null=True)
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
    num_crypto_account_items = models.IntegerField(default=0)
    num_driver_license_items = models.IntegerField(default=0)
    num_citizen_id_items = models.IntegerField(default=0)
    num_passport_items = models.IntegerField(default=0)
    num_social_security_number_items = models.IntegerField(default=0)
    num_wireless_router = models.IntegerField(default=0)
    num_server_items = models.IntegerField(default=0)
    num_api_items = models.IntegerField(default=0)
    num_database_items = models.IntegerField(default=0)
    # Private email
    num_private_emails = models.IntegerField(default=0)

    deleted_account = models.BooleanField(default=False)
    lk_plan = models.CharField(max_length=64, default=PLAN_TYPE_PM_FREE)
    utm_source = models.CharField(max_length=128, blank=True, null=True, default=None)
    paid_money = models.FloatField(default=0)
    first_payment_date = models.DateTimeField(null=True)
    paid_platforms = models.CharField(max_length=128, blank=True, null=True, default=None)
    lk_referral_count = models.IntegerField(default=0)
    personal_trial_mobile_applied = models.BooleanField(default=False)
    personal_trial_web_applied = models.BooleanField(default=False)

    class Meta:
        db_table = 'lk_user_statistics'

    @classmethod
    def bulk_update_or_create(cls, common_keys, unique_key_name, unique_key_to_defaults,
                              batch_size=None, ignore_conflicts=False):
        """
        Source: https://stackoverflow.com/questions/27047630/django-batching-bulk-update-or-create
        ex. Event.bulk_update_or_create(
            {"organization": organization}, "external_id", {1234: {"started": True}}
        )
        :param common_keys: {field_name: field_value}
        :param unique_key_name: field_name
        :param unique_key_to_defaults: {field_value: {field_name: field_value}}
        :param batch_size:
        :param ignore_conflicts:
        :return:
        """

        with transaction.atomic(using="locker_statistics_db"):
            filter_kwargs = dict(common_keys)
            filter_kwargs[f"{unique_key_name}__in"] = unique_key_to_defaults.keys()
            existing_objs = {
                getattr(obj, unique_key_name): obj
                for obj in cls.objects.filter(**filter_kwargs).select_for_update()
            }

            create_data = {
                k: v for k, v in unique_key_to_defaults.items() if k not in existing_objs
            }
            for unique_key_value, obj in create_data.items():
                obj[unique_key_name] = unique_key_value
                obj.update(common_keys)
            creates = [cls(**obj_data) for obj_data in create_data.values()]
            if creates:
                cls.objects.bulk_create(creates, batch_size=batch_size, ignore_conflicts=ignore_conflicts)

            # This set should contain the name of the `auto_now` field of the model
            update_fields = set()
            updates = []
            for key, obj in existing_objs.items():
                obj.update(unique_key_to_defaults[key], save=False)
                update_fields.update(unique_key_to_defaults[key].keys())
                updates.append(obj)
            if existing_objs:
                cls.objects.bulk_update(updates, update_fields)
        return creates, updates

    def update(self, update_dict=None, save=True, **kwargs):
        """ Helper method to update objects """
        if not update_dict:
            update_dict = kwargs
        # This set should contain the name of the `auto_now` field of the model
        update_fields = set()
        for k, v in update_dict.items():
            setattr(self, k, v)
            update_fields.add(k)
        if save:
            self.save(update_fields=update_fields)
