from typing import Optional, List

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models import ExcludeDomainORM
from locker_server.core.entities.user.exclude_domain import ExcludeDomain
from locker_server.core.repositories.exclude_domain_repository import ExcludeDomainRepository


ModelParser = get_model_parser()


class ExcludeDomainORMRepository(ExcludeDomainRepository):
    # ------------------------ List ExcludeDomain resource ------------------- #
    def list_user_exclude_domains(self, user_id: int, **filter_params) -> List[ExcludeDomain]:
        exclude_domains_orm = ExcludeDomainORM.objects.filter(
            user_id=user_id
        ).order_by('-created_time').select_related('user')
        q_param = filter_params.get("q")
        if q_param:
            exclude_domains_orm = exclude_domains_orm.filter(domain__icontains=q_param.lower())
        return [
            ModelParser.user_parser().parse_exclude_domain(exclude_domain_orm=exclude_domain_orm)
            for exclude_domain_orm in exclude_domains_orm
        ]

    # ------------------------ Get ExcludeDomain resource --------------------- #
    def get_exclude_domain_by_id(self, exclude_domain_id: str) -> Optional[ExcludeDomain]:
        try:
            exclude_domain_orm = ExcludeDomainORM.objects.get(id=exclude_domain_id)
        except ExcludeDomainORM.DoesNotExist:
            return None
        return ModelParser.user_parser().parse_exclude_domain(exclude_domain_orm=exclude_domain_orm)

    # ------------------------ Create ExcludeDomain resource --------------------- #
    def create_exclude_domain(self, user_id: int, domain: str) -> ExcludeDomain:
        exclude_domain_orm = ExcludeDomainORM.retrieve_or_create(domain=domain, user_id=user_id)
        return ModelParser.user_parser().parse_exclude_domain(exclude_domain_orm=exclude_domain_orm)

    # ------------------------ Update ExcludeDomain resource --------------------- #

    # ------------------------ Delete ExcludeDomain resource --------------------- #
    def remove_exclude_domain(self, exclude_domain_id: str):
        try:
            exclude_domain_orm = ExcludeDomainORM.objects.get(id=exclude_domain_id)
        except ExcludeDomainORM.DoesNotExist:
            return False
        exclude_domain_orm.delete()
        return True
