import random

from django.core.management import BaseCommand

from cystack_models.models import *
from locker_statistic.models.user_statistics import UserStatistic
from shared.utils.app import datetime_from_ts, now


class Command(BaseCommand):
    def handle(self, *args, **options):
        users = User.objects.filter(user_id__in=[801, 802])
        user_statistic_dicts = {}
        for user in users:
            deleted_account = False
            user_statistic_data = {
                "user_id": user.user_id,
                "country": random.choice(["VN", "EN"]),
                "verified": True,
                "created_master_password": user.activated,
                "cs_created_date": datetime_from_ts(now()),
                "lk_created_date": datetime_from_ts(user.creation_date),
                "use_web_app": random.choice([True, False]),
                "use_android": random.choice([True, False]),
                "use_ios": random.choice([True, False]),
                "use_extension": random.choice([True, False]),
                "use_desktop": random.choice([True, False]),
                "total_items": random.randrange(2, 20),
                "num_password_items": random.randrange(2, 20),
                "num_note_items": random.randrange(2, 20),
                "num_card_items": random.randrange(2, 20),
                "num_identity_items": random.randrange(2, 20),
                "num_crypto_backup_items": random.randrange(2, 20),
                "num_totp_items": random.randrange(2, 20),
                "num_private_emails": random.randrange(2, 20),
                "deleted_account": deleted_account,
                "lk_plan": random.choice(["Free", "Premium"]),
                "utm_source": None,
                "paid_money": random.randrange(2, 20)
            }
            user_statistic_dict_data = user_statistic_data.copy()
            user_statistic_dict_data.pop('user_id', None)
            user_statistic_dicts.update({user.user_id: user_statistic_dict_data})

        print(user_statistic_dicts)
        UserStatistic.bulk_update_or_create(
            common_keys={},
            unique_key_name='user_id',
            unique_key_to_defaults=user_statistic_dicts
        )
