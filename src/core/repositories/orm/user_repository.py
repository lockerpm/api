from typing import Dict

from django.core.exceptions import ObjectDoesNotExist

from core.repositories import IUserRepository
from shared.constants.members import PM_MEMBER_STATUS_INVITED
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
