from typing import Optional, List

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_release_model
from locker_server.core.entities.release.release import Release
from locker_server.core.repositories.release_repository import ReleaseRepository

ReleaseORM = get_release_model()
ModelParser = get_model_parser()


class ReleaseORMRepository(ReleaseRepository):
    # ------------------------ List Release resource ------------------- #
    def list_releases(self, **filters) -> List[Release]:
        releases_orm = ReleaseORM.objects.all().order_by('-id')
        client_id_param = filters.get("client_id")
        environment_param = filters.get("environment")
        if client_id_param is not None:
            releases_orm = releases_orm.filter(
                client_id=client_id_param
            )
        if environment_param:
            releases_orm = releases_orm.filter(
                environment=environment_param
            )
        return [
            ModelParser.release_parser().parse_release(release_orm=release_orm)
            for release_orm in releases_orm
        ]

        # ------------------------ Get Release resource --------------------- #

    def get_release_by_id(self, release_id: int) -> Optional[Release]:
        try:
            release_orm = ReleaseORM.objects.get(id=release_id)
        except ReleaseORM.DoesNotExist:
            return None
        return ModelParser.release_parser().parse_release(release_orm=release_orm)

    def get_latest_release(self, client_id: str, environment: str) -> Optional[Release]:
        latest_release_orm = ReleaseORM.objects.filter(
            client_id=client_id, environment=environment
        ).order_by('-id').first()
        if not latest_release_orm:
            return None
        return ModelParser.release_parser().parse_release(release_orm=latest_release_orm)

    def get_release(self, client_id: str, major: str, minor: str, patch: str = None, build_number: str = None) \
            -> Optional[Release]:
        releases_orm = ReleaseORM.objects.filter(
            client_id=client_id,
            major=major,
            minor=minor
        )
        if patch is not None:
            releases_orm = releases_orm.filter(
                patch=patch
            )
        if build_number is not None:
            releases_orm = releases_orm.filter(
                build_number=build_number
            )
        release_orm = releases_orm.first()
        if release_orm is None:
            return None
        return ModelParser.release_parser().parse_release(release_orm=release_orm)

    # ------------------------ Create Release resource --------------------- #
    def create_release(self, release_create_data) -> Release:
        release_orm = ReleaseORM.create(**release_create_data)
        return ModelParser.release_parser().parse_release(release_orm=release_orm)

    # ------------------------ Update Release resource --------------------- #

    # ------------------------ Delete Release resource --------------------- #
