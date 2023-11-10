from abc import ABC, abstractmethod
from typing import List, Optional

from locker_server.core.entities.enterprise.payment.billing_contact import EnterpriseBillingContact


class EnterpriseBillingContactRepository(ABC):

    # ------------------------ List EnterpriseBillingContact resource ------------------- #
    @abstractmethod
    def list_enterprise_billing_contacts(self, enterprise_id: str, **filters) -> List[EnterpriseBillingContact]:
        pass

    # ------------------------ Get EnterpriseBillingContact resource --------------------- #
    @abstractmethod
    def get_enterprise_billing_contact_by_id(self, enterprise_billing_contact_id: str) \
            -> Optional[EnterpriseBillingContact]:
        pass

    # ------------------------ Create EnterpriseBillingContact resource --------------------- #
    @abstractmethod
    def create_enterprise_billing_contact(self, enterprise_billing_contact_create_data) \
            -> Optional[EnterpriseBillingContact]:
        pass

    # ------------------------ Delete EnterpriseBillingContact resource --------------------- #

    @abstractmethod
    def delete_enterprise_billing_contact_by_id(self, enterprise_billing_contact_id: str) -> bool:
        pass
