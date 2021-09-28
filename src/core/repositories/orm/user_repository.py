from typing import Dict

from core.repositories import IUserRepository
from cystack_models.models import User


class UserRepository(IUserRepository):
    def get_by_id(self, user_id) -> User:
        return User.objects.get(user_id=user_id)

    def get_by_email(self, email) -> User:
        pass

    def get_kdf_information_by_email(self, email) -> Dict:
        pass

    def get_many_by_ids(self, user_ids: list):
        return User.objects.filter(user_id__in=user_ids)
