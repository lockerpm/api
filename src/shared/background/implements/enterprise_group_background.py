import requests
from django.conf import settings
from django.db import connection
from django.core.exceptions import ObjectDoesNotExist

from core.settings import CORE_CONFIG
from cystack_models.models.notifications.notification_settings import NotificationSetting
from shared.background.i_background import ILockerBackground
from shared.background.implements import NotifyBackground
from shared.constants.members import PM_MEMBER_STATUS_CONFIRMED
from shared.constants.user_notification import NOTIFY_SHARING
from shared.external_request.requester import requester, RequesterError
from shared.services.fcm.constants import FCM_TYPE_NEW_SHARE_GROUP_MEMBER, FCM_TYPE_NEW_SHARE, \
    FCM_TYPE_CONFIRM_SHARE_GROUP_MEMBER_ADDED
from shared.services.fcm.fcm_request_entity import FCMRequestEntity
from shared.services.fcm.fcm_sender import FCMSenderService


class EnterpriseGroupBackground(ILockerBackground):
    sharing_repository = CORE_CONFIG["repositories"]["ISharingRepository"]()
    device_repository = CORE_CONFIG["repositories"]["IDeviceRepository"]()
    team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()

    def add_group_member_to_share(self, enterprise_group, new_member_ids):
        try:
            enterprise_group_member_user_ids = enterprise_group.groups_members.filter(
                member_id__in=new_member_ids
            ).values_list('member__user_id', flat=True)
            sharing_groups = enterprise_group.sharing_groups.select_related('team').prefetch_related('groups_members')
            members = [{"user_id": user_id, "key": None} for user_id in enterprise_group_member_user_ids]

            confirmed_data = []
            for sharing_group in sharing_groups:
                team = sharing_group.team
                try:
                    owner_user = self.team_repository.get_primary_member(team=team).user
                except ObjectDoesNotExist:
                    continue

                # confirmed_members_user_ids = list(team.team_members.filter(
                #     status=PM_MEMBER_STATUS_CONFIRMED
                # ).values_list('user_id', flat=True))
                collection = team.collections.first()
                groups = [{
                    "id": sharing_group.enterprise_group_id,
                    "role": sharing_group.role_id,
                    "members": members
                }]
                existed_member_users, non_existed_member_users = self.sharing_repository.add_group_members(
                    team=team, shared_collection=collection, groups=groups
                )
                if collection:
                    shared_type_name = "folder"
                else:
                    cipher_obj = team.ciphers.first()
                    shared_type_name = cipher_obj.type if cipher_obj else None

                # # Sending notification to group members
                # mail_user_ids = NotificationSetting.get_user_mail(
                #     category_id=NOTIFY_SHARING, user_ids=existed_member_users
                # )
                # notification_user_ids = NotificationSetting.get_user_notification(
                #     category_id=NOTIFY_SHARING, user_ids=existed_member_users
                # )

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
                    fcm_ids = self.device_repository.get_fcm_ids_by_user_ids(user_ids=[owner_user.user_id])
                    fcm_message = FCMRequestEntity(
                        fcm_ids=fcm_ids, priority="high",
                        data={
                            "event": FCM_TYPE_CONFIRM_SHARE_GROUP_MEMBER_ADDED,
                            "data": {
                                "share_type": shared_type_name,
                                "group_id": sharing_group.enterprise_group_id,
                                "group_name": sharing_group.name,
                                "owner_name": team.name,
                                "emails": emails
                            }
                        }
                    )
                    FCMSenderService(is_background=False).run("send_message", **{"fcm_message": fcm_message})

                # TODO: Notification here
                confirmed_data.append({
                    "id": team.id,
                    "name": team.name,
                    "owner": owner_user.user_id,
                    "group_id": sharing_group.enterprise_group_id,
                    "group_name": sharing_group.name,
                    "shared_type_name": shared_type_name,
                    "existed_member_users": existed_member_users,
                    "non_existed_member_users": non_existed_member_users,
                })

            NotifyBackground(background=False).notify_add_group_member_to_share(data={"teams": confirmed_data})

        except Exception as e:
            self.log_error(func_name="add_group_member_to_share")
        finally:
            if self.background:
                connection.close()
