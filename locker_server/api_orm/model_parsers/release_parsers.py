from locker_server.api_orm.models import *
from locker_server.core.entities.release.release import Release


class ReleaseParser:
    @classmethod
    def parse_release(cls, release_orm: ReleaseORM) -> Release:
        return Release(
            release_id=release_orm.id,
            created_time=release_orm.created_time,
            major=release_orm.major,
            minor=release_orm.minor,
            patch=release_orm.patch,
            build_number=release_orm.build_number,
            description_en=release_orm.description_en,
            description_vi=release_orm.description_vi,
            client_id=release_orm.client_id,
            environment=release_orm.environment,
            checksum=release_orm.checksum,
        )
