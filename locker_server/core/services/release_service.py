from typing import List, Optional

from locker_server.core.entities.release.release import Release
from locker_server.core.repositories.release_repository import ReleaseRepository


class ReleaseService:
    """
    This class represents Use Cases related release
    """

    def __init__(self, release_repository: ReleaseRepository):
        self.release_repository = release_repository

    def list_releases(self, **filters) -> List[Release]:
        return self.release_repository.list_releases(**filters)

    def get_release_by_id(self, release_id: int) -> Optional[Release]:
        release = self.release_repository.get_release_by_id(
            release_id=release_id
        )
        return release

    def get_release(self, client_id: str, version: str) -> Optional[Release]:
        ver = version.split(".")
        try:
            major = ver[0]
        except IndexError:
            major = "0"
        try:
            minor = ver[1]
        except IndexError:
            minor = "0"
        try:
            patch = ver[2]
        except IndexError:
            patch = None
        try:
            build_number = ver[3]
        except IndexError:
            build_number = None
        return self.release_repository.get_release(
            client_id=client_id,
            major=major,
            minor=minor,
            patch=patch,
            build_number=build_number
        )

    def get_latest_release(self, client_id: str, environment: str) -> Optional[Release]:
        latest_release = self.release_repository.get_latest_release(
            client_id=client_id,
            environment=environment
        )
        return latest_release

    def create_release(self, release_create_data) -> Release:
        return self.release_repository.create_release(release_create_data=release_create_data)

    def generate_next_release(self, client_id: str, environment: str) -> Optional[Release]:
        latest_release = self.get_latest_release(client_id=client_id, environment=environment)
        if not latest_release:
            return None
        if not latest_release.patch:
            next_minor = int(latest_release.minor) + 1
            return Release(
                release_id=None,
                major=latest_release.major,
                minor=next_minor,
                client_id=client_id,
                environment=environment
            )
        if not latest_release.build_number:
            next_patch = int(latest_release.patch) + 1
            return Release(
                release_id=None,
                major=latest_release.major,
                minor=latest_release.minor,
                patch=next_patch,
                client_id=client_id,
                environment=environment
            )
        next_build_number = int(latest_release.build_number) + 1
        return Release(
            release_id=None,
            major=latest_release.major,
            patch=latest_release.patch,
            build_number=next_build_number,
            client_id=client_id,
            environment=environment
        )

    def create_next_release(self, client_id: str, environment: str, checksum: list = None) -> Optional[Release]:
        latest_release = self.get_latest_release(
            client_id=client_id,
            environment=environment
        )
        if not latest_release:
            return None
        if not latest_release.patch:
            next_minor = int(latest_release.minor) + 1
            release_create_data = {
                "major": latest_release.major,
                "minor": next_minor,
                "client_id": client_id,
                "environment": environment,
                "checksum": checksum
            }
            return self.create_release(release_create_data=release_create_data)
        if not latest_release.build_number:
            next_patch = int(latest_release.patch) + 1
            release_create_data = {
                "major": latest_release.major,
                "minor": latest_release.minor,
                "patch": next_patch,
                "client_id": client_id,
                "environment": environment,
                "checksum": checksum
            }
            return self.create_release(release_create_data=release_create_data)
        next_build_number = int(latest_release.build_number) + 1
        release_create_data = {
            "major": latest_release.major,
            "minor": latest_release.minor,
            "patch": latest_release.patch,
            "build_number": next_build_number,
            "client_id": client_id,
            "environment": environment,
            "checksum": checksum
        }
        return self.create_release(release_create_data=release_create_data)
