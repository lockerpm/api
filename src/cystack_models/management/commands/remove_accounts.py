import json

import humps
import requests
from django.conf import settings

from django.core.management import BaseCommand

from core.settings import CORE_CONFIG
from cystack_models.models import *
from shared.constants.transactions import PLAN_TYPE_PM_FREE
from shared.external_request.requester import requester


class Command(BaseCommand):
    def handle(self, *args, **options):
        # user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        # users = User.objects.filter(user_id__in=[6960])
        # for user in users:
        #     primary_team = user_repository.get_default_team(user=user)
        #     if primary_team:
        #         primary_team.delete()
        # Cipher.objects.filter(user__in=users).delete()
        # users.delete()
        print("Start")
        users = User.objects.all().order_by('-user_id')
        print("Users: ", users.count())
        user_ids = users.values_list('user_id', flat=True)
        error_request_user_ids = []
        for user_id in user_ids:
            url = "{}/micro_services/users/{}".format(settings.GATEWAY_API, user_id)
            headers = {'Authorization': settings.MICRO_SERVICE_USER_AUTH}
            try:
                res = requester(method="GET", url=url, headers=headers)
            except:
                error_request_user_ids.append(user_id)
                print("Exception: ", user_id)
                continue
            if res.status_code == 404:
                user = User.objects.get(user_id=user_id)
                print("Delete user_id: ", user_id)
                # print(res.status_code, res.text)
                self.delete_user(user=user)
            else:
                print("OK: ", user_id)
        print("Requests errors: ", error_request_user_ids)

    def delete_user(self, user):
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        primary_team = user_repository.get_default_team(user=user)
        if primary_team:
            primary_team.delete()
        Cipher.objects.filter(user_id__in=[user.user_id]).delete()
        user.delete()

    def remove_plan(self):
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()

        scope = settings.SCOPE_PWD_MANAGER
        user = User.objects.get(user_id=802)
        payment_data = {}
        current_plan = user_repository.get_current_plan(user=user, scope=scope)
        old_plan = current_plan.get_plan_type_name()
        current_plan.cancel_mobile_subscription()

        # if this plan is canceled because the user is added into family plan => Not notify
        if not current_plan.user.pm_plan_family.exists():
            user_repository.update_plan(
                user=user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=scope
            )
            # Notify downgrade here
            # LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=True).run(
            #     func_name="downgrade_plan", **{
            #         "user_id": user.user_id, "old_plan": old_plan, "downgrade_time": now(),
            #         "scope": settings.SCOPE_PWD_MANAGER, **{"payment_data": payment_data}
            #     }
            # )
