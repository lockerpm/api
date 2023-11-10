from locker_server.api_orm.model_parsers.wrapper_specific_model_parser import get_specific_model_parser
from locker_server.api_orm.models import *
from locker_server.core.entities.enterprise.domain.domain import Domain
from locker_server.core.entities.enterprise.domain.domain_ownership import DomainOwnership
from locker_server.core.entities.enterprise.domain.ownership import Ownership
from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.enterprise.group.group import EnterpriseGroup
from locker_server.core.entities.enterprise.group.group_member import EnterpriseGroupMember
from locker_server.core.entities.enterprise.member.enterprise_member import EnterpriseMember
from locker_server.core.entities.enterprise.member.enterprise_member_role import EnterpriseMemberRole
from locker_server.core.entities.enterprise.payment.billing_contact import EnterpriseBillingContact
from locker_server.core.entities.enterprise.policy.policy import EnterprisePolicy
from locker_server.core.entities.enterprise.policy.policy_2fa import Policy2FA
from locker_server.core.entities.enterprise.policy.policy_failed_login import PolicyFailedLogin
from locker_server.core.entities.enterprise.policy.policy_master_password import PolicyMasterPassword
from locker_server.core.entities.enterprise.policy.policy_password import PolicyPassword
from locker_server.core.entities.enterprise.policy.policy_passwordless import PolicyPasswordless


