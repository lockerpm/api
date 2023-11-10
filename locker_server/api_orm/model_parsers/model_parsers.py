from .factor2_parsers import Factor2Parser
from .sso_configuration_parsers import SSOConfigurationParser
from .user_parsers import UserParser
from .notification_setting_parser import NotificationParser
from .user_plan_parsers import UserPlanParser
from .payment_parsers import PaymentParser
from .cipher_parsers import CipherParser
from .team_parser import TeamParser
from .enterprise_parser import EnterpriseParser
from .event_parsers import EventParser
from .relay_parsers import RelayParser
from .form_submission_parsers import FormSubmissionParser
from .release_parsers import ReleaseParser
from .quick_share_parser import QuickShareParser
from .user_reward_parsers import UserRewardParser
from .emergency_access_parsers import EmergencyAccessParser
from .configuration_parsers import ConfigurationParser


class ModelParser:
    """
    Parse ORM objects to Entities
    """

    @classmethod
    def user_parser(cls):
        return UserParser

    @classmethod
    def notification_parser(cls):
        return NotificationParser

    @classmethod
    def user_plan_parser(cls):
        return UserPlanParser

    @classmethod
    def payment_parser(cls):
        return PaymentParser

    @classmethod
    def cipher_parser(cls):
        return CipherParser

    @classmethod
    def team_parser(cls):
        return TeamParser

    @classmethod
    def enterprise_parser(cls):
        return EnterpriseParser

    @classmethod
    def event_parser(cls):
        return EventParser

    @classmethod
    def relay_parser(cls):
        return RelayParser

    @classmethod
    def form_submission_parser(cls):
        return FormSubmissionParser

    @classmethod
    def release_parser(cls):
        return ReleaseParser

    @classmethod
    def quick_share_parser(cls):
        return QuickShareParser

    @classmethod
    def user_reward_parser(cls):
        return UserRewardParser

    @classmethod
    def emergency_access_parser(cls):
        return EmergencyAccessParser

    @classmethod
    def factor2_parser(cls):
        return Factor2Parser

    @classmethod
    def configuration_parser(cls):
        return ConfigurationParser

    @classmethod
    def sso_configuration_parser(cls):
        return SSOConfigurationParser
