import ast
import uuid
from typing import Dict

import stripe
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from core.repositories import IUserRepository
from shared.constants.ciphers import *
from shared.constants.members import *
from shared.constants.transactions import *
from shared.log.cylog import CyLog
from shared.utils.app import now
from cystack_models.models.users.users import User
from cystack_models.models.users.device_access_tokens import DeviceAccessToken
from cystack_models.models.members.team_members import TeamMember
from cystack_models.models.user_plans.pm_plans import PMPlan


class UserRepository(IUserRepository):
    def retrieve_or_create_by_id(self, user_id, creation_date=None) -> User:
        try:
            user = self.get_by_id(user_id=user_id)
        except User.DoesNotExist:
            creation_date = now() if not creation_date else float(creation_date)
            user = User(user_id=user_id, creation_date=creation_date)
            user.save()
            # Create default team for this new user
            self.get_default_team(user=user, create_if_not_exist=True)
            # Create default plan for this user
            self.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        return user

    def upgrade_member_family_plan(self, user: User):
        # Upgrade plan if the user is a family member
        from cystack_models.models.user_plans.pm_user_plan_family import PMUserPlanFamily
        email = user.get_from_cystack_id().get("email")
        if not email:
            return user
        family_invitations = PMUserPlanFamily.objects.filter(email=email).order_by('created_time')
        family_invitation = family_invitations.first()
        if family_invitation:
            root_user_plan = family_invitation.root_user_plan
            self.update_plan(
                user=user, plan_type_alias=PLAN_TYPE_PM_PREMIUM, duration=root_user_plan.duration,
                scope=settings.SCOPE_PWD_MANAGER, **{
                    "start_period": root_user_plan.start_period,
                    "end_period": root_user_plan.end_period,
                    "number_members": 1
                }
            )
            family_invitations.update(user=user, email=None)
        return user

    def invitations_confirm(self, user):
        email = user.get_from_cystack_id().get("email")
        if not email:
            return user
        invitations = TeamMember.objects.filter(email=email, team__key__isnull=False, status=PM_MEMBER_STATUS_INVITED)
        for invitation in invitations:
            team = invitation.team
            # Check max number members
            primary_user = team.team_members.get(is_primary=True).user
            primary_plan = self.get_current_plan(user=primary_user, scope=settings.SCOPE_PWD_MANAGER)
            plan_obj = primary_plan.get_plan_obj()
            if plan_obj.allow_personal_share() or plan_obj.is_team_plan or plan_obj.is_family_plan:
                if plan_obj.is_team_plan:
                    current_total_members = team.team_members.all().count()
                    max_allow_members = primary_plan.get_max_allow_members()
                    if max_allow_members and current_total_members + 1 > max_allow_members:
                        continue
                invitation.email = None
                invitation.token_invitation = None
                invitation.user = user
                invitation.save()
        return user

    def get_by_id(self, user_id) -> User:
        return User.objects.get(user_id=user_id)

    def get_default_team(self, user: User, create_if_not_exist=False):
        try:
            default_team = user.team_members.get(is_default=True).team
        except ObjectDoesNotExist:
            if create_if_not_exist is False:
                return None
            default_team = self._create_default_team(user)
        except MultipleObjectsReturned:
            # If user has multiple default teams because of concurrent requests ="> Delete others
            multiple_default_teams = user.team_members.filter(is_default=True).order_by('-created_time')
            # Set first team as default
            default_team = multiple_default_teams.first().team
            multiple_default_teams.exclude(team_id=default_team.id).delete()

        return default_team

    def _create_default_team(self, user: User):
        from cystack_models.models.teams.teams import Team
        from cystack_models.models.members.member_roles import MemberRole
        team_name = user.get_from_cystack_id().get("full_name", "My Vault")
        default_group = Team.create(**{
            "members": [{
                "user": user,
                "role": MemberRole.objects.get(name=MEMBER_ROLE_OWNER),
                "is_default": True,
                "is_primary": True
            }],
            "name": team_name,
            "description": ""
        })
        return default_group

    def get_by_email(self, email) -> User:
        pass

    def get_kdf_information(self, user: User) -> Dict:
        return {
            "kdf": user.kdf,
            "kdf_iterations": user.kdf_iterations
        }

    def get_many_by_ids(self, user_ids: list):
        return User.objects.filter(user_id__in=user_ids)

    def is_activated(self, user: User) -> bool:
        return user.activated

    def retrieve_or_create_user_score(self, user: User):
        try:
            return user.user_score
        except AttributeError:
            from cystack_models.models.users.user_score import UserScore
            return UserScore.create(user=user)

    def get_personal_team_plans(self, user: User, personal_share=False):
        user_team_ids = user.team_members.filter(
            team__key__isnull=False, status=PM_MEMBER_STATUS_CONFIRMED,
            team__personal_share=personal_share
        ).values_list('team_id', flat=True)
        primary_owners = TeamMember.objects.filter(team_id__in=list(user_team_ids)).filter(
            role_id=MEMBER_ROLE_OWNER
        ).values_list('user_id', flat=True)
        from cystack_models.models.user_plans.pm_user_plan import PMUserPlan
        personal_team_plans = PMUserPlan.objects.filter(
            user_id__in=list(primary_owners) + [user.user_id]
        ).select_related('pm_plan')
        return personal_team_plans

    def get_max_allow_cipher_type(self, user: User, personal_share=False):
        personal_team_plans = self.get_personal_team_plans(user=user, personal_share=personal_share)
        cipher_limits = PMPlan.objects.filter(id__in=personal_team_plans.values_list('pm_plan_id')).values(
            'limit_password', 'limit_secure_note', 'limit_identity', 'limit_payment_card', 'limit_crypto_asset'
        )
        limit_password = [cipher_limit.get("limit_password") for cipher_limit in cipher_limits]
        limit_secure_note = [cipher_limit.get("limit_secure_note") for cipher_limit in cipher_limits]
        limit_identity = [cipher_limit.get("limit_identity") for cipher_limit in cipher_limits]
        limit_payment_card = [cipher_limit.get("limit_payment_card") for cipher_limit in cipher_limits]
        limit_crypto_asset = [cipher_limit.get("limit_crypto_asset") for cipher_limit in cipher_limits]
        return {
            CIPHER_TYPE_LOGIN: None if None in limit_password else max(limit_password),
            CIPHER_TYPE_NOTE: None if None in limit_secure_note else max(limit_secure_note),
            CIPHER_TYPE_IDENTITY: None if None in limit_identity else max(limit_identity),
            CIPHER_TYPE_CARD: None if None in limit_payment_card else max(limit_payment_card),
            CIPHER_TYPE_CRYPTO_ACCOUNT: None if None in limit_crypto_asset else max(limit_crypto_asset),
            CIPHER_TYPE_CRYPTO_WALLET: None if None in limit_crypto_asset else max(limit_crypto_asset),
            CIPHER_TYPE_TOTP: None
        }

    def get_mobile_user_plan(self, pm_mobile_subscription):
        from cystack_models.models.user_plans.pm_user_plan import PMUserPlan
        try:
            user_plan = PMUserPlan.objects.get(pm_mobile_subscription=pm_mobile_subscription)
            return user_plan
        except PMUserPlan.DoesNotExist:
            return None

    def get_current_plan(self, user: User, scope=None):
        try:
            return user.pm_user_plan
        except (ValueError, AttributeError):
            from cystack_models.models.user_plans.pm_user_plan import PMUserPlan
            return PMUserPlan.update_or_create(user)

    def update_plan(self, user: User, plan_type_alias: str, duration=DURATION_MONTHLY,
                    scope=settings.SCOPE_PWD_MANAGER, **kwargs):
        """
        Update the Password Manager plan of this user
        :param user: (obj) User object
        :param plan_type_alias: (str) Name of Pm Plan
        :param duration: monthly/half_yearly/yearly
        :param scope:
        :param kwargs:
        :return:
        """
        start_period = kwargs.get("start_period")
        end_period = kwargs.get("end_period")
        number_members = kwargs.get("number_members", 1)
        promo_code = kwargs.get("promo_code")
        if start_period is None and plan_type_alias != PLAN_TYPE_PM_FREE:
            start_period = now(return_float=True)
        if end_period is None and plan_type_alias != PLAN_TYPE_PM_FREE:
            if duration == DURATION_HALF_YEARLY:
                end_period = 6 * 30 * 86400 + start_period
            elif duration == DURATION_YEARLY:
                end_period = 365 * 86400 + start_period
            else:
                end_period = 30 * 86400 + start_period
        pm_user_plan = self.get_current_plan(user=user, scope=scope)
        pm_user_plan.pm_plan = PMPlan.objects.get(alias=plan_type_alias)
        pm_user_plan.duration = duration
        pm_user_plan.start_period = start_period
        pm_user_plan.end_period = end_period
        pm_user_plan.number_members = number_members
        pm_user_plan.promo_code = promo_code
        pm_user_plan.cancel_at_period_end = False
        pm_user_plan.save()

        if plan_type_alias == PLAN_TYPE_PM_FREE:
            pm_user_plan.start_period = None
            pm_user_plan.end_period = None
            # Lock all primary teams
            primary_owners = user.team_members.filter(is_primary=True, key__isnull=False)
            for primary_owner in primary_owners:
                primary_owner.team.lock_pm_team(lock=True)
            # Downgrade all family members
            self.__cancel_family_members(pm_user_plan)
        else:
            # Unlock all their PM teams
            primary_owners = user.team_members.filter(is_primary=True, key__isnull=False)
            for primary_owner in primary_owners:
                primary_owner.team.lock_pm_team(lock=False)

        pm_user_plan.save()

        # Update plan rule here
        # If the plan is team plan => Create vault org
        pm_plan = pm_user_plan.get_plan_obj()
        if pm_plan.is_team_plan:
            # Leave other family plans if user is a member
            user.pm_plan_family.all().delete()
            # Create Vault Org here
            default_collection_name = kwargs.get("collection_name")
            key = kwargs.get("key")
            self.__create_vault_team(user=user, key=key, collection_name=default_collection_name)

        # If the plan is family plan => Upgrade plan for the user
        if pm_plan.is_family_plan:
            # Leave other family plans if user is a member
            user.pm_plan_family.all().delete()
            # Create family members
            family_members = kwargs.get("family_members", [])
            self.__create_family_members(pm_user_plan=pm_user_plan, family_members=family_members)

        return pm_user_plan

    def cancel_plan(self, user: User, scope=None):
        current_plan = self.get_current_plan(user=user, scope=scope)
        pm_plan_alias = current_plan.get_plan_type_alias()
        if pm_plan_alias == PLAN_TYPE_PM_FREE:
            return
        stripe_subscription = current_plan.get_stripe_subscription()
        if stripe_subscription:
            payment_method = PAYMENT_METHOD_CARD
        else:
            payment_method = PAYMENT_METHOD_WALLET

        from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory
        end_time = PaymentMethodFactory.get_method(
            user=user, scope=settings.SCOPE_PWD_MANAGER, payment_method=payment_method
        ).cancel_recurring_subscription()
        return end_time

    def add_to_family_sharing(self, family_user_plan, user_id: int = None, email: str = None):
        if user_id and family_user_plan.pm_plan_family.filter(user_id=user_id).exists():
            return family_user_plan
        if email and family_user_plan.pm_plan_family.filter(email=email).exists():
            return family_user_plan

        # Retrieve user
        try:
            family_member_user = User.objects.get(user_id=user_id, activated=True)
        except User.DoesNotExist:
            family_member_user = None

        if family_member_user:

            # If the member user has a plan => Cancel this plan if this plan is not a team plan
            current_member_plan = self.get_current_plan(user=family_member_user, scope=settings.SCOPE_PWD_MANAGER)
            if current_member_plan.get_plan_obj().is_family_plan is False and \
                    current_member_plan.get_plan_obj().is_team_plan is False:

                # Add to family plan
                family_user_plan.pm_plan_family.model.create(family_user_plan, family_member_user, None)

                # Cancel current plan
                from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory
                PaymentMethodFactory.get_method(
                    user=family_member_user, scope=settings.SCOPE_PWD_MANAGER,
                    payment_method=current_member_plan.get_default_payment_method()
                ).cancel_immediately_recurring_subscription()
                # Then upgrade to Premium
                self.update_plan(
                    user=family_member_user, plan_type_alias=PLAN_TYPE_PM_PREMIUM, duration=family_user_plan.duration,
                    scope=settings.SCOPE_PWD_MANAGER, **{
                        "start_period": family_user_plan.start_period,
                        "end_period": family_user_plan.end_period,
                        "number_members": 1
                    }
                )
        else:
            family_user_plan.pm_plan_family.model.create(family_user_plan, None, email)
        return family_user_plan

    def __create_vault_team(self, user, key, collection_name):
        # Retrieve or create default team
        team = self.get_default_team(user=user, create_if_not_exist=True)
        # if this team was created => Return this team
        if team.key:
            return team
        # Save owner key for this team
        team.key = key
        team.revision_date = now()
        team.save()
        # Create default collection for this team
        team.collections.model.create(team, **{"name": collection_name, "is_default": True})
        # Save owner key for primary member
        primary_member = team.team_members.get(user=user)
        primary_member.key = key
        primary_member.external_id = uuid.uuid4()
        primary_member.save()

    def __create_family_members(self, pm_user_plan, family_members):
        plan_obj = pm_user_plan.get_plan_obj()
        if plan_obj.is_family_plan is False:
            return pm_user_plan
        # If this pm user plan has family members => Not create
        if pm_user_plan.pm_plan_family.exists():
            family_members = pm_user_plan.pm_plan_family.all()
            for family_member in family_members:
                # Update period for the family members
                if family_member.user:
                    self.update_plan(
                        user=family_member.user, plan_type_alias=PLAN_TYPE_PM_PREMIUM, duration=pm_user_plan.duration,
                        scope=settings.SCOPE_PWD_MANAGER, **{
                            "start_period": pm_user_plan.start_period,
                            "end_period": pm_user_plan.end_period,
                            "number_members": 1
                        }
                    )
            return pm_user_plan

        family_members = ast.literal_eval(str(family_members))
        for family_member in family_members:
            email = family_member.get("email")
            user_id = family_member.get("user_id")
            self.add_to_family_sharing(family_user_plan=pm_user_plan, user_id=user_id, email=email)
            # try:
            #     family_member_user = User.objects.get(user_id=user_id, activated=True)
            # except User.DoesNotExist:
            #     family_member_user = None
            # if family_member_user:
            #     pm_user_plan.pm_plan_family.model.create(pm_user_plan, family_member_user, None)
            #
            #     # If the member user has a plan => Cancel this plan if this plan is not a team plan
            #     current_member_plan = self.get_current_plan(user=family_member_user, scope=settings.SCOPE_PWD_MANAGER)
            #     if current_member_plan.get_plan_obj().is_family_plan is False and \
            #             current_member_plan.get_plan_obj().is_team_plan is False:
            #         from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory
            #         PaymentMethodFactory.get_method(
            #             user=family_member_user, scope=settings.SCOPE_PWD_MANAGER,
            #             payment_method=current_member_plan.get_default_payment_method()
            #         ).cancel_immediately_recurring_subscription()
            #         # Then upgrade to Premium
            #         self.update_plan(
            #             user=family_member_user, plan_type_alias=PLAN_TYPE_PM_PREMIUM, duration=pm_user_plan.duration,
            #             scope=settings.SCOPE_PWD_MANAGER, **{
            #                 "start_period": pm_user_plan.start_period,
            #                 "end_period": pm_user_plan.end_period,
            #                 "number_members": 1
            #             }
            #         )
            # else:
            #     pm_user_plan.pm_plan_family.model.create(pm_user_plan, None, email)
        return pm_user_plan

    def __cancel_family_members(self, pm_user_plan):
        family_members = pm_user_plan.pm_plan_family.all()
        for family_member in family_members:
            if family_member.user:
                self.update_plan(
                    user=family_member.user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=settings.SCOPE_PWD_MANAGER
                )
            family_member.delete()

    def get_max_allow_member_pm_team(self, user: User, scope=None):
        return self.get_current_plan(user, scope=scope).get_max_allow_members()

    def get_customer_data(self, user: User, token_card=None, id_card=None):
        # Get customer data from stripe customer
        if not token_card:
            cystack_user_data = user.get_from_cystack_id()
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
                    "postal_code": data_customer_stripe.get("address_zip", "")
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
                    "postal_code": cystack_user_data.get("postal_code", "")
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
                "postal_code": card.get("address_zip", "")
            }
        return customer_data

    def get_list_invitations(self, user: User, personal_share=False):
        member_invitations = user.team_members.filter(
            status__in=[PM_MEMBER_STATUS_INVITED, PM_MEMBER_STATUS_ACCEPTED], team__personal_share=personal_share
        ).select_related('team').order_by('access_time')
        return member_invitations

    def delete_account(self, user: User):
        # Cancel current plan at the end period
        self.cancel_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        # Then, delete related data: device sessions, folders, ciphers
        user.user_devices.all().delete()
        user.folders.all().delete()
        user.ciphers.all().delete()
        # user.delete()

        # We only soft-delete this user. The plan of user is still available (but it will be canceled at the end period)
        # If user registers again, the data is deleted but the plan is still available.
        # User must restart the plan manually. Otherwise, the plan is still removed at the end period
        user.revision_date = None
        user.activated = False
        user.account_revision_date = None
        user.master_password = None
        user.master_password_hint = None
        user.master_password_score = 0
        user.security_stamp = None
        user.key = None
        user.public_key = None
        user.private_key = None
        user.save()

    def purge_account(self, user: User):
        user.folders.all().delete()
        user.ciphers.all().delete()
        return user

    def revoke_all_sessions(self, user: User):
        DeviceAccessToken.objects.filter(device__user=user).delete()
        return user

    def change_master_password_hash(self, user: User, new_master_password_hash: str, key: str):
        user.set_master_password(new_master_password_hash)
        user.key = key
        user.save()
