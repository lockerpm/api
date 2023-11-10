from locker_server.core.entities.user.user import User
from locker_server.core.entities.user_plan.pm_user_plan import PMUserPlan


class PMUserPlanFamily(object):
    def __init__(self, pm_user_plan_family_id: int, created_time: int = None, email: str = None,
                 user: User = None, root_user_plan: PMUserPlan = None):
        self._pm_user_plan_family_id = pm_user_plan_family_id
        self._created_time = created_time
        self._email = email
        self._user = user
        self._root_user_plan = root_user_plan

    @property
    def pm_user_plan_family_id(self):
        return self._pm_user_plan_family_id

    @property
    def created_time(self):
        return self._created_time

    @property
    def email(self):
        return self._email

    @property
    def user(self):
        return self._user

    @property
    def root_user_plan(self):
        return self._root_user_plan
