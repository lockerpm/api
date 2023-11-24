from typing import Optional, List, Dict

import pyotp

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.core.entities.factor2.factor2_method import Factor2Method
from locker_server.api_orm.models.factor2.factor2_method import Factor2MethodORM
from locker_server.core.entities.user.user import User
from locker_server.core.repositories.factor2_method_repository import Factor2MethodRepository
from locker_server.shared.constants.factor2 import FA2_MAIL_CODE_EXPIRED_TIME, FA2_METHOD_SMART_OTP, FA2_METHOD_MAIL_OTP
from locker_server.shared.utils.app import now, random_n_digit

Factor2MethodORM = Factor2MethodORM
ModelParser = get_model_parser()


class Factor2MethodORMRepository(Factor2MethodRepository):
    # ------------------------ List Factor2Method resource ------------------- #
    def list_user_factor2_methods(self, user_id: int, **filter_params) -> List[Factor2Method]:
        factor2_methods_orm = Factor2MethodORM.objects.filter(
            user_id=user_id
        ).select_related("user")
        is_activate_param = filter_params.get("is_activate")
        if is_activate_param is not None:
            factor2_methods_orm = factor2_methods_orm.filter(
                is_activate=is_activate_param
            )
        return [
            ModelParser.factor2_parser().parse_factor2_method(factor2_method_orm=factor2_method_orm)
            for factor2_method_orm in factor2_methods_orm
        ]

    # ------------------------ Get Factor2Method resource --------------------- #
    def get_factor2_method_by_id(self, factor2_method_id: str) -> Optional[Factor2Method]:
        pass

    def get_factor2_method_by_method(self, user_id: int, method: str) -> Factor2Method:
        factor2_method_orm = Factor2MethodORM.retrieve_or_create(
            user_id=user_id,
            method=method
        )
        return ModelParser.factor2_parser().parse_factor2_method(factor2_method_orm=factor2_method_orm)

    def check_otp(self, user_id: int, method: str, otp_code: str) -> bool:
        try:
            factor2_method_orm = Factor2MethodORM.objects.get(
                user_id=user_id,
                method=method
            )
        except Factor2MethodORM.DoesNotExist:
            return False
        if factor2_method_orm.method == FA2_METHOD_SMART_OTP:
            user_secret = factor2_method_orm.user.base32_secret_factor2
            totp = pyotp.TOTP(user_secret)
            is_valid = totp.verify(otp_code)
            return is_valid

        elif factor2_method_orm.method == FA2_METHOD_MAIL_OTP:
            if factor2_method_orm.code_expired_time <= now():
                return False
            if otp_code and otp_code == factor2_method_orm.activate_code:
                return True
            else:
                return False
        return False

    # ------------------------ Create Factor2Method resource --------------------- #
    def create_factor2_method(self, factor2_method_create_data: Dict) -> Factor2Method:
        factor2_method_orm = Factor2MethodORM.retrieve_or_create(**factor2_method_create_data)
        return ModelParser.factor2_parser().parse_factor2_method(factor2_method_orm=factor2_method_orm)

    def create_activate_code_by_method(self, user_id: int, method: str, new_code: bool) -> Factor2Method:
        factor2_method_orm = Factor2MethodORM.retrieve_or_create(
            user_id=user_id,
            method=method
        )
        if (factor2_method_orm.activate_code == "") or (factor2_method_orm.code_expired_time < now()) or (
                new_code is True):
            activate_code = random_n_digit(n=6).upper()
            code_expired_time = now() + FA2_MAIL_CODE_EXPIRED_TIME * 60
            factor2_method_orm.activate_code = activate_code
            factor2_method_orm.code_expired_time = code_expired_time
            factor2_method_orm.save()
        return ModelParser.factor2_parser().parse_factor2_method(factor2_method_orm=factor2_method_orm)

    # ------------------------ Update Factor2Method resource --------------------- #
    def update_factor2_method(self, factor2_method_id: str, factor2_method_update_data: Dict) -> Factor2Method:
        try:
            factor2_method_orm = Factor2MethodORM.objects.get(id=factor2_method_id)
        except Factor2MethodORM.DoesNotExist:
            return None
        factor2_method_orm.is_activate = factor2_method_update_data.get("is_activate", factor2_method_orm.is_activate)
        factor2_method_orm.updated_time = factor2_method_update_data.get("updated_time", now())
        factor2_method_orm.activate_code = factor2_method_update_data.get("activate_code",
                                                                          factor2_method_orm.activate_code)
        factor2_method_orm.save()
        return ModelParser.factor2_parser().parse_factor2_method(factor2_method_orm=factor2_method_orm)

    def disable_factor2_by_user(self, user_id: int):
        user_factor2_methods = Factor2MethodORM.objects.filter(user_id=user_id)
        user_factor2_methods.update(is_activate=False, updated_time=now())

    # ------------------------ Delete Factor2Method resource --------------------- #
