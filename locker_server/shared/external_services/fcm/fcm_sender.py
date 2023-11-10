import json
import traceback

from django.conf import settings
from firebase_admin import messaging

from locker_server.shared.external_services.fcm.fcm_request_entity import FCMRequestEntity
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.background.i_background import BackgroundThread


class FCMSenderService:
    def __init__(self, is_background=True):
        self.is_background = is_background

    @staticmethod
    def log_error(func_name: str = "", meta="", tb=None):
        if not tb:
            tb = traceback.format_exc()
        CyLog.error(**{"message": "[Locker FCM] Function {} {} error: {}".format(func_name, meta, tb)})

    def run(self, func_name: str, **kwargs):
        # Get self-function by function name
        func = getattr(self, func_name)
        if not func:
            raise Exception("Func name {} does not exist in this background".format(func_name))
        if not callable(func):
            raise Exception("Func name {} is not callable".format(func_name))

        # Run background or not this function
        if self.is_background:
            BackgroundThread(task=func, **kwargs)
        else:
            func(**kwargs)

    def send_message(self, fcm_message) -> tuple:
        """
        Sending notification to multiple devices
        :param fcm_message:
        :return: (tuple) success_fcm_ids, failed_fcm_ids
        """
        if not settings.FCM_CRED_SERVICE_ACCOUNT:
            CyLog.warning(**{"message": "The FCM Cred is not provided"})
            return [], []
        if isinstance(fcm_message, FCMRequestEntity):
            fcm_message = fcm_message.to_json()
        fcm_ids = list(set(fcm_message.get("fcm_ids", [])))
        if not fcm_ids:
            return [], []

        fcm_message_data = fcm_message.get("data")
        if "data" in fcm_message_data:
            fcm_message_data["data"] = json.dumps(fcm_message_data["data"])

        failed_fcm_ids = []
        success_fcm_ids = fcm_ids.copy()

        batch_size = 450
        for i in range(0, len(fcm_ids), batch_size):
            batch_fcm_ids = fcm_ids[i:i+batch_size]
            message = messaging.MulticastMessage(
                data=fcm_message_data,
                tokens=batch_fcm_ids,
                android=messaging.AndroidConfig(
                    priority=fcm_message.get("priority") or "high"
                ),
                apns=messaging.APNSConfig(
                    headers={
                        'apns-push-type': 'background',
                        'apns-priority': '5',
                        'apns-topic': 'com.cystack.lockerapp'
                    },
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(content_available=True)
                    )
                )
            )
            response = messaging.send_multicast(message)
            if response.failure_count > 0:
                responses = response.responses
                for idx, resp in enumerate(responses):
                    if not resp.success:
                        failed_fcm_ids.append(fcm_ids[idx])
                        success_fcm_ids.remove(fcm_ids[idx])

        print("success; ", success_fcm_ids, failed_fcm_ids)
        return success_fcm_ids, failed_fcm_ids
