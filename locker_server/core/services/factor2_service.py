from typing import List, Optional, NoReturn, Dict
from datetime import datetime

import pyotp

from locker_server.core.entities.factor2.factor2_method import Factor2Method
from locker_server.core.entities.user.user import User
from locker_server.core.exceptions.factor2_method_exception import Factor2CodeInvalidException, \
    Factor2MethodInvalidException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException, UserPasswordInvalidException
from locker_server.core.repositories.auth_repository import AuthRepository

from locker_server.core.repositories.factor2_method_repository import Factor2MethodRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.factor2 import FA2_METHOD_MAIL_OTP, LIST_FA2_METHOD, FA2_METHOD_SMART_OTP
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY
from locker_server.shared.external_services.user_notification.list_jobs import ID_FACTOR2_MAIL_LOGIN, \
    ID_FACTOR2_ENABLED_SUCCESSFULLY, ID_FACTOR2_DISABLED, ID_FACTOR2_ENABLED, ID_FACTOR2_DISABLED_SUCCESSFULLY
from locker_server.shared.utils.app import get_ip_location, now


class Factor2Service:
    """
    This class represents Use Cases related User
    """

    def __init__(self, user_repository: UserRepository,
                 auth_repository: AuthRepository,
                 factor2_method_repository: Factor2MethodRepository
                 ):
        self.user_repository = user_repository
        self.auth_repository = auth_repository
        self.factor2_method_repository = factor2_method_repository

    def list_user_factor2_methods(self, user_id: int, **filters) -> List[Factor2Method]:
        return self.factor2_method_repository.list_user_factor2_methods(
            user_id=user_id,
            **filters
        )

    def auth_otp_mail(self, email: str, raw_password: str, device_info: Dict, ip_address: str):
        user = self.user_repository.get_user_by_email(
            email=email
        )
        if not user:
            raise UserDoesNotExistException
        check_password = self.auth_repository.check_master_password(
            user=user,
            raw_password=raw_password
        )
        if not check_password:
            raise UserPasswordInvalidException

        mail_otp = self.factor2_method_repository.create_activate_code_by_method(
            user_id=user.user_id,
            method=FA2_METHOD_MAIL_OTP,
            new_code=True
        )
        ip_location = get_ip_location(ip_address)
        browser = device_info.get("browser", None)
        login_browser = "" if browser is None else browser.get("family") + " " + browser.get("version", "")
        os = device_info.get("os", None)
        login_os = "" if os is None else os.get("family", "") + " " + os.get("version", "")
        mail_data = {
            "user": user,
            "user_ids": [user.user_id],
            "job": ID_FACTOR2_MAIL_LOGIN,
            "scope": "id",
            "code": mail_otp.activate_code,
            "login_time": datetime.utcfromtimestamp(now()).strftime('%Y-%m-%d %H:%M:%S +00'),
            "login_email": user.email,
            "login_location": ip_location.get("location"),
            "login_ip": ip_location.get("ip", ""),
            "login_os": login_os,
            "login_browser": login_browser,
            # TODO: Replace gateway host
            "gateway_host": "api.locker.io"
        }
        BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
            func_name="notify_sending", **mail_data
        )

    def create_default_user_factor2(self, user_id: int) -> List:
        created_factor2 = []
        for method in LIST_FA2_METHOD:
            factor2_method = self.factor2_method_repository.create_factor2_method({
                "user_id": user_id,
                "method": method
            })
            created_factor2.append(factor2_method)
        return created_factor2

    def get_factor2(self, user_id) -> Dict:
        user = self.user_repository.get_user_by_id(user_id=user_id)
        if not user:
            raise UserDoesNotExistException
        factor2_methods = self.factor2_method_repository.list_user_factor2_methods(
            user_id=user.user_id
        )
        if factor2_methods is None or len(factor2_methods) < len(LIST_FA2_METHOD):
            factor2_methods = self.create_default_user_factor2(user_id=user_id)
        smart_otp = None
        mail_otp = None
        for factor2_method in factor2_methods:
            method = factor2_method.method
            if method == FA2_METHOD_SMART_OTP:
                smart_otp = factor2_method
            if method == FA2_METHOD_MAIL_OTP:
                mail_otp = factor2_method

        # Return data
        mail_otp_data = {
            "is_activate": mail_otp.is_activate
        }
        smart_otp_data = {
            "is_activate": smart_otp.is_activate
        }
        if not smart_otp_data.get("is_activate"):
            # Re-generate time OTP
            while True:
                base32_secret = pyotp.random_base32()
                users_by_secret = self.user_repository.list_users(**{
                    "base32_secret_factor2": base32_secret
                })
                if not users_by_secret:
                    break
            # Save new timeOTP
            updated_user = self.user_repository.update_user(
                user_id=user.user_id,
                user_update_data={
                    "base32_secret_factor2": base32_secret
                }
            )

            smart_factor2_url = pyotp.totp.TOTP(base32_secret).provisioning_uri(
                user.email,
                issuer_name="CyStack Security"
            )
            smart_otp_data.update({"url": smart_factor2_url, "secret": base32_secret})
        return {
            "is_factor2": user.is_factor2,
            "updated_time": max(smart_otp.updated_time, mail_otp.updated_time),
            "smart_otp": smart_otp_data,
            "mail_otp": mail_otp_data
        }

    def update_factor2(self, user_id: int, method: str, user_otp: str, device) -> User:
        user = self.user_repository.get_user_by_id(user_id=user_id)
        old_factor2 = user.is_factor2
        if not user:
            raise UserDoesNotExistException
        if method not in LIST_FA2_METHOD:
            raise Factor2MethodInvalidException
        smart_otp = self.factor2_method_repository.get_factor2_method_by_method(
            user_id=user.user_id,
            method=FA2_METHOD_SMART_OTP
        )
        mail_otp = self.factor2_method_repository.get_factor2_method_by_method(
            user_id=user.user_id,
            method=FA2_METHOD_MAIL_OTP
        )
        if method == FA2_METHOD_SMART_OTP:
            time_based_otp = pyotp.TOTP(user.base32_secret_factor2)
            if time_based_otp.verify(user_otp):
                smart_otp_update_data = {
                    "is_activate": not smart_otp.is_activate,
                    "updated_time": now()
                }
                smart_otp = self.factor2_method_repository.update_factor2_method(
                    factor2_method_id=smart_otp.factor2_method_id,
                    factor2_method_update_data=smart_otp_update_data
                )
                if smart_otp.is_activate:
                    mail_data = {
                        "user": user,
                        "user_ids": [user.user_id],
                        "scope": "id",
                        "job": ID_FACTOR2_ENABLED_SUCCESSFULLY,
                        "type": "app" if method == FA2_METHOD_SMART_OTP else "email",
                        "backup_code": user.base32_secret_factor2,
                        "gateway_host": "api.locker.io"
                    }
                    BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                        func_name="notify_sending", **mail_data
                    )
            else:
                raise Factor2CodeInvalidException
        elif method == FA2_METHOD_MAIL_OTP:
            if mail_otp.activate_code == user_otp and mail_otp.code_expired_time > now():
                mail_update_data = {
                    "is_activate": not mail_otp.is_activate,
                    "activate_code": "",
                    "code_expired_time": 0
                }
                mail_otp = self.factor2_method_repository.update_factor2_method(
                    factor2_method_id=mail_otp.factor2_method_id,
                    factor2_method_update_data=mail_update_data
                )
                if mail_otp.is_activate:
                    mail_data = {
                        "user": user,
                        "user_ids": [user.user_id],
                        "scope": "id",
                        "job": ID_FACTOR2_ENABLED_SUCCESSFULLY,
                        "type": "app" if method == FA2_METHOD_SMART_OTP else "email",
                        "backup_code": "",
                        # TODO: Replace gateway host
                        "gateway_host": "api.locker.io"
                    }
                    BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                        func_name="notify_sending", **mail_data
                    )
            else:
                raise Factor2CodeInvalidException
        if smart_otp.is_activate or mail_otp.is_activate:
            self.user_repository.update_user_factor2(user_id=user_id, is_factor2=True)
            self.user_repository.revoke_all_sessions(user=user, exclude_sso_token_ids=[device.sso_token_id])
            is_factor2 = True
        else:
            is_factor2 = False
        if is_factor2 != old_factor2:
            self.user_repository.revoke_all_sessions(user=user)
        user = self.user_repository.update_user_factor2(user_id=user_id, is_factor2=is_factor2)
        return user

    def create_mail_activate_code(self, user_id: int, method: str) -> Factor2Method:
        if method != FA2_METHOD_MAIL_OTP:
            raise Factor2MethodInvalidException
        user = self.user_repository.get_user_by_id(user_id=user_id)
        if not user:
            raise UserDoesNotExistException
        mail_otp = self.factor2_method_repository.create_activate_code_by_method(
            user_id=user.user_id,
            method=method,
            new_code=False
        )
        # Sending code via mail
        mail_data = {
            "user": user,
            "user_ids": [user.user_id],
            "scope": "id",
            "code": mail_otp.activate_code,
            # TODO: Replace gateway host
            "gateway_host": "api.locker.io"
        }

        if mail_otp.is_activate is True:
            mail_data.update({"job": ID_FACTOR2_DISABLED})
            BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                func_name="notify_sending", **mail_data
            )
        else:
            mail_data.update({"job": ID_FACTOR2_ENABLED})
            BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                func_name="notify_sending", **mail_data
            )

        return mail_otp

    def disable_factor2(self, user_id: int, raw_password: str) -> User:
        user = self.user_repository.get_user_by_id(user_id=user_id)
        if not user:
            raise UserDoesNotExistException
        valid_password = self.auth_repository.check_master_password(
            user=user,
            raw_password=raw_password
        )
        if not valid_password:
            raise UserPasswordInvalidException
        self.factor2_method_repository.disable_factor2_by_user(user_id=user.user_id)
        updated_user = self.user_repository.update_user_factor2(user_id=user.user_id, is_factor2=False)
        # Sending notification mail
        mail_data = {
            "user": user,
            "user_ids": [user.user_id],
            "scope": "id",
            "job": ID_FACTOR2_DISABLED_SUCCESSFULLY,
            # TODO: Replace host
            "gateway_host": "api.locker.io"
        }
        BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(func_name="notify_sending", **mail_data)
        return updated_user
