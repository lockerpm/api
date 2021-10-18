from shared.background.constants import *
from shared.background.i_background import ILockerBackground
from shared.background.implements import *


class LockerBackgroundFactory:
    @classmethod
    def get_background(cls, bg_name, background: bool = True) -> ILockerBackground:
        if bg_name == BG_NOTIFY:
            return NotifyBackground(background)
        elif bg_name == BG_EVENT:
            return EventBackground(background)
        raise Exception('Background name {} is not supported'.format(bg_name))
