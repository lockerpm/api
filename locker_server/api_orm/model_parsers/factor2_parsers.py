from locker_server.api_orm.model_parsers.wrapper_specific_model_parser import get_specific_model_parser
from locker_server.api_orm.models import Factor2MethodORM, DeviceFactor2ORM
from locker_server.core.entities.factor2.device_factor2 import DeviceFactor2
from locker_server.core.entities.factor2.factor2_method import Factor2Method


class Factor2Parser:
    @classmethod
    def parse_factor2_method(cls, factor2_method_orm: Factor2MethodORM) -> Factor2Method:
        user_parser = get_specific_model_parser("UserParser")
        return Factor2Method(
            factor2_method_id=factor2_method_orm.id,
            method=factor2_method_orm.method,
            is_activate=factor2_method_orm.is_activate,
            activate_code=factor2_method_orm.activate_code,
            code_expired_time=factor2_method_orm.code_expired_time,
            updated_time=factor2_method_orm.updated_time,
            user=user_parser.parse_user(user_orm=factor2_method_orm.user)
        )

    @classmethod
    def parse_device_factor2(cls, device_factor2_orm: DeviceFactor2ORM) -> DeviceFactor2:
        user_parser = get_specific_model_parser("UserParser")
        return DeviceFactor2(
            device_factor2_id=device_factor2_orm.id,
            expired_time=device_factor2_orm.expired_time,
            factor2_method=cls.parse_factor2_method(factor2_method_orm=device_factor2_orm.factor2_method),
            device=user_parser.parse_device(device_factor2_orm=device_factor2_orm.device),
        )
