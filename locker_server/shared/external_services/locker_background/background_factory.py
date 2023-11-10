from locker_server.shared.external_services.locker_background.background import LockerBackground
from locker_server.shared.external_services.locker_background.constants import *
from locker_server.shared.external_services.locker_background.impl import *


class BackgroundFactory:
    @classmethod
    def get_background(cls, bg_name: str, background: bool = True) -> LockerBackground:
        if bg_name == BG_NOTIFY:
            return NotifyBackground(background)
        elif bg_name == BG_EVENT:
            return EventBackground(background)
        elif bg_name == BG_CIPHER:
            return CipherBackground(background)
        elif bg_name == BG_DOMAIN:
            return DomainBackground(background)
        elif bg_name == BG_ENTERPRISE_GROUP:
            return EnterpriseGroupBackground(background)
        raise Exception(f"Background name {bg_name} is not supported")
