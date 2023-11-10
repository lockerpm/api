import json
from typing import Optional, List

import requests

from locker_server.core.entities.sso_configuration.sso_configuration import SSOConfiguration
from locker_server.core.exceptions.sso_configuration_exception import SSOConfigurationIdentifierExistedException, \
    SSOConfigurationDoesNotExistException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.repositories.sso_configuration_repository import SSOConfigurationRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.sso_provider import SSO_PROVIDER_OAUTH2
from locker_server.shared.external_services.requester.retry_requester import requester
from locker_server.shared.log.cylog import CyLog


class SSOConfigurationService:
    """
    Organization SSO configuration Use cases
    """

    def __init__(self, sso_configuration_repository: SSOConfigurationRepository, user_repository: UserRepository):
        self.sso_configuration_repository = sso_configuration_repository
        self.user_repository = user_repository

    def get_sso_configuration(self, sso_configuration_id: str) -> Optional[SSOConfiguration]:
        return self.sso_configuration_repository.get_sso_configuration(
            sso_configuration_id=sso_configuration_id
        )

    def get_sso_configuration_by_identifier(self, identifier: str) -> Optional[SSOConfiguration]:
        org_sso_config = self.sso_configuration_repository.get_sso_configuration_by_identifier(
            identifier=identifier
        )
        if not org_sso_config:
            raise SSOConfigurationDoesNotExistException
        return org_sso_config

    def update_sso_configuration(self, user_id: int, sso_config_update_data) -> Optional[SSOConfiguration]:
        user = self.user_repository.get_user_by_id(user_id=user_id)
        if not user:
            raise UserDoesNotExistException
        sso_config_update_data.update({
            "created_by_id": user.user_id
        })
        updated_sso_configuration = self.sso_configuration_repository.update_sso_configuration(
            sso_config_update_data=sso_config_update_data
        )
        return updated_sso_configuration

    def destroy_sso_configuration(self):
        return self.sso_configuration_repository.destroy_sso_configuration()

    def get_user_by_code(self, sso_identifier: str, code: str):
        if sso_identifier:
            sso_configuration = self.sso_configuration_repository.get_sso_configuration_by_identifier(
                identifier=sso_identifier
            )
            if not sso_identifier:
                return {}
        sso_configuration = self.get_first()
        if not sso_identifier:
            return {}
        sso_provider_id = sso_configuration.sso_provider.sso_provider_id
        if sso_provider_id == SSO_PROVIDER_OAUTH2:
            token_endpoint = sso_configuration.sso_provider_options.get("token_endpoint")
            userinfo_endpoint = sso_configuration.sso_provider_options.get("userinfo_endpoint")
            try:
                res = requester(method="GET", url=token_endpoint)
                if res.status_code == 200:
                    id_token = res.json().get("id_token")
                    token_type = res.json().get("token_type")
                else:
                    return {}
                user_res_header = {'Authorization': f"{token_type} {id_token}"}
                user_res = requester(method="GET", url=userinfo_endpoint, headers=user_res_header)
                if user_res.status_code == 200:
                    try:
                        user_info = user_res.json()
                        return user_info
                    except json.JSONDecodeError:
                        CyLog.error(
                            **{
                                "message": f"[!] User.get_from_sso_configuration JSON Decode error: {sso_configuration.identifier} {res.text}"
                            }
                        )
                        return {}
            except (requests.RequestException, requests.ConnectTimeout):
                return {}
        return {}

    def get_first(self) -> Optional[SSOConfiguration]:
        return self.sso_configuration_repository.get_first()
