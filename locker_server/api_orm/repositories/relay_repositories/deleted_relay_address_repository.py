from typing import Optional, List

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_relay_deleted_address_model
from locker_server.core.entities.relay.deleted_relay_address import DeletedRelayAddress
from locker_server.core.repositories.relay_repositories.deleted_relay_address_repository import \
    DeletedRelayAddressRepository

DeletedRelayAddressORM = get_relay_deleted_address_model()
ModelParser = get_model_parser()


class DeletedRelayAddressORMRepository(DeletedRelayAddressRepository):
    # ------------------------ List DeletedRelayAddress resource ------------------- #
    def list_deleted_relay_addresses(self, **filters) -> List[DeletedRelayAddress]:
        pass

    def list_user_deleted_relay_addresses(self, user_id: int, **filters) -> List[DeletedRelayAddress]:
        pass

    # ------------------------ Get DeletedRelayAddress resource --------------------- #
    def get_deleted_relay_address_by_id(self, deleted_relay_address_id: str) -> Optional[DeletedRelayAddress]:
        try:
            deleted_relay_address_orm = DeletedRelayAddressORM.objects.get(id=deleted_relay_address_id)
        except DeletedRelayAddressORM.DoesNotExist:
            return None
        return ModelParser.relay_parser().parse_deleted_relay_address(
            deleted_relay_address_orm=deleted_relay_address_orm
        )

    def check_exist_address_hash(self, address_hash: str) -> bool:
        existed = DeletedRelayAddressORM.objects.filter(
            address_hash=address_hash
        ).exists()
        return existed

    # ------------------------ Create DeletedRelayAddress resource --------------------- #
    def create_deleted_relay_address(self, deleted_relay_address_create_data) -> DeletedRelayAddress:
        deleted_relay_address_orm = DeletedRelayAddressORM.create(**deleted_relay_address_create_data)
        return ModelParser.relay_parser().parse_deleted_relay_address(
            deleted_relay_address_orm=deleted_relay_address_orm
        )

    # ------------------------ Update DeletedRelayAddress resource --------------------- #

    # ------------------------ Delete DeletedRelayAddress resource --------------------- #