class EnterpriseParser:
    @classmethod
    def parse_enterprise(cls, enterprise_orm: EnterpriseORM) -> Enterprise:
        return Enterprise(
            enterprise_id=enterprise_orm.id,
            name=enterprise_orm.name,
            description=enterprise_orm.description,
            creation_date=enterprise_orm.creation_date,
            revision_date=enterprise_orm.revision_date,
            locked=enterprise_orm.locked,
            enterprise_name=enterprise_orm.enterprise_name,
            enterprise_address1=enterprise_orm.enterprise_address1,
            enterprise_address2=enterprise_orm.enterprise_address2,
            enterprise_phone=enterprise_orm.enterprise_phone,
            enterprise_country=enterprise_orm.enterprise_country,
            enterprise_postal_code=enterprise_orm.enterprise_postal_code,
            init_seats=enterprise_orm.init_seats,
            init_seats_expired_time=enterprise_orm.init_seats_expired_time,
            avatar=enterprise_orm.avatar
        )

    @classmethod
    def parse_enterprise_member_role(cls, enterprise_member_role_orm: EnterpriseMemberRoleORM) -> EnterpriseMemberRole:
        return EnterpriseMemberRole(name=enterprise_member_role_orm.name)

    @classmethod
    def parse_ownership(cls, ownership_orm: OwnershipORM) -> Ownership:
        return Ownership(ownership_id=ownership_orm.id, description=ownership_orm.description)

    @classmethod
    def parse_domain(cls, domain_orm: DomainORM) -> Domain:
        return Domain(
            domain_id=domain_orm.id,
            created_time=domain_orm.created_time,
            updated_time=domain_orm.updated_time,
            domain=domain_orm.domain,
            root_domain=domain_orm.root_domain,
            verification=domain_orm.verification,
            auto_approve=domain_orm.auto_approve,
            is_notify_failed=domain_orm.is_notify_failed,
            enterprise=cls.parse_enterprise(enterprise_orm=domain_orm.enterprise)
        )

    @classmethod
    def parse_domain_ownership(cls, domain_ownership_orm: DomainOwnershipORM) -> DomainOwnership:
        return DomainOwnership(
            domain_ownership_id=domain_ownership_orm.id,
            key=domain_ownership_orm.key,
            value=domain_ownership_orm.value,
            verification=domain_ownership_orm.verification,
            domain=cls.parse_domain(domain_orm=domain_ownership_orm.domain),
            ownership=cls.parse_ownership(ownership_orm=domain_ownership_orm.ownership)
        )

    @classmethod
    def parse_enterprise_member(cls, enterprise_member_orm: EnterpriseMemberORM) -> EnterpriseMember:
        user = get_specific_model_parser("UserParser").parse_user(user_orm=enterprise_member_orm.user) \
            if enterprise_member_orm.user else None
        domain = cls.parse_domain(domain_orm=enterprise_member_orm.domain) if enterprise_member_orm.domain else None
        return EnterpriseMember(
            enterprise_member_id=enterprise_member_orm.id,
            access_time=enterprise_member_orm.access_time,
            is_default=enterprise_member_orm.is_default,
            is_activated=enterprise_member_orm.is_activated,
            status=enterprise_member_orm.status,
            email=enterprise_member_orm.email,
            token_invitation=enterprise_member_orm.token_invitation,
            user=user,
            enterprise=cls.parse_enterprise(enterprise_orm=enterprise_member_orm.enterprise),
            role=cls.parse_enterprise_member_role(enterprise_member_role_orm=enterprise_member_orm.role),
            domain=domain
        )

    @classmethod
    def parse_enterprise_group(cls, enterprise_group_orm: EnterpriseGroupORM) -> EnterpriseGroup:
        created_by = get_specific_model_parser("UserParser").parse_user(user_orm=enterprise_group_orm.created_by) \
            if enterprise_group_orm.created_by else None
        return EnterpriseGroup(
            enterprise_group_id=enterprise_group_orm.id,
            name=enterprise_group_orm.name,
            creation_date=enterprise_group_orm.creation_date,
            revision_date=enterprise_group_orm.revision_date,
            created_by=created_by,
            enterprise=cls.parse_enterprise(enterprise_orm=enterprise_group_orm.enterprise)

        )

    @classmethod
    def parse_enterprise_group_member(cls,
                                      enterprise_group_member_orm: EnterpriseGroupMemberORM) -> EnterpriseGroupMember:
        return EnterpriseGroupMember(
            enterprise_group_member_id=enterprise_group_member_orm.id,
            group=cls.parse_enterprise_group(enterprise_group_orm=enterprise_group_member_orm.group),
            member=cls.parse_enterprise_member(enterprise_member_orm=enterprise_group_member_orm.member)
        )

    @classmethod
    def parse_enterprise_policy(cls, enterprise_policy_orm: EnterprisePolicyORM) -> EnterprisePolicy:
        enterprise_policy = EnterprisePolicy(
            policy_id=enterprise_policy_orm.id,
            enterprise=cls.parse_enterprise(enterprise_orm=enterprise_policy_orm.enterprise),
            policy_type=enterprise_policy_orm.policy_type,
            enabled=enterprise_policy_orm.enabled
        )
        enterprise_policy.config = enterprise_policy_orm.get_config_json()
        return enterprise_policy

    @classmethod
    def parse_policy_2fa(cls, policy_2fa_orm: Policy2FAORM) -> Policy2FA:
        return Policy2FA(
            policy_id=policy_2fa_orm.policy_id,
            enterprise=cls.parse_enterprise(enterprise_orm=policy_2fa_orm.policy.enterprise),
            policy_type=policy_2fa_orm.policy.policy_type,
            enabled=policy_2fa_orm.policy.enabled,
            only_admin=policy_2fa_orm.only_admin
        )

    @classmethod
    def parse_policy_failed_login(cls, policy_failed_login_orm: PolicyFailedLoginORM) -> PolicyFailedLogin:
        return PolicyFailedLogin(
            policy_id=policy_failed_login_orm.policy_id,
            enterprise=cls.parse_enterprise(enterprise_orm=policy_failed_login_orm.policy.enterprise),
            policy_type=policy_failed_login_orm.policy.policy_type,
            enabled=policy_failed_login_orm.policy.enabled,
            failed_login_attempts=policy_failed_login_orm.failed_login_attempts,
            failed_login_duration=policy_failed_login_orm.failed_login_duration,
            failed_login_block_time=policy_failed_login_orm.failed_login_block_time,
            failed_login_owner_email=policy_failed_login_orm.failed_login_owner_email
        )

    @classmethod
    def parse_policy_master_password(cls, policy_master_password_orm: PolicyMasterPasswordORM) -> PolicyMasterPassword:
        return PolicyMasterPassword(
            policy_id=policy_master_password_orm.policy_id,
            enterprise=cls.parse_enterprise(enterprise_orm=policy_master_password_orm.policy.enterprise),
            policy_type=policy_master_password_orm.policy.policy_type,
            enabled=policy_master_password_orm.policy.enabled,
            min_length=policy_master_password_orm.min_length,
            require_lower_case=policy_master_password_orm.require_lower_case,
            require_upper_case=policy_master_password_orm.require_upper_case,
            require_special_character=policy_master_password_orm.require_special_character,
            require_digit=policy_master_password_orm.require_digit
        )

    @classmethod
    def parse_policy_password(cls, policy_password_orm: PolicyPasswordORM) -> PolicyPassword:
        return PolicyPassword(
            policy_id=policy_password_orm.policy_id,
            enterprise=cls.parse_enterprise(enterprise_orm=policy_password_orm.policy.enterprise),
            policy_type=policy_password_orm.policy.policy_type,
            enabled=policy_password_orm.policy.enabled,
            min_length=policy_password_orm.min_length,
            require_lower_case=policy_password_orm.require_lower_case,
            require_upper_case=policy_password_orm.require_upper_case,
            require_special_character=policy_password_orm.require_special_character,
            require_digit=policy_password_orm.require_digit
        )

    @classmethod
    def parse_policy_passwordless(cls, policy_passwordless_orm: PolicyPasswordlessORM) -> PolicyPasswordless:
        return PolicyPasswordless(
            policy_id=policy_passwordless_orm.policy_id,
            enterprise=cls.parse_enterprise(enterprise_orm=policy_passwordless_orm.policy.enterprise),
            policy_type=policy_passwordless_orm.policy.policy_type,
            enabled=policy_passwordless_orm.policy.enabled,
            only_allow_passwordless=policy_passwordless_orm.only_allow_passwordless
        )

    @classmethod
    def parse_enterprise_billing_contact(cls, enterprise_billing_contact_orm: EnterpriseBillingContactORM) \
            -> EnterpriseBillingContact:
        enterprise = cls.parse_enterprise(enterprise_orm=enterprise_billing_contact_orm.enterprise)
        return EnterpriseBillingContact(
            enterprise_billing_contact_id=enterprise_billing_contact_orm.id,
            enterprise=enterprise,
            created_time=enterprise_billing_contact_orm.created_time,
            email=enterprise_billing_contact_orm.email
        )
