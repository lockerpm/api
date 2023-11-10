from typing import List, Optional

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_enterprise_domain_model
from locker_server.core.entities.enterprise.domain.domain import Domain
from locker_server.core.repositories.enterprise_domain_repository import EnterpriseDomainRepository

ModelParser = get_model_parser()
DomainORM = get_enterprise_domain_model()


class EnterpriseDomainORMRepository(EnterpriseDomainRepository):
    # ------------------------ List Domain resource ------------------- #
    def list_domains(self, **filters) -> List[Domain]:
        verification_param = filters.get("verification")

        domains_orm = DomainORM.objects.all().select_related("enterprise")
        if verification_param is not None:
            domains_orm = domains_orm.filter(verification=verification_param)
        return [
            ModelParser.enterprise_parser().parse_domain(domain_orm=domain_orm)
            for domain_orm in domains_orm
        ]

    def list_enterprise_domains(self, enterprise_id: str, **filters) -> List[Domain]:
        domains_orm = DomainORM.objects.filter(
            enterprise_id=enterprise_id
        ).order_by('-created_time')
        return [
            ModelParser.enterprise_parser().parse_domain(domain_orm=domain_orm)
            for domain_orm in domains_orm
        ]

    def check_domain_exist(self, enterprise_id: str, domain: str) -> bool:
        return DomainORM.objects.filter(
            enterprise_id=enterprise_id,
            domain=domain
        ).exists()

    def check_root_domain_verify(self, root_domain: str, enterprise_id: str = None, exclude_enterprise_id: str = None):
        if exclude_enterprise_id:
            domains_orm = DomainORM.objects.exclude(enterprise_id=exclude_enterprise_id)
        else:
            domains_orm = DomainORM.objects.all()
        if enterprise_id:
            domains_orm = domains_orm.filter(
                enterprise_id=enterprise_id
            )
        domains_orm = domains_orm.filter(
            root_domain=root_domain,
            verification=True
        )
        return domains_orm.exists()

    def count_unverified_domain(self, enterprise_id: str) -> int:
        unverified_domain_count = DomainORM.objects.filter(
            verification=False,
            enterprise_id=enterprise_id
        ).count()
        return unverified_domain_count

    # ------------------------ Get Domain resource --------------------- #
    def get_domain_by_id(self, domain_id: str) -> Optional[Domain]:
        try:
            domain_orm = DomainORM.objects.get(id=domain_id)
        except DomainORM.DoesNotExist:
            return None
        return ModelParser.enterprise_parser().parse_domain(domain_orm=domain_orm)

    def get_ownerships_by_domain_id(self, domain_id: str) -> List:
        try:
            domain_orm = DomainORM.objects.get(id=domain_id)
        except DomainORM.DoesNotExist:
            return []
        return domain_orm.get_verifications()

    def check_verification(self, domain_id: str) -> bool:
        try:
            domain_orm = DomainORM.objects.get(id=domain_id)
        except DomainORM.DoesNotExist:
            return False
        return domain_orm.check_verification()

    # ------------------------ Create Domain resource --------------------- #
    def create_domain(self, domain_create_data) -> Domain:
        domain_orm = DomainORM.create(**domain_create_data)
        return ModelParser.enterprise_parser().parse_domain(domain_orm=domain_orm)

    # ------------------------ Update Domain resource --------------------- #
    def update_domain(self, domain_id: str, domain_update_data) -> Optional[Domain]:
        try:
            domain_orm = DomainORM.objects.get(id=domain_id)
        except DomainORM.DoesNotExist:
            return None
        domain_orm.auto_approve = domain_update_data.get("auto_approve", domain_orm.auto_approve)
        domain_orm.is_notify_failed = domain_update_data.get("is_notify_failed", domain_orm.is_notify_failed)
        domain_orm.save()
        return ModelParser.enterprise_parser().parse_domain(domain_orm=domain_orm)

    # ------------------------ Delete Domain resource --------------------- #

    def delete_domain_by_id(self, domain_id: str) -> bool:
        try:
            domain_orm = DomainORM.objects.get(id=domain_id)
        except DomainORM.DoesNotExist:
            return False
        domain_orm.delete()
        return True
