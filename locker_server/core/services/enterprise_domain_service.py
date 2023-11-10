from typing import List, Optional

from locker_server.core.entities.enterprise.domain.domain import Domain
from locker_server.core.exceptions.enterprise_domain_exception import DomainDoesNotExistException, \
    DomainExistedException, DomainVerifiedByOtherException, DomainVerifiedErrorException
from locker_server.core.exceptions.enterprise_exception import EnterpriseDoesNotExistException
from locker_server.core.repositories.enterprise_domain_repository import EnterpriseDomainRepository
from locker_server.core.repositories.enterprise_member_repository import EnterpriseMemberRepository
from locker_server.core.repositories.enterprise_repository import EnterpriseRepository
from locker_server.core.repositories.event_repository import EventRepository
from locker_server.core.repositories.user_plan_repository import UserPlanRepository
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_REQUESTED, E_MEMBER_STATUS_CONFIRMED
from locker_server.shared.constants.event import EVENT_E_MEMBER_CONFIRMED
from locker_server.shared.constants.transactions import PAYMENT_METHOD_CARD


class EnterpriseDomainService:
    """
    This class represents Use Cases related Enterprise Domain
    """

    def __init__(self, enterprise_domain_repository: EnterpriseDomainRepository,
                 enterprise_repository: EnterpriseRepository,
                 enterprise_member_repository: EnterpriseMemberRepository,
                 event_repository: EventRepository,
                 user_plan_repository: UserPlanRepository):
        self.enterprise_domain_repository = enterprise_domain_repository
        self.enterprise_repository = enterprise_repository
        self.enterprise_member_repository = enterprise_member_repository
        self.event_repository = event_repository
        self.user_plan_repository = user_plan_repository

    def list_enterprise_domains(self, enterprise_id: str) -> List[Domain]:
        return self.enterprise_domain_repository.list_enterprise_domains(
            enterprise_id=enterprise_id
        )

    def get_domain_by_id(self, domain_id: str) -> Optional[Domain]:
        domain = self.enterprise_domain_repository.get_domain_by_id(domain_id=domain_id)
        if not domain:
            raise DomainDoesNotExistException
        return domain

    def create_domain(self, domain_create_data) -> Domain:
        domain = domain_create_data.get("domain")
        root_domain = domain_create_data.get("root_domain")
        enterprise_id = domain_create_data.get("enterprise_id")
        enterprise = self.enterprise_repository.get_enterprise_by_id(enterprise_id=enterprise_id)
        if not enterprise:
            raise EnterpriseDoesNotExistException
        is_existed_domain = self.enterprise_domain_repository.check_domain_exist(
            enterprise_id=enterprise.enterprise_id,
            domain=domain
        )
        if is_existed_domain:
            raise DomainExistedException
        is_verified_by_other = self.enterprise_domain_repository.check_root_domain_verify(
            exclude_enterprise_id=enterprise.enterprise_id,
            root_domain=root_domain
        )
        if is_verified_by_other:
            raise DomainVerifiedByOtherException
        is_verified_before = self.enterprise_domain_repository.check_root_domain_verify(
            enterprise_id=enterprise.enterprise_id,
            root_domain=root_domain
        )
        domain_create_data = {
            "enterprise_id": enterprise_id,
            "verification": is_verified_before,
            "domain": domain,
            "root_domain": root_domain
        }
        new_domain = self.enterprise_domain_repository.create_domain(
            domain_create_data=domain_create_data
        )
        return new_domain

    def update_domain(self, domain_id: str, domain_update_data) -> Optional[Domain]:
        updated_domain = self.enterprise_domain_repository.update_domain(
            domain_id=domain_id,
            domain_update_data=domain_update_data
        )
        if not updated_domain:
            raise DomainDoesNotExistException
        return updated_domain

    def delete_domain(self, domain_id: str) -> bool:
        deleted_domain = self.enterprise_domain_repository.delete_domain_by_id(
            domain_id=domain_id
        )
        if not deleted_domain:
            raise DomainDoesNotExistException
        return deleted_domain

    def get_ownerships_by_domain_id(self, domain_id) -> List:
        return self.enterprise_domain_repository.get_ownerships_by_domain_id(
            domain_id=domain_id
        )

    def verify_domain(self, domain: Domain):
        is_verified_by_other = self.enterprise_domain_repository.check_root_domain_verify(
            exclude_enterprise_id=domain.enterprise.enterprise_id,
            root_domain=domain.root_domain
        )
        if is_verified_by_other:
            raise DomainVerifiedByOtherException
        is_verify = self.enterprise_domain_repository.check_verification(
            domain_id=domain.domain_id
        )
        if not is_verify:
            raise DomainVerifiedErrorException
        return is_verify

    def domain_auto_approve(self, user_id_update_domain: int, domain: Domain, ip_address: str = None,
                            scope: str = None):
        enterprise = domain.enterprise
        members = self.enterprise_member_repository.list_enterprise_members(**{
            "domain_id": domain.domain_id,
            "statuses": [E_MEMBER_STATUS_REQUESTED]
        })
        billing_members = len(members)
        member_events_data = []
        for member in members:
            member_events_data.append({
                "acting_user_id": user_id_update_domain,
                "user_id": member.user.user_id,
                "team_id": enterprise.enterprise_id,
                "team_member_id": member.enterprise_member_id,
                "type": EVENT_E_MEMBER_CONFIRMED,
                "ip_address": ip_address
            })

        # Update the Stripe subscription
        if billing_members > 0:
            from locker_server.shared.external_services.payment_method.payment_method_factory import \
                PaymentMethodFactory
            from locker_server.core.exceptions.payment_exception import PaymentMethodNotSupportException
            primary_admin = self.enterprise_member_repository.get_primary_member(enterprise_id=enterprise.enterprise_id)
            if primary_admin:
                try:
                    primary_admin_plan = self.user_plan_repository.get_user_plan(user_id=primary_admin.user.user_id)
                    PaymentMethodFactory.get_method(
                        user_plan=primary_admin_plan, scope=scope, payment_method=PAYMENT_METHOD_CARD
                    ).update_quantity_subscription(amount=billing_members)
                except PaymentMethodNotSupportException:
                    pass

        # Auto accept all requested members
        self.enterprise_member_repository.update_batch_enterprise_members(
            enterprise_member_ids=[m.enterprise_member_id for m in members],
            **{
                "status": E_MEMBER_STATUS_CONFIRMED
            }
        )
        # Log events
        self.event_repository.create_multiple_by_enterprise_members(member_events_data)
