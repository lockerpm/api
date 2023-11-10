import requests

from django.conf import settings

from locker_server.shared.background.i_background import BackgroundThread, background_exception_wrapper
from locker_server.shared.caching.sync_cache import delete_sync_cache_data
from locker_server.shared.constants.members import PM_MEMBER_STATUS_CONFIRMED
from locker_server.shared.external_services.pm_sync import LIST_DELETE_SYNC_CACHE_EVENTS
from locker_server.shared.external_services.requester.retry_requester import requester
from locker_server.shared.external_services.websocket.websocket_sender import WebSocketSender
from locker_server.shared.general_websocket_consumer import WS_PWD_SYNC_GROUP_NAME

API_SYNC = "{}/micro_services/cystack_platform/pm/sync".format(settings.GATEWAY_API)
HEADERS = {
    'User-agent': 'CyStack Locker',
    "Authorization": settings.MICRO_SERVICE_USER_AUTH
}


class PwdSync:
    def __init__(self, event, user_ids=None, team=None, teams=None, add_all=False):
        self.event = event
        self.user_ids = user_ids
        self.team = team
        self.teams = teams
        self.add_all = add_all

    def send(self, data=None, is_background=True):
        if is_background:
            BackgroundThread(task=self.real_send, **{"data": data})
        else:
            self.real_send(data)

    @background_exception_wrapper
    def real_send(self, data):
        from locker_server.containers.containers import team_member_service

        user_ids = []
        if self.team:
            team_user_ids = team_member_service.list_member_user_ids_by_teams(teams=[self.team])
            user_ids = user_ids + team_user_ids if self.add_all else team_user_ids
        elif self.teams:
            teams_user_ids = team_member_service.list_member_user_ids_by_teams(
                teams=self.teams, status=PM_MEMBER_STATUS_CONFIRMED
            )
            user_ids = user_ids + teams_user_ids if self.add_all else teams_user_ids
        else:
            user_ids = user_ids + self.user_ids if self.add_all else self.user_ids
        try:
            # Clear all sync cache data
            if self.event in LIST_DELETE_SYNC_CACHE_EVENTS:
                for user_id in user_ids:
                    delete_sync_cache_data(user_id=user_id)
            user_ids = list(set(user_ids))
            if settings.SELF_HOSTED:
                for user_id in user_ids:
                    WebSocketSender.send_message(
                        group_name=WS_PWD_SYNC_GROUP_NAME.format(user_id),
                        message={
                            "event": "sync",
                            "type": self.event,
                            "data": data
                        }
                    )
            else:
                requester(method="POST", url=API_SYNC, headers=HEADERS, timeout=10, data_send={
                    "event": self.event,
                    "user_ids": list(set(user_ids)),
                    "data": data
                })

        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout):
            pass
