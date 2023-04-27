from shared.log.cylog import CyLog


# The valid review must be in one day
MAX_REVIEW_DURATION_TIME = 24 * 3600


class Mission:
    def __init__(self, mission_type: str, extra_requirements=None):
        # self.mission_id = mission_id
        self.mission_type = mission_type
        self.extra_requirements = extra_requirements

    @property
    def name(self):
        return self.__class__.__name__

    def check_mission_completion(self, input_data):
        raise NotImplementedError

