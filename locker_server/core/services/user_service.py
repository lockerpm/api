from datetime import datetime
from typing import Optional, List, Dict, NoReturn, Union

import jwt
from django.conf import settings

from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.enterprise.member.enterprise_member import EnterpriseMember
from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.user import User
from locker_server.core.entities.user_plan.pm_user_plan import PMUserPlan
from locker_server.core.exceptions.device_exception import DeviceDoesNotExistException
from locker_server.core.exceptions.team_member_exception import TeamMemberDoesNotExistException
from locker_server.core.exceptions.user_exception import *
from locker_server.core.repositories.auth_repository import AuthRepository
from locker_server.core.repositories.cipher_repository import CipherRepository
from locker_server.core.repositories.device_access_token_repository import DeviceAccessTokenRepository
from locker_server.core.repositories.device_repository import DeviceRepository
from locker_server.core.repositories.enterprise_member_repository import EnterpriseMemberRepository
from locker_server.core.repositories.enterprise_policy_repository import EnterprisePolicyRepository
from locker_server.core.repositories.enterprise_repository import EnterpriseRepository
from locker_server.core.repositories.factor2_method_repository import Factor2MethodRepository
from locker_server.core.repositories.notification_setting_repository import NotificationSettingRepository
from locker_server.core.repositories.payment_repository import PaymentRepository
from locker_server.core.repositories.plan_repository import PlanRepository
from locker_server.core.repositories.team_member_repository import TeamMemberRepository
from locker_server.core.repositories.team_repository import TeamRepository
from locker_server.core.repositories.user_plan_repository import UserPlanRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.caching.sync_cache import delete_sync_cache_data, get_sync_cache_key
from locker_server.shared.constants.account import LOGIN_METHOD_PASSWORD
from locker_server.shared.constants.enterprise_members import *
from locker_server.shared.constants.event import EVENT_USER_LOGIN_FAILED, EVENT_USER_LOGIN, EVENT_USER_BLOCK_LOGIN
from locker_server.shared.constants.factor2 import FA2_METHOD_MAIL_OTP
from locker_server.shared.constants.members import PM_MEMBER_STATUS_INVITED, PM_MEMBER_STATUS_ACCEPTED
from locker_server.shared.constants.token import TOKEN_EXPIRED_TIME_INVITE_MEMBER, TOKEN_TYPE_RESET_PASSWORD, \
    TOKEN_PREFIX
from locker_server.shared.constants.transactions import *
from locker_server.shared.constants.user_notification import NOTIFY_CHANGE_MASTER_PASSWORD, NOTIFY_SHARING
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY, BG_EVENT
from locker_server.shared.external_services.pm_sync import SYNC_EVENT_MEMBER_UPDATE, PwdSync, SYNC_EVENT_VAULT, \
    SYNC_EVENT_MEMBER_ACCEPTED
from locker_server.shared.utils.app import secure_random_string, now
from locker_server.shared.utils.network import detect_device


