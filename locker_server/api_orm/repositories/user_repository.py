from typing import Union, Dict, Optional, Tuple, List

import requests
import stripe
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Subquery, OuterRef, Count, Case, When, IntegerField, Value, Q, Sum, CharField, F, Min
from django.forms import FloatField

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models import UserScoreORM
from locker_server.api_orm.models.wrapper import get_user_model, get_enterprise_member_model, get_enterprise_model, \
    get_event_model, get_cipher_model, get_device_access_token_model, get_team_model, get_team_member_model, \
    get_device_model
from locker_server.api_orm.utils.revision_date import bump_account_revision_date
from locker_server.core.entities.user.user import User
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.caching.sync_cache import delete_sync_cache_data
from locker_server.shared.constants.account import ACCOUNT_TYPE_ENTERPRISE, ACCOUNT_TYPE_PERSONAL
from locker_server.shared.constants.ciphers import *
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED, E_MEMBER_ROLE_PRIMARY_ADMIN, \
    E_MEMBER_ROLE_ADMIN
from locker_server.shared.constants.event import EVENT_USER_BLOCK_LOGIN
from locker_server.shared.constants.members import MEMBER_ROLE_OWNER
from locker_server.shared.constants.policy import POLICY_TYPE_PASSWORDLESS, POLICY_TYPE_2FA
from locker_server.shared.constants.transactions import PAYMENT_STATUS_PAID
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY
from locker_server.shared.external_services.requester.retry_requester import requester
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.utils.app import now, start_end_month_current, datetime_from_ts

DeviceORM = get_device_model()
UserORM = get_user_model()
TeamORM = get_team_model()
TeamMemberORM = get_team_member_model()
DeviceAccessTokenORM = get_device_access_token_model()
CipherORM = get_cipher_model()
EnterpriseORM = get_enterprise_model()
EnterpriseMemberORM = get_enterprise_member_model()
EventORM = get_event_model()
ModelParser = get_model_parser()


