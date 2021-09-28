from abc import ABC, abstractmethod


class IUserService(ABC):

    @abstractmethod
    def get_user_by_id(self, user_id: str):
        pass

    @abstractmethod
    def get_account_revision_date_by_id(self, user_id: str):
        pass

    @abstractmethod
    def save_user(self, user, push: bool = False):
        pass

    @abstractmethod
    def register_user(self, validated_data):
        pass

    @abstractmethod
    def send_master_password_hint(self, email):
        pass

    @abstractmethod
    def send_email_verification(self, user):
        pass

    @abstractmethod
    def confirm_email(self, user, token):
        pass

    @abstractmethod
    def change_password(self, user, master_password, new_master_password, key):
        pass

    @abstractmethod
    def set_password(self, user, new_master_password, team_identifier=None):
        pass

    @abstractmethod
    def check_password(self, user, password):
        pass