class UserService:
    """
    This class represents Use Cases related User
    """

    def __init__(self, user_repository: UserRepository,
                 auth_repository: AuthRepository,
                 device_repository: DeviceRepository,
                 device_access_token_repository: DeviceAccessTokenRepository,
                 user_plan_repository: UserPlanRepository,
                 payment_repository: PaymentRepository, plan_repository: PlanRepository,
                 team_repository: TeamRepository,
                 team_member_repository: TeamMemberRepository,
                 cipher_repository: CipherRepository,
                 enterprise_repository: EnterpriseRepository,
                 enterprise_member_repository: EnterpriseMemberRepository,
                 enterprise_policy_repository: EnterprisePolicyRepository,
                 notification_setting_repository: NotificationSettingRepository,
                 factor2_method_repository: Factor2MethodRepository
                 ):
        self.user_repository = user_repository
        self.auth_repository = auth_repository
        self.device_repository = device_repository
        self.device_access_token_repository = device_access_token_repository
        self.user_plan_repository = user_plan_repository
        self.payment_repository = payment_repository
        self.plan_repository = plan_repository
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.cipher_repository = cipher_repository
        self.enterprise_repository = enterprise_repository
        self.enterprise_member_repository = enterprise_member_repository
        self.enterprise_policy_repository = enterprise_policy_repository
        self.notification_setting_repository = notification_setting_repository
        self.factor2_method_repository = factor2_method_repository

    def get_current_plan(self, user: User) -> PMUserPlan:
        return self.user_plan_repository.get_user_plan(user_id=user.user_id)

    def update_plan(self, user_id: int, plan_type_alias: str, duration: str = DURATION_MONTHLY, scope: str = None,
                    **kwargs):
        return self.user_plan_repository.update_plan(
            user_id=user_id, plan_type_alias=plan_type_alias, duration=duration, scope=scope, **kwargs
        )

    def get_user_type(self, user: User) -> str:
        return self.user_repository.get_user_type(user_id=user.user_id)

    def get_default_enterprise(self, user_id: int, enterprise_name: str = None,
                               create_if_not_exist=False) -> Optional[Enterprise]:
        return self.user_plan_repository.get_default_enterprise(
            user_id=user_id, enterprise_name=enterprise_name, create_if_not_exist=create_if_not_exist
        )

    def is_blocked_by_source(self, user: User, utm_source: str) -> bool:
        return self.payment_repository.is_blocked_by_source(user_id=user.user_id, utm_source=utm_source)

    def update_user(self, user_id: int, user_update_data) -> Optional[User]:
        user = self.user_repository.update_user(user_id=user_id, user_update_data=user_update_data)
        if not user:
            raise UserDoesNotExistException
        return user

    def update_passwordless_cred(self, user: User, fd_credential_id: str, fd_random: str) -> User:
        return self.user_repository.update_passwordless_cred(
            user_id=user.user_id, fd_credential_id=fd_credential_id, fd_random=fd_random
        )

    def retrieve_by_id(self, user_id: int) -> User:
        user = self.user_repository.get_user_by_id(user_id=user_id)
        if not user:
            raise UserDoesNotExistException
        return user

    def retrieve_by_email(self, email: str) -> Optional[User]:
        user = self.user_repository.get_user_by_email(email=email)
        if not user:
            raise UserDoesNotExistException
        return user

    def retrieve_or_create_by_id(self, user_id: int) -> User:
        user, is_created = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
        if is_created is True:
            self.get_current_plan(user=user)
        return user

    def retrieve_or_create_by_email(self, email: str) -> User:
        user, is_created = self.user_repository.retrieve_or_create_by_email(email=email)
        if is_created is True:
            self.get_current_plan(user=user)
        return user

    def get_from_cystack_id(self, user_id: int) -> Dict:
        return self.user_repository.get_from_cystack_id(user_id=user_id)

    def register_user(self, user_id: Union[str, int], master_password_hash: str, key: str, keys,
                      default_plan=PLAN_TYPE_PM_FREE, default_plan_time=3 * 365 * 86400,
                      **kwargs):
        if not self.allow_create_user(default_plan=default_plan):
            raise UserCreationDeniedException
        if isinstance(user_id, int):
            user = self.retrieve_or_create_by_id(user_id=user_id)
        else:
            user = self.retrieve_or_create_by_email(email=user_id)
        is_supper_admin = True if default_plan == PLAN_TYPE_PM_ENTERPRISE else False
        master_password_score = kwargs.get("score") or kwargs.get("master_password_score") or user.master_password_score
        user_new_creation_data = {
            "kdf": kwargs.get("kdf", 0),
            "kdf_iterations": kwargs.get("kdf_iterations", 100000),
            "key": key,
            "public_key": keys.get("public_key"),
            "private_key": keys.get("encrypted_private_key"),
            "master_password_hash": master_password_hash,
            "master_password_hint": kwargs.get("master_password_hint", ""),
            "master_password_score": master_password_score,
            "api_key": secure_random_string(length=30),
            "activated": True,
            "activated_date": now(),
            "revision_date": now(),
            "delete_account_date": None,
            "is_supper_admin": is_supper_admin,
            "full_name": kwargs.get("full_name") or user_id,
        }
        user = self.user_repository.update_user(user_id=user.user_id, user_update_data=user_new_creation_data)
        current_plan = self.get_current_plan(user=user)
        # Upgrade user to default plan
        if default_plan is not None and default_plan != PLAN_TYPE_PM_FREE:
            start_period = current_plan.start_period
            if start_period is None:
                start_period = now()
            end_period = default_plan_time + start_period
            current_plan = self.update_plan(
                user_id=user.user_id, plan_type_alias=default_plan, duration=current_plan.duration,
                **{
                    "start_period": start_period,
                    "end_period": end_period
                }
            )
        # Upgrade trial plan
        trial_plan = kwargs.get("trial_plan")
        is_trial_promotion = kwargs.get("is_trial_promotion", False)
        enterprise_name = kwargs.get("enterprise_name")

        # Upgrade trial plan
        if trial_plan and trial_plan != PLAN_TYPE_PM_FREE and current_plan.pm_plan.alias == PLAN_TYPE_PM_FREE:
            trial_plan_obj = self.plan_repository.get_plan_by_alias(alias=trial_plan)
            if trial_plan_obj.is_team_plan is False:
                if current_plan.is_personal_trial_applied() is False:
                    end_period = now() + TRIAL_PERSONAL_PLAN
                    trial_duration = TRIAL_PERSONAL_DURATION_TEXT
                    if is_trial_promotion is True and trial_plan_obj.alias == PLAN_TYPE_PM_FAMILY:
                        end_period = now() + TRIAL_PROMOTION
                        trial_duration = TRIAL_PROMOTION_DURATION_TEXT
                    plan_metadata = {
                        "start_period": now(),
                        "end_period": end_period
                    }
                    self.user_plan_repository.update_plan(
                        user_id=user.user_id, plan_type_alias=trial_plan_obj.alias,
                        duration=DURATION_MONTHLY, **plan_metadata
                    )
                    self.user_plan_repository.set_personal_trial_applied(user_id=user_id, applied=True, platform="web")
                    # Send trial mail
                    BackgroundFactory.get_background(
                        bg_name=BG_NOTIFY, background=True
                    ).run(
                        func_name="trial_successfully", **{
                            "user_id": user.user_id,
                            "plan": trial_plan_obj.alias,
                            "payment_method": None,
                            "duration": trial_duration,
                        }
                    )

            # Enterprise plan
            else:
                if self.user_repository.is_in_enterprise(user_id=user_id) is False and \
                        current_plan.pm_plan.alias == PLAN_TYPE_PM_FREE:
                    end_period = now() + TRIAL_TEAM_PLAN
                    number_members = TRIAL_TEAM_MEMBERS
                    plan_metadata = {
                        "start_period": now(),
                        "end_period": end_period,
                        "number_members": number_members,
                        "enterprise_name": enterprise_name
                    }
                    self.user_plan_repository.update_plan(
                        user_id=user.user_id, plan_type_alias=trial_plan_obj.alias, duration=DURATION_MONTHLY,
                        **plan_metadata
                    )
                    self.user_plan_repository.set_enterprise_trial_applied(user_id=user_id, applied=True)
                    # Send trial enterprise mail here
                    BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                        func_name="trial_enterprise_successfully", **{"user_id": user.user_id}
                    )

        # Upgrade plan if the user is a family member
        self.user_plan_repository.upgrade_member_family_plan(user=user)
        # Update sharing confirmation
        self.team_member_repository.sharing_invitations_confirm(user=user)
        # Update enterprise invitations
        self.enterprise_member_repository.enterprise_invitations_confirm(user=user)
        # Update enterprise share groups
        self.enterprise_member_repository.enterprise_share_groups_confirm(user=user)
        # Update lifetime mail
        if user.saas_source:
            if current_plan.pm_plan.alias in [PLAN_TYPE_PM_LIFETIME, PLAN_TYPE_PM_LIFETIME_FAMILY]:
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_locker_mail", **{
                        "user_ids": [user.user_id],
                        "job": "upgraded_to_lifetime_from_code",
                        "service_name": user.saas_source,
                    }
                )
            else:
                BackgroundFactory.get_background(bg_name=BG_NOTIFY).run(
                    func_name="notify_locker_mail", **{
                        "user_ids": [user.user_id],
                        "job": "upgraded_from_code_promo",
                        "service_name": user.saas_source,
                        "plan": current_plan.pm_plan.alias
                    }
                )

        return user

    def invitation_confirmation(self, user_id: int, email: str = None) -> User:
        user = self.retrieve_or_create_by_id(user_id=user_id)
        # Update sharing confirmation
        self.team_member_repository.sharing_invitations_confirm(user=user, email=email)
        # Update enterprise invitations
        self.enterprise_member_repository.enterprise_invitations_confirm(user=user, email=email)
        return user

    def is_require_passwordless(self, user_id: int,
                                require_enterprise_member_status: str = E_MEMBER_STATUS_CONFIRMED) -> bool:
        return self.user_repository.is_require_passwordless(
            user_id=user_id, require_enterprise_member_status=require_enterprise_member_status
        )

    def is_block_by_2fa_policy(self, user_id: int, is_factor2: bool) -> bool:
        return self.user_repository.is_block_by_2fa_policy(user_id=user_id, is_factor2=is_factor2)

    def count_failed_login_event(self, user_id: int) -> int:
        return self.user_repository.count_failed_login_event(user_id=user_id)

    def user_session(self, user: User, password: str, client_id: str = None, device_identifier: str = None,
                     device_name: str = None, device_type: int = None, is_factor2: bool = False,
                     token_auth_value: str = None, secret: str = None,
                     ip: str = None, ua: str = None):
        # Check login block
        if user.login_block_until and user.login_block_until > now():
            wait = user.login_block_until - now()
            raise UserAuthBlockingEnterprisePolicyException(wait=wait)

        user_enterprises = self.enterprise_repository.list_user_enterprises(
            user_id=user.user_id, **{"status": E_MEMBER_STATUS_CONFIRMED}
        )
        user_enterprise_ids = [enterprise.enterprise_id for enterprise in user_enterprises]

        # Login failed
        if self.auth_repository.check_master_password(user=user, raw_password=password) is False:
            if user_enterprise_ids:
                BackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                    "enterprise_ids": user_enterprise_ids, "user_id": user.user_id, "acting_user_id": user.user_id,
                    "type": EVENT_USER_LOGIN_FAILED, "ip_address": ip
                })
                block_failed_login_policy = self.enterprise_policy_repository.get_block_failed_login_policy(
                    user_id=user.user_id
                )
                if block_failed_login_policy:
                    failed_login_attempts = block_failed_login_policy.failed_login_attempts
                    failed_login_duration = block_failed_login_policy.failed_login_duration
                    failed_login_block_time = block_failed_login_policy.failed_login_block_time
                    latest_request_login = user.last_request_login

                    user = self.user_repository.update_login_time_user(
                        user_id=user.user_id,
                        update_data={
                            "login_failed_attempts": user.login_failed_attempts + 1,
                            "last_request_login": now()
                        }
                    )
                    if user.login_failed_attempts >= failed_login_attempts and \
                            latest_request_login and now() - latest_request_login < failed_login_duration:
                        # Lock login of this member
                        user = self.user_repository.update_login_time_user(
                            user_id=user.user_id,
                            update_data={
                                "login_block_until": now() + failed_login_block_time
                            }
                        )
                        # Create block failed login event
                        BackgroundFactory.get_background(bg_name=BG_EVENT).run(
                            func_name="create_by_enterprise_ids", **{
                                "enterprise_ids": user_enterprise_ids, "user_id": user.user_id,
                                "type": EVENT_USER_BLOCK_LOGIN, "ip_address": ip
                            }
                        )
                        owner = self.enterprise_member_repository.get_primary_member(
                            enterprise_id=block_failed_login_policy.enterprise.enterprise_id
                        ).user.user_id
                        raise UserAuthBlockedEnterprisePolicyException(
                            failed_login_owner_email=block_failed_login_policy.failed_login_owner_email,
                            owner=owner,
                            lock_time="{} (UTC+00)".format(
                                datetime.utcfromtimestamp(now()).strftime('%H:%M:%S %d-%m-%Y')
                            ),
                            unlock_time="{} (UTC+00)".format(
                                datetime.utcfromtimestamp(user.login_block_until).strftime('%H:%M:%S %d-%m-%Y')
                            ),
                            ip=ip
                        )
            raise UserAuthFailedException

        if self.enterprise_repository.list_user_enterprises(user_id=user.user_id, **{"is_activated": False}):
            raise UserIsLockedByEnterpriseException
        if self.enterprise_member_repository.lock_login_account_belong_enterprise(user_id=user.user_id) is True:
            raise UserBelongEnterpriseException
        if [e for e in user_enterprises if e.locked is True]:
            raise UserEnterprisePlanExpiredException

        # Check 2FA policy
        if is_factor2 is False:
            for enterprise in user_enterprises:
                policy = self.enterprise_policy_repository.get_enterprise_2fa_policy(
                    enterprise_id=enterprise.enterprise_id
                )
                if not policy:
                    continue
                enterprise_member = self.enterprise_member_repository.get_enterprise_member_by_user_id(
                    enterprise_id=enterprise.enterprise_id, user_id=user.user_id,
                )
                if not enterprise_member:
                    continue
                member_role = enterprise_member.role.name

                only_admin = policy.only_admin
                if only_admin is False or \
                        (only_admin and member_role in [E_MEMBER_ROLE_ADMIN, E_MEMBER_ROLE_PRIMARY_ADMIN]):
                    raise User2FARequireException

        # Unblock login
        user = self.user_repository.update_login_time_user(user_id=user.user_id, update_data={
            "last_request_login": now(),
            "login_failed_attempts": 0,
            "login_block_until": now()
        })

        # Get sso token id from authentication token
        try:
            decoded_token = self.auth_repository.decode_token(token_auth_value, secret=secret)
        except AttributeError:
            decoded_token = None
        sso_token_id = decoded_token.get("sso_token_id") if decoded_token else None

        # Get current user plan, the sync device limit
        current_plan = self.get_current_plan(user=user)
        limit_sync_device = None if user_enterprise_ids else current_plan.pm_plan.sync_device
        # The list stores sso token id which will not be synchronized
        not_sync_sso_token_ids = []

        # First, check the device exists
        device_existed = self.device_repository.get_device_by_identifier(
            user_id=user.user_id, device_identifier=device_identifier
        )
        device_info = detect_device(ua_string=ua)
        device_obj = self.device_repository.retrieve_or_create(user_id=user.user_id, **{
            "client_id": client_id,
            "device_name": device_name,
            "device_type": device_type,
            "device_identifier": device_identifier,
            "os": device_info.get("os"),
            "browser": device_info.get("browser"),
            "scope": "api offline_access",
            "token_type": "Bearer",
            "refresh_token": secure_random_string(length=64, lower=False)
        })
        # If the device does not exist => New device => Create new one
        if not device_existed:
            all_devices = self.device_repository.list_user_devices(user_id=user.user_id)
            if limit_sync_device and len(all_devices) > limit_sync_device:
                old_devices = all_devices[limit_sync_device:]
                old_devices_ids = [old_device.device_id for old_device in old_devices]
                not_sync_sso_token_ids = self.device_access_token_repository.list_sso_token_ids(
                    device_ids=old_devices_ids
                )
                self.device_access_token_repository.remove_devices_access_tokens(device_ids=old_devices_ids)

        # Set last login
        device_obj = self.device_repository.set_last_login(device_id=device_obj.device_id, last_login=now())
        # Retrieve or create new access token
        access_token = self.device_access_token_repository.fetch_device_access_token(
            device=device_obj, renewal=True, sso_token_id=sso_token_id
        )
        result = {
            "refresh_token": device_obj.refresh_token,
            "access_token": access_token.access_token,
            "token_type": device_obj.token_type,
            "public_key": user.public_key,
            "private_key": user.private_key,
            "key": user.key,
            "kdf": user.kdf,
            "kdf_iterations": user.kdf_iterations,
            "not_sync": not_sync_sso_token_ids,
            "has_no_master_pw_item": not self.user_repository.has_master_pw_item(user_id=user.user_id),
            "is_super_admin": user.is_supper_admin
        }
        # Create event login successfully
        if user_enterprise_ids:
            BackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                "enterprise_ids": user_enterprise_ids, "user_id": user.user_id, "acting_user_id": user.user_id,
                "type": EVENT_USER_LOGIN, "ip_address": ip
            })

        return result

    def update_device_fcm_id(self, user: User, device_identifier: str, fcm_id: str) -> Optional[Device]:
        device = self.device_repository.update_fcm_id(
            user_id=user.user_id, device_identifier=device_identifier, fcm_id=fcm_id
        )
        if not device:
            raise DeviceDoesNotExistException
        return device

    def change_master_password(self, user: User, key: str, master_password_hash: str, new_master_password_hash: str,
                               new_master_password_hint: str = None, score: float = None, login_method: str = None,
                               current_sso_token_id: str = None):
        if master_password_hash:
            if self.auth_repository.check_master_password(user=user, raw_password=master_password_hash) is False:
                raise UserAuthFailedException
        if login_method and login_method == LOGIN_METHOD_PASSWORD and \
                self.is_require_passwordless(user_id=user.user_id) is True:
            raise UserAuthFailedPasswordlessRequiredException
        self.user_repository.change_master_password(
            user=user, new_master_password_hash=new_master_password_hash,
            new_master_password_hint=new_master_password_hint,
            key=key, score=score, login_method=login_method
        )
        exclude_sso_token_ids = None
        client = None
        if login_method:
            exclude_sso_token_ids = [current_sso_token_id] if current_sso_token_id else []
            exclude_device_access_token = self.device_access_token_repository.get_first_device_access_token_by_sso_ids(
                user_id=user.user_id, sso_token_ids=exclude_sso_token_ids
            )
            client = exclude_device_access_token.device.client_id if exclude_device_access_token else None
        self.user_repository.revoke_all_sessions(user=user, exclude_sso_token_ids=exclude_sso_token_ids)
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_CHANGE_MASTER_PASSWORD, user_ids=[user.user_id]
        )
        return {
            "notification": True if user.user_id in mail_user_ids else False,
            "mail_user_ids": mail_user_ids,
            "client": client
        }

    def check_master_password(self, user: User, master_password_hash: str) -> bool:
        try:
            return self.auth_repository.check_master_password(user=user, raw_password=master_password_hash)
        except TypeError:
            return False

    def revoke_all_sessions(self, user: User, exclude_sso_token_ids: List[str] = None):
        self.user_repository.revoke_all_sessions(user=user, exclude_sso_token_ids=exclude_sso_token_ids)

    def delete_locker_user(self, user: User):
        # Check if user is the owner of the enterprise
        default_enterprise = self.get_default_enterprise(user_id=user.user_id)
        # Clear data of the default enterprise
        if default_enterprise:
            self.enterprise_repository.delete_completely(enterprise=default_enterprise)

        # Remove all user's share teams
        personal_sharing_ids = self.team_repository.list_owner_sharing_ids(user_id=user.user_id)
        self.cipher_repository.delete_permanent_multiple_cipher_by_teams(team_ids=personal_sharing_ids)
        self.team_repository.delete_multiple_teams(team_ids=personal_sharing_ids)

        # Delete sharing with me
        owners_share_with_me = self.team_repository.delete_sharing_with_me(user_id=user.user_id)
        PwdSync(event=SYNC_EVENT_MEMBER_UPDATE, user_ids=owners_share_with_me).send()

        # Deactivated this account and cancel the current plan immediately
        self.user_plan_repository.cancel_plan(user=user, immediately=True)
        self.user_repository.delete_account(user)

    def purge_user(self, user: User):
        shared_ciphers_members = self.user_repository.purge_account(user=user)
        shared_member_user_ids = [cipher_member.get("shared_member") for cipher_member in shared_ciphers_members]
        PwdSync(event=SYNC_EVENT_VAULT, user_ids=[user.user_id] + shared_member_user_ids).send()

        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=shared_member_user_ids
        )
        notification = [c for c in shared_ciphers_members if c.get("shared_member") in notification_user_ids]
        return notification

    def list_sharing_invitations(self, user: User):
        return self.team_member_repository.list_members_by_user_id(
            user_id=user.user_id, **{
                "statuses": [PM_MEMBER_STATUS_INVITED, PM_MEMBER_STATUS_ACCEPTED]
            }
        )

    def update_sharing_invitation(self, user: User, member_id: int, status: str):
        team_member = self.team_member_repository.get_team_member_by_id(team_member_id=member_id)
        if not team_member:
            raise TeamMemberDoesNotExistException
        if team_member.status != PM_MEMBER_STATUS_INVITED:
            raise TeamMemberDoesNotExistException
        if team_member.user.user.activated is False or team_member.team.key is None:
            raise TeamMemberDoesNotExistException
        if status == "accept":
            team_member = self.team_member_repository.accept_invitation(team_member_id=team_member.team_member_id)
            primary_owner = self.team_member_repository.get_primary_member(team_id=team_member.team.team_id)
            PwdSync(event=SYNC_EVENT_MEMBER_ACCEPTED, user_ids=[primary_owner.user.user_id, user.user_id]).send()
            result = {"status": status, "owner": primary_owner.user.user_id, "team_name": team_member.team.name}

        else:
            self.team_member_repository.reject_invitation(team_member_id=member_id)
            PwdSync(event=SYNC_EVENT_MEMBER_ACCEPTED, user_ids=[user.user_id]).send()
            result = {"status": status}
        return result

    def list_team_ids_owner_family_plan(self, user_id: int) -> List[str]:
        return self.team_member_repository.list_team_ids_owner_family_plan(user_id=user_id)

    def list_user_devices(self, user_id: int) -> List[Device]:
        all_devices = self.device_repository.list_user_devices(user_id=user_id)
        for device in all_devices:
            device.is_active = self.device_repository.is_active(device_id=device.device_id)
        return all_devices

    def list_user_by_emails(self, emails: List[str]) -> List[User]:
        return self.user_repository.list_users(**{"emails": emails})

    def list_user_by_ids(self, user_ids: List[int]) -> List[User]:
        return self.user_repository.list_users(**{"user_ids": user_ids})

    def list_user_ids(self, **filter_params) -> List[int]:
        return self.user_repository.list_user_ids(**filter_params)

    def list_user_emails(self, user_ids) -> List[str]:
        return self.user_repository.list_user_emails(user_ids=user_ids)

    def remove_user_device(self, user_id: int, device_identifier: str) -> List[str]:
        device = self.device_repository.get_device_by_identifier(user_id=user_id, device_identifier=device_identifier)
        if not device:
            raise DeviceDoesNotExistException
        sso_token_ids = self.device_repository.destroy_device(device=device)
        return sso_token_ids

    def delete_sync_cache_data(self, user_id: int):
        self.user_repository.delete_sync_cache_data(user_id=user_id)

    @staticmethod
    def get_sync_cache_key(user_id, page=1, size=100):
        return get_sync_cache_key(user_id=user_id, page=page, size=size)

    def is_active_enterprise_member(self, user_id: int) -> bool:
        return self.enterprise_member_repository.is_active_enterprise_member(user_id=user_id)

    def update_plan_by_plan_type(self, user: User, plan_type_alias, **plan_metadata) -> NoReturn:
        return self.user_plan_repository.update_plan(
            user_id=user.user_id, plan_type_alias=plan_type_alias,
            **plan_metadata
        )

    def update_user_plan_by_id(self, user_plan_id: str, user_plan_update_data):
        return self.user_plan_repository.update_user_plan_by_id(
            user_plan_id=user_plan_id,
            user_plan_update_data=user_plan_update_data
        )

    def cancel_plan(self, user: User, immediately=False, **kwargs):
        end_time = self.user_plan_repository.cancel_plan(user=user, immediately=immediately, **kwargs)
        return end_time

    def count_weak_cipher_password(self, user_ids: List[int]) -> int:
        return self.user_repository.count_weak_cipher_password(
            user_ids=user_ids
        )

    def get_user_cipher_overview(self, user_id: int) -> Dict:
        return self.user_repository.get_user_cipher_overview(
            user_id=user_id
        )

    def get_customer_data(self, user: User, token_card=None, id_card=None):
        return self.user_repository.get_customer_data(user=user, token_card=token_card, id_card=id_card)

    def allow_create_user(self, default_plan: str) -> bool:
        if default_plan == PLAN_TYPE_PM_ENTERPRISE:
            return self.user_repository.allow_create_enterprise_user()
        return True

    def check_exist(self) -> bool:
        return self.user_repository.check_exist()

    def check_reset_password_token(self, token_value: str, secret: str) -> Optional[EnterpriseMember]:
        payload = self.auth_repository.decode_token(
            value=token_value,
            secret=secret
        )
        token_type = payload.get("token_type")
        if token_type != TOKEN_TYPE_RESET_PASSWORD:
            return None
        current_time = now()
        expired_time = payload.get("expired_time")
        if expired_time <= current_time:
            return None
        member = self.enterprise_member_repository.get_enterprise_member_by_token(
            token=token_value
        )
        if not member:
            return None
        if member.user and member.user.user_id == payload.get("user_id"):
            return member
        return None

    def reset_password_by_token(self, secret: str, token_value: str, new_password: str, new_key: str = None):
        member = self.check_reset_password_token(
            token_value=token_value,
            secret=secret
        )
        if not member:
            raise UserResetPasswordTokenInvalidException
        self.user_repository.change_master_password(
            user=member.user,
            new_master_password_hash=new_password,
            key=new_key
        )
        # Delete token
        self.enterprise_member_repository.update_enterprise_member(**{
            "token_invitation": ""
        })

    def user_session_by_otp(self, user: User, password: str, method: str, otp_code: str, client_id: str = None,
                            device_identifier: str = None,
                            device_name: str = None, device_type: int = None, is_factor2: bool = False,
                            token_auth_value: str = None, secret: str = None,
                            ip: str = None, ua: str = None):
        # Check login block
        if user.login_block_until and user.login_block_until > now():
            wait = user.login_block_until - now()
            raise UserAuthBlockingEnterprisePolicyException(wait=wait)

        user_enterprises = self.enterprise_repository.list_user_enterprises(
            user_id=user.user_id, **{"status": E_MEMBER_STATUS_CONFIRMED}
        )
        user_enterprise_ids = [enterprise.enterprise_id for enterprise in user_enterprises]

        # Login failed
        if self.auth_repository.check_master_password(user=user, raw_password=password) is False:
            if user_enterprise_ids:
                BackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                    "enterprise_ids": user_enterprise_ids, "user_id": user.user_id, "acting_user_id": user.user_id,
                    "type": EVENT_USER_LOGIN_FAILED, "ip_address": ip
                })
                block_failed_login_policy = self.enterprise_policy_repository.get_block_failed_login_policy(
                    user_id=user.user_id
                )
                if block_failed_login_policy:
                    failed_login_attempts = block_failed_login_policy.failed_login_attempts
                    failed_login_duration = block_failed_login_policy.failed_login_duration
                    failed_login_block_time = block_failed_login_policy.failed_login_block_time
                    latest_request_login = user.last_request_login

                    user = self.user_repository.update_login_time_user(
                        user_id=user.user_id,
                        update_data={
                            "login_failed_attempts": user.login_failed_attempts + 1,
                            "last_request_login": now()
                        }
                    )
                    if user.login_failed_attempts >= failed_login_attempts and \
                            latest_request_login and now() - latest_request_login < failed_login_duration:
                        # Lock login of this member
                        user = self.user_repository.update_login_time_user(
                            user_id=user.user_id,
                            update_data={
                                "login_block_until": now() + failed_login_block_time
                            }
                        )
                        # Create block failed login event
                        BackgroundFactory.get_background(bg_name=BG_EVENT).run(
                            func_name="create_by_enterprise_ids", **{
                                "enterprise_ids": user_enterprise_ids, "user_id": user.user_id,
                                "type": EVENT_USER_BLOCK_LOGIN, "ip_address": ip
                            }
                        )
                        owner = self.enterprise_member_repository.get_primary_member(
                            enterprise_id=block_failed_login_policy.enterprise.enterprise_id
                        ).user.user_id
                        raise UserAuthBlockedEnterprisePolicyException(
                            failed_login_owner_email=block_failed_login_policy.failed_login_owner_email,
                            owner=owner,
                            lock_time="{} (UTC+00)".format(
                                datetime.utcfromtimestamp(now()).strftime('%H:%M:%S %d-%m-%Y')
                            ),
                            unlock_time="{} (UTC+00)".format(
                                datetime.utcfromtimestamp(user.login_block_until).strftime('%H:%M:%S %d-%m-%Y')
                            ),
                            ip=ip
                        )
            raise UserAuthFailedException

        if self.enterprise_repository.list_user_enterprises(user_id=user.user_id, **{"is_activated": False}):
            raise UserIsLockedByEnterpriseException
        if self.enterprise_member_repository.lock_login_account_belong_enterprise(user_id=user.user_id) is True:
            raise UserBelongEnterpriseException
        if [e for e in user_enterprises if e.locked is True]:
            raise UserEnterprisePlanExpiredException
        factor2_method = self.factor2_method_repository.get_factor2_method_by_method(
            user_id=user.user_id,
            method=method
        )
        if not factor2_method or not factor2_method.is_activate:
            raise UserFactor2IsNotActiveException

        # Check valid otp
        if self.factor2_method_repository.check_otp(user_id=user.user_id, method=method, otp_code=otp_code) is False:
            raise UserFactor2IsNotValidException
        else:
            # Update otp code
            if method == FA2_METHOD_MAIL_OTP:
                factor2_update_data = {
                    "activate_code": ""
                }
                self.factor2_method_repository.update_factor2_method(
                    factor2_method_id=factor2_method.factor2_method_id,
                    factor2_method_update_data=factor2_update_data
                )
        # Unblock login
        user = self.user_repository.update_login_time_user(user_id=user.user_id, update_data={
            "last_request_login": now(),
            "login_failed_attempts": 0,
            "login_block_until": now()
        })

        # Get sso token id from authentication token
        try:
            decoded_token = self.auth_repository.decode_token(token_auth_value, secret=secret)
        except AttributeError:
            decoded_token = None
        sso_token_id = decoded_token.get("sso_token_id") if decoded_token else None

        # Get current user plan, the sync device limit
        current_plan = self.get_current_plan(user=user)
        limit_sync_device = None if user_enterprise_ids else current_plan.pm_plan.sync_device
        # The list stores sso token id which will not be synchronized
        not_sync_sso_token_ids = []

        # First, check the device exists
        device_existed = self.device_repository.get_device_by_identifier(
            user_id=user.user_id, device_identifier=device_identifier
        )
        device_info = detect_device(ua_string=ua)
        device_obj = self.device_repository.retrieve_or_create(user_id=user.user_id, **{
            "client_id": client_id,
            "device_name": device_name,
            "device_type": device_type,
            "device_identifier": device_identifier,
            "os": device_info.get("os"),
            "browser": device_info.get("browser"),
            "scope": "api offline_access",
            "token_type": "Bearer",
            "refresh_token": secure_random_string(length=64, lower=False)
        })
        # If the device does not exist => New device => Create new one
        if not device_existed:
            all_devices = self.device_repository.list_user_devices(user_id=user.user_id)
            if limit_sync_device and len(all_devices) > limit_sync_device:
                old_devices = all_devices[limit_sync_device:]
                old_devices_ids = [old_device.device_id for old_device in old_devices]
                not_sync_sso_token_ids = self.device_access_token_repository.list_sso_token_ids(
                    device_ids=old_devices_ids
                )
                self.device_access_token_repository.remove_devices_access_tokens(device_ids=old_devices_ids)

        # Set last login
        device_obj = self.device_repository.set_last_login(device_id=device_obj.device_id, last_login=now())
        # Retrieve or create new access token
        access_token = self.device_access_token_repository.fetch_device_access_token(
            device=device_obj, renewal=True, sso_token_id=sso_token_id
        )
        result = {
            "refresh_token": device_obj.refresh_token,
            "access_token": access_token.access_token,
            "token_type": device_obj.token_type,
            "public_key": user.public_key,
            "private_key": user.private_key,
            "key": user.key,
            "kdf": user.kdf,
            "kdf_iterations": user.kdf_iterations,
            "not_sync": not_sync_sso_token_ids,
            "has_no_master_pw_item": not self.user_repository.has_master_pw_item(user_id=user.user_id),
            "is_super_admin": user.is_supper_admin
        }
        # Create event login successfully
        if user_enterprise_ids:
            BackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                "enterprise_ids": user_enterprise_ids, "user_id": user.user_id, "acting_user_id": user.user_id,
                "type": EVENT_USER_LOGIN, "ip_address": ip
            })

        return result
