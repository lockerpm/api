from typing import List, Optional

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.payments.country import CountryORM
from locker_server.core.entities.payment.country import Country
from locker_server.core.repositories.country_repository import CountryRepository


ModelParser = get_model_parser()


class CountryORMRepository(CountryRepository):
    # ------------------------ List Country resource ------------------- #
    def list_countries(self, **filter_params) -> List[Country]:
        countries_orm = CountryORM.objects.all().order_by('country_name')
        return [ModelParser.payment_parser().parse_country(country_orm=country_orm) for country_orm in countries_orm]

    # ------------------------ Get Country resource --------------------- #
    def get_country_by_code(self, country_code: str) -> Optional[Country]:
        try:
            country_orm = CountryORM.objects.get(country_code=country_code)
        except CountryORM.DoesNotExist:
            return None
        return ModelParser.payment_parser().parse_country(country_orm=country_orm)

    def get_country_by_name(self, country_name: str) -> Optional[Country]:
        try:
            country_orm = CountryORM.objects.get(country_name=country_name)
        except CountryORM.DoesNotExist:
            return None
        return ModelParser.payment_parser().parse_country(country_orm=country_orm)

    # ------------------------ Create Country resource --------------------- #

    # ------------------------ Update Country resource --------------------- #

    # ------------------------ Delete Country resource --------------------- #

