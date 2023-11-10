from typing import Optional, List

from locker_server.core.entities.enterprise.payment.billing_contact import EnterpriseBillingContact
from locker_server.core.exceptions.enterprise_billing_contact_exception import *
from locker_server.core.repositories.enterprise_billing_contact_repository import EnterpriseBillingContactRepository


class EnterpriseBillingContactService:

    """
    This class represents Use cases related Enterprise Contact
    """

    def __init__(self, enterprise_billing_contact_repository: EnterpriseBillingContactRepository):
        self.enterprise_billing_contact_repository = enterprise_billing_contact_repository

    def list_enterprise_billing_contacts(self, enterprise_id: str) -> List[EnterpriseBillingContact]:
        return self.enterprise_billing_contact_repository.list_enterprise_billing_contacts(
            enterprise_id=enterprise_id
        )

    def create_enterprise_billing_contact(self, enterprise_id: str, email: str) -> EnterpriseBillingContact:
        return self.enterprise_billing_contact_repository.create_enterprise_billing_contact(
            enterprise_billing_contact_create_data={
                "enterprise_id": enterprise_id,
                "email": email
            }
        )

    def get_enterprise_billing_contact_by_id(self, enterprise_billing_contact_id: str) \
            -> Optional[EnterpriseBillingContact]:
        enterprise_billing_contact = self.enterprise_billing_contact_repository.get_enterprise_billing_contact_by_id(
            enterprise_billing_contact_id=enterprise_billing_contact_id
        )
        if not enterprise_billing_contact:
            raise EnterpriseBillingContactDoesNotExistException
        return enterprise_billing_contact

    def delete_enterprise_billing_contact_by_id(self, enterprise_billing_contact_id: str) -> bool:
        deleted = self.enterprise_billing_contact_repository.delete_enterprise_billing_contact_by_id(
            enterprise_billing_contact_id=enterprise_billing_contact_id
        )
        if not deleted:
            raise EnterpriseBillingContactDoesNotExistException
        return deleted