class UserORMRepository(UserRepository):
    # ------------------------ List User resource ------------------- #
    def list_users(self, **filters) -> List[User]:
        users_orm = UserORM.objects.all()
        user_ids_param = filters.get("user_ids")
        emails_param = filters.get("emails")
        base32_secret_factor2_param = filters.get("base32_secret_factor2")
        if user_ids_param:
            users_orm = users_orm.filter(user_id__in=user_ids_param)
        if base32_secret_factor2_param:
            users_orm = users_orm.filter(base32_secret_factor2=base32_secret_factor2_param)
        if emails_param:
            users_orm = users_orm.filter(email__in=emails_param)

        return [
            ModelParser.user_parser().parse_user(user_orm=user_orm) for user_orm in users_orm
        ]

    def list_user_ids(self, **filter_params) -> List[int]:
        users_orm = UserORM.objects.all()
        activated_param = filter_params.get("activated")
        q_param = filter_params.get("q")
        user_ids_param = filter_params.get("user_ids")
        exclude_user_ids = filter_params.get("exclude_user_ids")
        emails_param = filter_params.get("emails")
        email_endswith_param = filter_params.get("email_endswith")

        if q_param:
            users_orm = users_orm.filter(
                Q(email__icontains=q_param.lower()) | Q(full_name__icontains=q_param.lower())
            )
        if user_ids_param is not None:
            users_orm = users_orm.filter(user_id__in=user_ids_param)
        if activated_param is not None:
            users_orm = users_orm.filter(activated=activated_param)
        if exclude_user_ids is not None:
            users_orm = users_orm.exclude(user_id__in=exclude_user_ids)
        if emails_param is not None:
            users_orm = users_orm.filter(email__in=emails_param)
        if email_endswith_param is not None:
            users_orm = users_orm.filter(email__endswith=email_endswith_param)
        return list(users_orm.values_list('user_id', flat=True))

    def list_user_emails(self, user_ids: List[int]) -> List[str]:
        return list(UserORM.objects.filter(user_id__in=user_ids).values_list('email', flat=True))

    def count_weak_cipher_password(self, user_ids: List[int] = None) -> int:
        if user_ids:
            users_orm = UserORM.objects.filter(
                user_id__in=user_ids
            )
        else:
            users_orm = UserORM.objects.all()
        weak_cipher_password_count = users_orm.annotate(
            weak_ciphers=Count(
                Case(
                    When(Q(ciphers__score__lte=1, ciphers__type=CIPHER_TYPE_LOGIN), then=Value(1)),
                    output_field=IntegerField()
                )
            )
        ).values('user_id', 'weak_ciphers').filter(weak_ciphers__gte=10).count()
        return weak_cipher_password_count

    def list_new_users(self) -> List[Dict]:
        current_time = now()
        devices = DeviceORM.objects.filter(user_id=OuterRef("user_id")).order_by('last_login')
        new_users = UserORM.objects.filter(
            activated=True,
            activated_date__lte=current_time, activated_date__gt=current_time - 86400
        ).annotate(
            first_device_client_id=Subquery(devices.values('client_id')[:1], output_field=CharField()),
            first_device_name=Subquery(devices.values('device_name')[:1], output_field=CharField()),
        ).order_by('activated_date').values('user_id', 'first_device_client_id', 'first_device_name')
        return new_users

    def count_users(self, **filters) -> int:
        users_orm = UserORM.objects.all()
        activated_param = filters.get("activated")
        if activated_param is not None:
            if activated_param == "1" or activated_param is True:
                users_orm = users_orm.filter(activated=True)
            elif activated_param == "0" or activated_param is False:
                users_orm = users_orm.filter(activated=False)
        return users_orm.count()

    def list_user_ids_tutorial_reminder(self, duration_unit: int) -> Dict:
        current_time = now()

        users_orm = UserORM.objects.filter()
        enterprise_user_ids = EnterpriseMemberORM.objects.filter(
            status=E_MEMBER_STATUS_CONFIRMED
        ).values_list('user_id', flat=True)
        exclude_enterprise_users_orm = users_orm.exclude(user_id__in=enterprise_user_ids)

        # 3 days
        user_ids_3days = users_orm.filter(
            creation_date__range=(current_time - 3 * duration_unit, current_time - 2 * duration_unit)
        ).values_list('user_id', flat=True)

        # 5 days
        user_ids_5days = users_orm.filter(
            creation_date__range=(current_time - 5 * duration_unit, current_time - 4 * duration_unit)
        ).values_list('user_id', flat=True)

        # 7 days
        user_ids_7days = users_orm.filter(
            creation_date__range=(current_time - 7 * duration_unit, current_time - 6 * duration_unit)
        ).values_list('user_id', flat=True)

        # 13 days
        user_ids_13days = exclude_enterprise_users_orm.exclude(
            pm_user_plan__start_period__isnull=True
        ).exclude(
            pm_user_plan__end_period__isnull=True
        ).annotate(
            plan_period=F('pm_user_plan__end_period') - F('pm_user_plan__start_period'),
            remain_period=F('pm_user_plan__end_period') - current_time
        ).filter(
            plan_period__lte=15 * duration_unit, remain_period__lte=duration_unit, remain_period__gte=0
        ).values_list('user_id', flat=True)

        # 20 days
        user_ids_20days = exclude_enterprise_users_orm.filter(
            creation_date__range=(current_time - 20 * duration_unit, current_time - 19 * duration_unit)
        ).values_list('user_id', flat=True)
        return {
            "user_ids_3days": list(user_ids_3days),
            "user_ids_5days": list(user_ids_5days),
            "user_ids_7days": list(user_ids_7days),
            "user_ids_13days": list(user_ids_13days),
            "user_ids_20days": list(user_ids_20days),
        }

    # ------------------------ Get User resource --------------------- #
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        try:
            user_orm = UserORM.objects.get(user_id=user_id)
            return ModelParser.user_parser().parse_user(user_orm=user_orm)
        except UserORM.DoesNotExist:
            return None

    def get_user_type(self, user_id: int) -> str:
        if EnterpriseMemberORM.objects.filter(user_id=user_id, status=E_MEMBER_STATUS_CONFIRMED).exists():
            return ACCOUNT_TYPE_ENTERPRISE
        return ACCOUNT_TYPE_PERSONAL

    def is_in_enterprise(self, user_id: int) -> bool:
        return EnterpriseMemberORM.objects.filter(user_id=user_id).exists()

    def is_require_passwordless(self, user_id: int,
                                require_enterprise_member_status: str = E_MEMBER_STATUS_CONFIRMED) -> bool:
        if require_enterprise_member_status:
            e_member_orm = EnterpriseMemberORM.objects.filter(
                user_id=user_id, status=require_enterprise_member_status, enterprise__locked=False
            ).first()
        else:
            e_member_orm = EnterpriseMemberORM.objects.filter(
                user_id=user_id, enterprise__locked=False
            ).first()
        e_passwordless_policy = False
        if e_member_orm:
            enterprise_orm = e_member_orm.enterprise
            policy_orm = enterprise_orm.policies.filter(policy_type=POLICY_TYPE_PASSWORDLESS, enabled=True).first()
            if policy_orm:
                e_passwordless_policy = policy_orm.policy_passwordless.only_allow_passwordless
        return e_passwordless_policy

    def is_block_by_2fa_policy(self, user_id: int, is_factor2: bool) -> bool:
        if is_factor2 is True:
            return False
        user_enterprises_orm = EnterpriseORM.objects.filter(
            enterprise_members__user_id=user_id, enterprise_members__status=E_MEMBER_STATUS_CONFIRMED
        )
        for enterprise_orm in user_enterprises_orm:
            policy_orm = enterprise_orm.policies.filter(policy_type=POLICY_TYPE_2FA, enabled=True).first()
            if not policy_orm:
                continue
            try:
                member_role = enterprise_orm.enterprise_members.get(user_id=user_id).role_id
            except ObjectDoesNotExist:
                continue
            only_admin = policy_orm.policy_2fa.only_admin
            if only_admin is False or \
                    (only_admin and member_role in [E_MEMBER_ROLE_ADMIN, E_MEMBER_ROLE_PRIMARY_ADMIN]):
                return True
        return False

    def count_failed_login_event(self, user_id: int) -> int:
        start_ts, end_ts = start_end_month_current()
        failed_login = EventORM.objects.filter(
            type=EVENT_USER_BLOCK_LOGIN, user_id=user_id,
            creation_date__gte=start_ts, creation_date__lte=end_ts
        ).count()
        return failed_login

    def has_master_pw_item(self, user_id: int) -> bool:
        return CipherORM.objects.filter(created_by_id=user_id, type=CIPHER_TYPE_MASTER_PASSWORD).exists()

    def get_from_cystack_id(self, user_id: int) -> Dict:
        try:
            user_orm = UserORM.objects.get(user_id=user_id)
            return user_orm.get_from_cystack_id()
        except UserORM.DoesNotExist:
            return {}

    def get_user_by_email(self, email: str) -> Optional[User]:
        try:
            user_orm = UserORM.objects.get(email=email)
            return ModelParser.user_parser().parse_user(user_orm=user_orm)
        except UserORM.DoesNotExist:
            return None

    def get_user_cipher_overview(self, user_id: int) -> Dict:
        try:
            user_orm = UserORM.objects.get(user_id=user_id)
        except UserORM.DoesNotExist:
            return {}
        cipher_overview = user_orm.created_ciphers.filter(
            type=CIPHER_TYPE_LOGIN, deleted_date__isnull=True
        ).aggregate(
            cipher0=Sum(
                Case(When(score=0, then=Value(1)), default=0), output_field=IntegerField()
            ),
            cipher1=Sum(
                Case(When(score=1, then=Value(1)), default=0), output_field=IntegerField()
            ),
            cipher2=Sum(
                Case(When(score=2, then=Value(1)), default=0), output_field=IntegerField()
            ),
            cipher3=Sum(
                Case(When(score=3, then=Value(1)), default=0), output_field=IntegerField()
            ),
            cipher4=Sum(
                Case(When(score=4, then=Value(1)), default=0), output_field=IntegerField()
            )
        )
        return cipher_overview

    def get_customer_data(self, user: User, token_card=None, id_card=None) -> Dict:
        # Get customer data from stripe customer
        if not token_card:
            cystack_user_data = self.get_from_cystack_id(user_id=user.user_id)
            stripe_customer_id = cystack_user_data.get("stripe_customer_id")
            if stripe_customer_id:
                customer_stripe = stripe.Customer.retrieve(stripe_customer_id)
                try:
                    sources = customer_stripe.sources.data
                    data_customer_stripe = {}
                    if id_card:
                        for source in sources:
                            if source.get("id") == id_card:
                                data_customer_stripe = source
                                break
                        # Retrieve from Payment Methods:
                        if not data_customer_stripe:
                            payment_methods = stripe.PaymentMethod.list(
                                customer=stripe_customer_id, type="card"
                            ).get("data", [])
                            for payment_method in payment_methods:
                                if payment_method.get("id") == id_card:
                                    data_customer_stripe = self._get_data_customer_stripe_from_pm(payment_method)
                    else:
                        data_customer_stripe = customer_stripe.sources.data[0]
                except:
                    CyLog.info(**{"message": "Can not get stripe customer: {}".format(stripe_customer_id)})
                    data_customer_stripe = {}
                customer_data = {
                    "full_name": data_customer_stripe.get("name"),
                    "address": data_customer_stripe.get("address_line1", ""),
                    "country": data_customer_stripe.get("country", None),
                    "last4": data_customer_stripe.get("last4"),
                    "organization": customer_stripe.get("metadata").get("company", ""),
                    "city": data_customer_stripe.get("address_city", ""),
                    "state": data_customer_stripe.get("address_state", ""),
                    "postal_code": data_customer_stripe.get("address_zip", ""),
                    "brand": data_customer_stripe.get("brand", "")
                }
            else:
                customer_data = {
                    "full_name": cystack_user_data.get("full_name"),
                    "address": cystack_user_data.get("address", ""),
                    "country": cystack_user_data.get("country", None),
                    "last4": cystack_user_data.get("last4"),
                    "organization": cystack_user_data.get("organization"),
                    "city": cystack_user_data.get("city", ""),
                    "state": cystack_user_data.get("state", ""),
                    "postal_code": cystack_user_data.get("postal_code", ""),
                    "brand": cystack_user_data.get("brand", "")
                }
        # Else, get from specific card
        else:
            card = stripe.Token.retrieve(token_card).get("card")
            customer_data = {
                "full_name": card.get("name"),
                "address": card.get("address_line1", ""),
                "country": card.get("address_country", None),
                "last4": card.get("last4"),
                "organization": card.get("organization"),
                "city": card.get("address_city", ""),
                "state": card.get("address_state", ""),
                "postal_code": card.get("address_zip", ""),
                "brand": card.get("brand", "")
            }
        return customer_data

    @staticmethod
    def _get_data_customer_stripe_from_pm(payment_method):
        data_customer_stripe = {
            "name": payment_method.get("billing_details", {}).get("name"),
            "address_line1": payment_method.get("billing_details", {}).get("address", {}).get("line1") or "",
            "country": payment_method.get("billing_details", {}).get("address", {}).get("country") or "",
            "address_city": payment_method.get("billing_details", {}).get("address", {}).get("city") or "",
            "address_state": payment_method.get("billing_details", {}).get("address", {}).get("state") or "",
            "address_zip": payment_method.get("billing_details", {}).get("address", {}).get("postal_code") or "",
            "brand": payment_method.get("card", {}).get("brand"),
            "last4": payment_method.get("card", {}).get("last4"),
            "organization": payment_method.get("metadata").get("company", ""),
        }

        return data_customer_stripe

    @staticmethod
    def _retrieve_or_create_user_score_orm(user_orm):
        try:
            return user_orm.user_score
        except AttributeError:
            return UserScoreORM.objects.get_or_create(user_id=user_orm.user_id, defaults={"user_id": user_orm.user_id})

    def allow_create_enterprise_user(self) -> bool:
        return not UserORM.objects.count() >= 1

    def check_exist(self) -> bool:
        return UserORM.objects.filter().exists()

    # ------------------------ Create User resource --------------------- #
    def retrieve_or_create_by_id(self, user_id, creation_date=None) -> Tuple[User, bool]:
        creation_date = now() if not creation_date else float(creation_date)
        user_orm, is_created = UserORM.objects.get_or_create(user_id=user_id, defaults={
            "user_id": user_id,
            "creation_date": creation_date
        })
        return ModelParser.user_parser().parse_user(user_orm=user_orm), is_created

    def retrieve_or_create_by_email(self, email: str, creation_date=None) -> Tuple[User, bool]:
        creation_date = now() if not creation_date else float(creation_date)
        user_orm, is_created = UserORM.objects.get_or_create(email=email, defaults={
            "email": email,
            "full_name": email,
            "creation_date": creation_date
        })
        return ModelParser.user_parser().parse_user(user_orm=user_orm), is_created

    # ------------------------ Update User resource --------------------- #
    def update_user(self, user_id: int, user_update_data) -> Optional[User]:
        try:
            user_orm = UserORM.objects.get(user_id=user_id)
        except UserORM.DoesNotExist:
            return None
        scores = user_update_data.get("scores", {})
        onboarding_process = user_update_data.get("onboarding_process")
        user_orm.timeout = user_update_data.get("timeout", user_orm.timeout)
        user_orm.timeout_action = user_update_data.get("timeout_action", user_orm.timeout_action)

        user_orm.kdf = user_update_data.get("kdf", user_orm.kdf)
        user_orm.kdf_iterations = user_update_data.get("kdf_iterations", user_orm.kdf_iterations)
        user_orm.key = user_update_data.get("key", user_orm.key)
        user_orm.public_key = user_update_data.get("public_key", user_orm.public_key)
        user_orm.private_key = user_update_data.get("private_key", user_orm.private_key)
        user_orm.master_password_hint = user_update_data.get("master_password_hint", user_orm.master_password_hint)
        user_orm.master_password_score = user_update_data.get("master_password_score", user_orm.master_password_score)
        user_orm.api_key = user_update_data.get("api_key", user_orm.api_key)
        user_orm.use_relay_subdomain = user_update_data.get("use_relay_subdomain", user_orm.use_relay_subdomain)
        user_orm.activated = user_update_data.get("activated", user_orm.activated)
        user_orm.activated_date = user_update_data.get("activated_date", user_orm.activated_date)
        user_orm.revision_date = user_update_data.get("revision_date", user_orm.revision_date)
        user_orm.delete_account_date = user_update_data.get("delete_account_date", user_orm.delete_account_date)
        user_orm.first_login = user_update_data.get("first_login", user_orm.first_login)
        user_orm.saas_source = user_update_data.get("saas_source", user_orm.saas_source)

        user_orm.full_name = user_update_data.get("full_name", user_orm.full_name)
        user_orm.language = user_update_data.get("language", user_orm.language)

        user_orm.base32_secret_factor2 = user_update_data.get("base32_secret_factor2", user_orm.base32_secret_factor2)

        user_orm.is_leaked = user_update_data.get("is_leaked", user_orm.is_leaked)

        user_orm.is_supper_admin = user_update_data.get("is_supper_admin", False)
        
        if user_update_data.get("master_password_hash"):
            user_orm.set_master_password(raw_password=user_update_data.get("master_password_hash"))

        if scores:
            user_score_orm = self._retrieve_or_create_user_score_orm(user_orm=user_orm)
            user_score_orm.cipher0 = scores.get("0", user_score_orm.cipher0)
            user_score_orm.cipher1 = scores.get("1", user_score_orm.cipher1)
            user_score_orm.cipher2 = scores.get("2", user_score_orm.cipher2)
            user_score_orm.cipher3 = scores.get("3", user_score_orm.cipher3)
            user_score_orm.cipher4 = scores.get("4", user_score_orm.cipher4)
            user_score_orm.cipher5 = scores.get("5", user_score_orm.cipher5)
            user_score_orm.cipher6 = scores.get("6", user_score_orm.cipher6)
            user_score_orm.cipher7 = scores.get("7", user_score_orm.cipher7)
            user_score_orm.save()
        if onboarding_process:
            user_orm.onboarding_process = onboarding_process
        user_orm.save()
        return ModelParser.user_parser().parse_user(user_orm=user_orm)

    def update_login_time_user(self, user_id: int, update_data) -> Optional[User]:
        try:
            user_orm = UserORM.objects.get(user_id=user_id)
        except UserORM.DoesNotExist:
            return None
        user_orm.login_failed_attempts = update_data.get("login_failed_attempts", user_orm.login_failed_attempts)
        user_orm.last_request_login = update_data.get("last_request_login", user_orm.last_request_login)
        user_orm.login_block_until = update_data.get("login_block_until", user_orm.login_block_until)
        user_orm.save()
        return ModelParser.user_parser().parse_user(user_orm=user_orm)

    def update_passwordless_cred(self, user_id: int, fd_credential_id: str, fd_random: str) -> User:
        try:
            user_orm = UserORM.objects.get(user_id=user_id)
        except UserORM.DoesNotExist:
            return None
        user_orm.fd_credential_id = fd_credential_id
        user_orm.fd_random = fd_random
        user_orm.save()
        return ModelParser.user_parser().parse_user(user_orm=user_orm)

    def change_master_password(self, user: User, new_master_password_hash: str, new_master_password_hint: str = None,
                               key: str = None, score=None, login_method: str = None):
        try:
            user_orm = UserORM.objects.get(user_id=user.user_id)
        except UserORM.DoesNotExist:
            return None
        user_orm.set_master_password(new_master_password_hash)
        user_orm.key = key or user_orm.key
        user_orm.master_password_hint = new_master_password_hint or user.master_password_hint
        if score:
            user_orm.master_password_score = score
        if login_method:
            user_orm.login_method = login_method
        user_orm.save()

    def update_user_factor2(self, user_id: int, is_factor2: bool) -> Optional[User]:
        try:
            user_orm = UserORM.objects.get(user_id=user_id)
        except UserORM.DoesNotExist:
            return None
        user_orm.is_factor2 = is_factor2
        user_orm.save()
        return ModelParser.user_parser().parse_user(user_orm=user_orm)

    # ------------------------ Delete User resource --------------------- #
    def purge_account(self, user: User):
        try:
            user_orm = UserORM.objects.get(user_id=user.user_id)
        except UserORM.DoesNotExist:
            return None
        # Delete all their folders
        user_orm.folders.all().delete()
        # Delete all personal ciphers
        user_orm.ciphers.all().delete()
        # Delete all team ciphers
        owners_orm = user_orm.team_members.filter(role_id=MEMBER_ROLE_OWNER, team__personal_share=True)
        team_ids = owners_orm.values_list('team_id', flat=True)
        other_members_orm = TeamMemberORM.objects.filter(
            team_id__in=team_ids, is_primary=False, team_id=OuterRef('team_id')
        ).order_by('id')
        shared_ciphers_orm = CipherORM.objects.filter(team_id__in=team_ids)
        shared_ciphers_members_orm = shared_ciphers_orm.annotate(
            shared_member=Subquery(other_members_orm.values('user_id')[:1])
        ).exclude(shared_member__isnull=True).values('id', 'shared_member')
        shared_ciphers_orm.delete()
        TeamORM.objects.filter(id__in=team_ids).delete()
        # Bump revision date
        bump_account_revision_date(user=user_orm)
        return list(shared_ciphers_members_orm)

    def delete_account(self, user: User):
        try:
            user_orm = UserORM.objects.get(user_id=user.user_id)
        except UserORM.DoesNotExist:
            return None

        # Then, delete related data: device sessions, folders, ciphers
        user_orm.user_devices.all().delete()
        user_orm.folders.all().delete()
        user_orm.ciphers.all().delete()
        user_orm.exclude_domains.all().delete()

        # We only soft-delete this user. The plan of user is still available (but it will be canceled at the end period)
        # If user registers again, the data is deleted but the plan is still available.
        # User must restart the plan manually. Otherwise, the plan is still removed at the end period
        user_orm.revision_date = None
        user_orm.activated = False
        user_orm.account_revision_date = None
        user_orm.delete_account_date = now()
        user_orm.master_password = None
        user_orm.master_password_hint = None
        user_orm.master_password_score = 0
        user_orm.security_stamp = None
        user_orm.key = None
        user_orm.public_key = None
        user_orm.private_key = None
        user_orm.save()

    def revoke_all_sessions(self, user: User, exclude_sso_token_ids=None) -> User:
        device_access_tokens = DeviceAccessTokenORM.objects.filter(device__user_id=user.user_id)
        if exclude_sso_token_ids:
            device_access_tokens = device_access_tokens.exclude(sso_token_id__in=exclude_sso_token_ids)
        device_access_tokens.delete()
        return user

    def delete_sync_cache_data(self, user_id: int):
        delete_sync_cache_data(user_id=user_id)
