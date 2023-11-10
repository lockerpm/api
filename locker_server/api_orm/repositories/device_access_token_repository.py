from typing import Optional, List

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_device_access_token_model, get_device_model
from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.device_access_token import DeviceAccessToken
from locker_server.core.repositories.device_access_token_repository import DeviceAccessTokenRepository
from locker_server.shared.utils.app import now

DeviceORM = get_device_model()
DeviceAccessTokenORM = get_device_access_token_model()
ModelParser = get_model_parser()


class DeviceAccessTokenORMRepository(DeviceAccessTokenRepository):
    # ------------------------ List DeviceAccessToken resource ------------------- #
    def list_sso_token_ids(self, device_ids: List, **filter_params) -> List[str]:
        return list(
            DeviceAccessTokenORM.objects.filter(device_id__in=device_ids).order_by('-expired_time').exclude(
                sso_token_id__isnull=True
            ).values_list('sso_token_id', flat=True)
        )

    # ------------------------ Get DeviceAccessToken resource --------------------- #
    def get_device_access_token_by_id(self, device_access_token_id: str) -> Optional[DeviceAccessToken]:
        try:
            device_access_token_orm = DeviceAccessTokenORM.objects.get(id=device_access_token_id)
        except DeviceAccessTokenORM.DoesNotExist:
            return None
        return ModelParser.user_parser().parse_device_access_token(device_access_token_orm=device_access_token_orm)

    def get_first_device_access_token_by_sso_ids(self, user_id: int,
                                                 sso_token_ids: List[str]) -> Optional[DeviceAccessToken]:
        device_access_token_orm = DeviceAccessTokenORM.objects.filter(
            device__user_id=user_id, sso_token_id__in=sso_token_ids
        ).order_by('-id').first()
        if not device_access_token_orm:
            return None
        return ModelParser.user_parser().parse_device_access_token(device_access_token_orm=device_access_token_orm)

    # ------------------------ Create DeviceAccessToken resource --------------------- #
    def fetch_device_access_token(self, device: Device, renewal: bool = False,
                                  sso_token_id: str = None) -> DeviceAccessToken:
        valid_access_token_orm = DeviceAccessTokenORM.objects.filter(
            device_id=device.device_id, expired_time__gte=now()
        ).order_by('-expired_time').first()

        if not valid_access_token_orm or renewal is True:
            device_orm = DeviceORM.objects.get(id=device.device_id)
            # Generate new access token
            valid_access_token_orm = DeviceAccessTokenORM.create(device=device_orm, **{
                "access_token": "access_token",
                "grant_type": "refresh_token",
                "expires_in": DeviceAccessTokenORM.get_token_duration(client_id=device_orm.client_id),
                "sso_token_id": sso_token_id
            })
        return ModelParser.user_parser().parse_device_access_token(device_access_token_orm=valid_access_token_orm)

    # ------------------------ Update DeviceAccessToken resource --------------------- #

    # ------------------------ Delete DeviceAccessToken resource --------------------- #
    def remove_devices_access_tokens(self, device_ids: List):
        return DeviceAccessTokenORM.objects.filter(device_id__in=list(device_ids)).delete()
