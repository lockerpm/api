import requests
from django.conf import settings
from django.db import connection

from locker_server.shared.external_services.fcm.constants import FCM_TYPE_CONFIRM_SHARE_GROUP_MEMBER_ADDED
from locker_server.shared.external_services.fcm.fcm_request_entity import FCMRequestEntity
from locker_server.shared.external_services.fcm.fcm_sender import FCMSenderService
from locker_server.shared.external_services.locker_background.background import LockerBackground
from locker_server.shared.external_services.locker_background.impl import NotifyBackground
from locker_server.shared.external_services.requester.retry_requester import requester
from locker_server.shared.external_services.user_notification.list_jobs import PWD_CONFIRM_SHARE_GROUP_MEMBER_ADDED
from locker_server.shared.external_services.user_notification.notification_sender import NotificationSender, \
    SENDING_SERVICE_WEB_NOTIFICATION


class EnterpriseGroupBackground(LockerBackground):
    def add_group_member_to_share(self, enterprise_group, new_member_ids):
        from locker_server.containers.containers import sharing_service, user_service, device_service

        try:
            confirmed_data = sharing_service.add_group_member_to_share(
                enterprise_group=enterprise_group, new_member_ids=new_member_ids
            )
            for confirm_data in confirmed_data:
                existed_member_users = confirm_data.get("existed_member_users")

                if settings.SELF_HOSTED:
                    emails = user_service.list_user_emails(user_ids=existed_member_users)
                else:
                    url = "{}/micro_services/users".format(settings.GATEWAY_API)
                    headers = {'Authorization': settings.MICRO_SERVICE_USER_AUTH}
                    data_send = {"ids": existed_member_users, "emails": []}
                    emails = []
                    try:
                        res = requester(method="POST", url=url, headers=headers, data_send=data_send, timeout=15)
                        if res.status_code == 200:
                            users_from_id_data = res.json()
                            emails = [u.get("email") for u in users_from_id_data]
                    except (requests.exceptions.RequestException, requests.exceptions.ConnectTimeout):
                        pass
                # Sending mobile notification
                if emails:
                    fcm_ids = device_service.list_fcm_ids(user_ids=[confirm_data.get("owner")])
                    fcm_message = FCMRequestEntity(
                        fcm_ids=fcm_ids, priority="high",
                        data={
                            "event": FCM_TYPE_CONFIRM_SHARE_GROUP_MEMBER_ADDED,
                            "data": {
                                "share_type": confirm_data.get("shared_type_name"),
                                "group_id": confirm_data.get("group_id"),
                                "group_name": confirm_data.get("group_name"),
                                "owner_name": confirm_data.get("name"),
                                "emails": emails
                            }
                        }
                    )
                    FCMSenderService(is_background=False).run("send_message", **{"fcm_message": fcm_message})

            if settings.SELF_HOSTED:
                for team in confirmed_data:
                    team_id = team.get("id")
                    group_id = team.get("group_id")
                    group_name = team.get("group_name")
                    existed_member_users = team.get("existed_member_users", [])
                    owner_user_id = team.get("owner")
                    new_member_emails = user_service.list_user_emails(user_ids=existed_member_users)
                    self._notify_confirmed_members(owner_user_id, team_id, new_member_emails, group_id, group_name)
            else:
                NotifyBackground(background=False).notify_add_group_member_to_share(data={"teams": confirmed_data})

        except Exception as e:
            self.log_error(func_name="add_group_member_to_share")
        finally:
            if self.background:
                connection.close()

    @staticmethod
    def _notify_confirmed_members(user_ids, sharing_id, new_member_emails, group_id, group_name):
        if not new_member_emails:
            return
        user_ids = [user_ids] if not isinstance(user_ids, list) else user_ids
        NotificationSender(
            job=PWD_CONFIRM_SHARE_GROUP_MEMBER_ADDED, scope=settings.SCOPE_PWD_MANAGER,
            services=[SENDING_SERVICE_WEB_NOTIFICATION]
        ).send(**{
            "user_ids": user_ids,
            "emails": new_member_emails,
            "sharing_id": sharing_id,
            "group_id": group_id,
            "group_name": group_name,
        })
