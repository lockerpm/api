from typing import Dict

import stripe
from django.core.exceptions import ObjectDoesNotExist

from core.repositories import IUserRepository
from shared.constants.members import PM_MEMBER_STATUS_INVITED
from shared.log.cylog import CyLog
from shared.utils.app import now
from cystack_models.models import User


class UserRepository(IUserRepository):
    def retrieve_or_create_by_id(self, user_id, creation_date=None) -> User:
        try:
            user = self.get_by_id(user_id=user_id)
        except User.DoesNotExist:
            creation_date = now() if not creation_date else float(creation_date)
            user = User(user_id=user_id, creation_date=creation_date)
            user.save()
            # Create default team for this new user
            self.get_default_team(user=user)
        return user

    def get_by_id(self, user_id) -> User:
        return User.objects.get(user_id=user_id)

    def get_default_team(self, user: User):
        try:
            default_team = user.team_members.get(is_default=True).team
        except ObjectDoesNotExist:
            return
            # default_team = self._create_default_team(user)
        return default_team

    def _create_default_team(self, user: User):
        pass

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

    def get_current_plan(self, user: User, scope=None):
        try:
            return user.pm_user_plan
        except (ValueError, AttributeError):
            from cystack_models.models.user_plans.pm_user_plan import PMUserPlan
            return PMUserPlan.update_or_create(user)

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

    def get_list_invitations(self, user: User):
        member_invitations = user.team_members.filter(status=PM_MEMBER_STATUS_INVITED).order_by('access_time')
        return member_invitations

    def delete_account(self, user: User):
        user.user_refresh_tokens.all().delete()
        user.folders.all().delete()
        user.ciphers.all().delete()
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
        user.user_refresh_tokens.all().delete()
        return user

    def change_master_password_hash(self, user: User, new_master_password_hash: str, key: str):
        user.set_master_password(new_master_password_hash)
        user.key = key
        user.save()
