import requests

from django.conf import settings

from shared.constants.members import PM_MEMBER_STATUS_CONFIRMED


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

    def send(self, data=None):
        user_ids = []
        if self.team:
            team_user_ids = list(self.team.team_members.values_list('user_id', flat=True))
            user_ids = user_ids + team_user_ids if self.add_all else team_user_ids
        elif self.teams:
            from cystack_models.models.members.team_members import TeamMember
            teams_user_ids = list(
                TeamMember.objects.filter(team_id__in=self.teams, status=PM_MEMBER_STATUS_CONFIRMED).values_list('user_id', flat=True).distinct()
            )
            user_ids = user_ids + teams_user_ids if self.add_all else teams_user_ids
        else:
            user_ids = user_ids + self.user_ids if self.add_all else self.user_ids
        try:
            requests.post(url=API_SYNC, verify=False, headers=HEADERS, timeout=10, json={
                "event": self.event,
                "user_ids": list(set(user_ids)),
                "data": data
            })
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout):
            pass
