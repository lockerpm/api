from typing import Optional, List

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_mission_model
from locker_server.core.entities.user_reward.mission import Mission
from locker_server.core.repositories.mission_repository import MissionRepository

MissionORM = get_mission_model()
ModelParser = get_model_parser()


class MissionORMRepository(MissionRepository):

    # ------------------------ List Mission resource ------------------- #
    def list_available_mission_ids(self) -> List[str]:
        mission_ids = MissionORM.objects.filter(available=True).order_by('order_index').values_list('id', flat=True)
        mission_ids = list(mission_ids)
        return mission_ids

    # ------------------------ Get Mission resource --------------------- #

    # ------------------------ Create Mission resource --------------------- #

    # ------------------------ Update Mission resource --------------------- #

    # ------------------------ Delete Mission resource --------------------- #
