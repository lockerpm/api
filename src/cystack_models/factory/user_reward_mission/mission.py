from shared.log.cylog import CyLog


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

