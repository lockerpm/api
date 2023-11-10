from typing import List, Optional

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models import EnterpriseBillingContactORM
from locker_server.core.entities.enterprise.payment.billing_contact import EnterpriseBillingContact
from locker_server.core.repositories.enterprise_billing_contact_repository import EnterpriseBillingContactRepository

ModelParser = get_model_parser()


class EnterpriseBillingContactORMRepository(EnterpriseBillingContactRepository):

    # ------------------------ List EnterpriseBillingContact resource ------------------- #
    def list_enterprise_billing_contacts(self, enterprise_id: str, **filters) -> List[EnterpriseBillingContact]:
        billing_contacts_orm = EnterpriseBillingContactORM.objects.filter(
            enterprise_id=enterprise_id
        ).order_by('-created_time').select_related("enterprise")
        return [
            ModelParser.enterprise_parser().parse_enterprise_billing_contact(
                enterprise_billing_contact_orm=billing_contact_orm
            )
            for billing_contact_orm in billing_contacts_orm
        ]

    # ------------------------ Get EnterpriseBillingContact resource --------------------- #
    def get_enterprise_billing_contact_by_id(self, enterprise_billing_contact_id: str) \
            -> Optional[EnterpriseBillingContact]:
        try:
            billing_contact_orm = EnterpriseBillingContactORM.objects.get(id=enterprise_billing_contact_id)
        except EnterpriseBillingContactORM.DoesNotExist:
            return None
        return ModelParser.enterprise_parser().parse_enterprise_billing_contact(
            enterprise_billing_contact_orm=billing_contact_orm
        )

    # ------------------------ Create EnterpriseBillingContact resource --------------------- #
    def create_enterprise_billing_contact(self, enterprise_billing_contact_create_data) \
            -> Optional[EnterpriseBillingContact]:
        billing_contact_orm = EnterpriseBillingContactORM.create(**enterprise_billing_contact_create_data)
        return ModelParser.enterprise_parser().parse_enterprise_billing_contact(
            enterprise_billing_contact_orm=billing_contact_orm
        )

    # ------------------------ Delete EnterpriseBillingContact resource --------------------- #
    def delete_enterprise_billing_contact_by_id(self, enterprise_billing_contact_id: str) -> bool:
        try:
            billing_contact_orm = EnterpriseBillingContactORM.objects.get(id=enterprise_billing_contact_id)
        except EnterpriseBillingContactORM.DoesNotExist:
            return False
        billing_contact_orm.delete()
        return True
