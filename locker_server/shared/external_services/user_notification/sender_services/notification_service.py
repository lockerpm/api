from locker_server.containers.containers import notification_service
from locker_server.shared.external_services.user_notification.list_jobs import *
from locker_server.shared.external_services.user_notification.sender_services import SenderService


class NotificationService(SenderService):
    def send(self, **kwargs):
        notification = self._config["sender"].get("web")
        kwargs["notification"] = notification
        user_ids = kwargs.get("user_ids", [])
        notification = kwargs.get("notification")
        kwargs = self.__get_web_notification_kwargs(**kwargs)

        notification_service.create_multiple(
            user_ids=user_ids,
            notification_type=notification["type"],
            vi_title=notification["title"]["vi"].format(**kwargs),
            en_title=notification["title"]["en"].format(**kwargs),
            metadata=self.__get_web_notification_metadata(**kwargs),
        )

    @staticmethod
    def __get_web_notification_kwargs(**kwargs):
        job = kwargs.get("job")
        if job == PWD_NEW_SHARE_ITEM:
            shared_type_name = kwargs.get("cipher_type")
            if not shared_type_name:
                kwargs["cipher_type"] = "item"
            else:
                map_share_type = {
                    "1": "password",
                    "2": "note",
                    "3": "card",
                    "4": "identity",
                    "5": "totp",
                    "6": "crypto account",
                    "7": "crypto wallet"
                }
                kwargs["cipher_type"] = map_share_type.get(str(shared_type_name)) or shared_type_name

        elif job == PWD_CONFIRM_SHARE_GROUP_MEMBER_ADDED:
            number_new_members = len(kwargs.get("emails", []))
            kwargs["member_joined_text_vi"] = f"{number_new_members} thành viên vừa tham gia"
            if number_new_members > 1:
                kwargs["member_joined_text_en"] = f"{number_new_members} members have joined"
            else:
                kwargs["member_joined_text_en"] = f"{number_new_members} member has joined"
        return kwargs

    @staticmethod
    def __get_web_notification_metadata(**kwargs):
        job = kwargs.get("job")
        if job in [PWD_JOIN_EMERGENCY_ACCESS, PWD_CONFIRM_EMERGENCY_ACCESS,
                   PWD_ACCEPT_INVITATION_EMERGENCY_ACCESS, PWD_DECLINED_INVITATION_EMERGENCY_ACCESS,
                   PWD_EMERGENCY_ACCESS_GRANTED,
                   PWD_NEW_EMERGENCY_ACCESS_REQUEST,
                   PWD_EMERGENCY_REQUEST_ACCEPTED, PWD_EMERGENCY_REQUEST_DECLINED]:
            return {
                "is_grantor": kwargs.get("is_grantor", False),
                "is_grantee": kwargs.get("is_grantee", False)
            }
        elif job in [PWD_CONFIRM_SHARE_GROUP_MEMBER_ADDED]:
            return {
                "sharing_id": kwargs.get("sharing_id"),
                "emails": kwargs.get("emails", []),
                "group_id": kwargs.get("group_id"),
                "group_name": kwargs.get("group_name"),
                "clicked": False
            }
        return {}
