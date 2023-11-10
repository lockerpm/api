from locker_server.core.entities.user_plan.plan_type import PlanType
from locker_server.shared.constants.transactions import *


class PMPlan(object):
    def __init__(self, plan_id: int, alias: str = None, name: str = None, price_usd: float = None,
                 price_vnd: float = None, half_yearly_price_usd: float = None, half_yearly_price_vnd: float = None,
                 yearly_price_usd: float = None, yearly_price_vnd: float = None, sync_device: int = None,
                 limit_password: int = None, limit_secure_note: int = None, limit_identity: int = None,
                 limit_payment_card: int = None, limit_crypto_asset: int = None, tools_password_reuse: int = None,
                 tools_master_password_check: bool = False, tools_data_breach: bool = False,
                 emergency_access: bool = False, personal_share: bool = False, relay_premium: bool = False,
                 is_family_plan: bool = False, is_team_plan: bool = False, max_number: int = None,
                 team_dashboard: bool = False, team_policy: bool = False, team_prevent_password: bool = False,
                 team_activity_log: bool = False, plan_type: PlanType = None):
        self._plan_id = plan_id
        self._alias = alias
        self._name = name
        self._price_usd = price_usd
        self._price_vnd = price_vnd
        self._half_yearly_price_usd = half_yearly_price_usd
        self._half_yearly_price_vnd = half_yearly_price_vnd
        self._yearly_price_usd = yearly_price_usd
        self._yearly_price_vnd = yearly_price_vnd
        self._sync_device = sync_device
        self._limit_password = limit_password
        self._limit_secure_note = limit_secure_note
        self._limit_identity = limit_identity
        self._limit_payment_card = limit_payment_card
        self._limit_crypto_asset = limit_crypto_asset
        self._tools_password_reuse = tools_password_reuse
        self._tools_master_password_check = tools_master_password_check
        self._tools_data_breach = tools_data_breach
        self._emergency_access = emergency_access
        self._personal_share = personal_share
        self._relay_premium = relay_premium
        self._is_family_plan = is_family_plan
        self._is_team_plan = is_team_plan
        self._max_number = max_number
        self._team_dashboard = team_dashboard
        self._team_policy = team_policy
        self._team_prevent_password = team_prevent_password
        self._team_activity_log = team_activity_log
        self._plan_type = plan_type

    @property
    def plan_id(self):
        return self._plan_id

    @property
    def alias(self):
        return self._alias

    @property
    def name(self):
        return self._name

    @property
    def price_usd(self):
        return self._price_usd

    @property
    def price_vnd(self):
        return self._price_vnd

    @property
    def half_yearly_price_usd(self):
        return self._half_yearly_price_usd

    @property
    def half_yearly_price_vnd(self):
        return self._half_yearly_price_vnd

    @property
    def yearly_price_usd(self):
        return self._yearly_price_usd

    @property
    def yearly_price_vnd(self):
        return self._yearly_price_vnd

    @property
    def sync_device(self):
        return self._sync_device

    @property
    def limit_password(self):
        return self._limit_password

    @property
    def limit_secure_note(self):
        return self._limit_secure_note

    @property
    def limit_identity(self):
        return self._limit_identity

    @property
    def limit_payment_card(self):
        return self._limit_payment_card

    @property
    def limit_crypto_asset(self):
        return self._limit_crypto_asset

    @property
    def tools_password_reuse(self):
        return self._tools_password_reuse

    @property
    def tools_master_password_check(self):
        return self._tools_master_password_check

    @property
    def tools_data_breach(self):
        return self._tools_data_breach

    @property
    def emergency_access(self):
        return self._emergency_access

    @property
    def personal_share(self):
        return self._personal_share

    @property
    def relay_premium(self):
        return self._relay_premium

    @property
    def is_family_plan(self):
        return self._is_family_plan

    @property
    def is_team_plan(self):
        return self._is_team_plan

    @property
    def max_number(self):
        return self._max_number

    @property
    def team_dashboard(self):
        return self._team_dashboard

    @property
    def team_policy(self):
        return self._team_policy

    @property
    def team_prevent_password(self):
        return self._team_prevent_password

    @property
    def team_activity_log(self):
        return self._team_activity_log

    @property
    def plan_type(self):
        return self._plan_type

    def get_price_usd(self, duration=DURATION_MONTHLY):
        if duration == DURATION_YEARLY:
            return self.yearly_price_usd
        elif duration == DURATION_HALF_YEARLY:
            return self.half_yearly_price_usd
        return self.price_usd

    def get_price_vnd(self, duration=DURATION_MONTHLY):
        if duration == DURATION_YEARLY:
            return self.yearly_price_vnd
        elif duration == DURATION_HALF_YEARLY:
            return self.half_yearly_price_vnd
        return self.price_vnd

    def get_price(self, duration=DURATION_MONTHLY, currency=CURRENCY_USD):
        if currency == CURRENCY_VND:
            return self.get_price_vnd(duration)
        return self.get_price_usd(duration)

    def allow_team_activity_log(self):
        return self.team_activity_log

    def to_json(self):
        data = {
            "id": self.plan_id,
            "name": self.name,
            "alias": self.alias,
            "max_number": self.max_number,
            "price": {
                "usd": self.get_price_usd(duration=DURATION_MONTHLY),
                "vnd": self.get_price_vnd(duration=DURATION_MONTHLY),
                "duration": DURATION_MONTHLY,
            },
            "half_yearly_price": {
                "usd": self.get_price_usd(duration=DURATION_HALF_YEARLY),
                "vnd": self.get_price_vnd(duration=DURATION_HALF_YEARLY),
                "duration": DURATION_HALF_YEARLY,
            },
            "yearly_price": {
                "usd": self.get_price_usd(duration=DURATION_YEARLY),
                "vnd": self.get_price_vnd(duration=DURATION_YEARLY),
                "duration": DURATION_YEARLY,
            }
        }
        return data
