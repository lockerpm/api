from rest_framework.response import Response
from rest_framework.decorators import action

from cystack_models.models.releases.releases import Release
from shared.permissions.locker_permissions.release_pwd_permission import ReleasePwdPermission
from v1_0.general_view import PasswordManagerViewSet
from .serializers import NewReleaseSerializer, NextReleaseSerializer


class ReleasePwdViewSet(PasswordManagerViewSet):
    permission_classes = (ReleasePwdPermission, )
    http_method_names = ["head", "options", "get", "post"]

    def get_serializer_class(self):
        if self.action == "new":
            self.serializer_class = NewReleaseSerializer
        elif self.action == "current":
            self.serializer_class = NextReleaseSerializer
        return super(ReleasePwdViewSet, self).get_serializer_class()

    @action(methods=["post"], detail=False)
    def current(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        client_id = validated_data.get("client_id")
        environment = validated_data.get("environment")

        latest_release = Release.objects.filter(client_id=client_id, environment=environment).order_by('-id').first()
        if not latest_release:
            return Response(status=200, data={"version": "1.0.0", "environment": environment})

        if not latest_release.patch:
            next_minor = int(latest_release.minor) + 1
            new_release = Release(**{
                "major": latest_release.major,
                "minor": next_minor,
                "client_id": client_id,
                "environment": environment
            })
            return Response(status=200, data={"version": new_release.version, "environment": new_release.environment})

        if not latest_release.build_number:
            next_patch = int(latest_release.patch) + 1
            new_release = Release(**{
                "major": latest_release.major, "minor": latest_release.minor, "patch": next_patch,
                "client_id": client_id, "environment": environment
            })
            return Response(status=200, data={"version": new_release.version, "environment": new_release.environment})

        next_build_number = int(latest_release.build_number) + 1
        new_release = Release(**{
            "major": latest_release.major, "minor": latest_release.minor, "patch": latest_release.patch,
            "build_number": next_build_number, "client_id": client_id, "environment": environment
        })
        return Response(status=200, data={"version": new_release.version, "environment": new_release.environment})

    @action(methods=["post"], detail=False)
    def new(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        success_build = validated_data.get("build")
        client_id = validated_data.get("client_id")
        environment = validated_data.get("environment")

        if not success_build:
            return Response(status=200, data={
                "build": success_build, "version": None, "environment": environment
            })

        latest_release = Release.objects.filter(client_id=client_id, environment=environment).order_by('-id').first()
        if not latest_release:
            return Response(status=200, data={"version": "1.0.0", "environment": environment})

        if not latest_release.patch:
            next_minor = int(latest_release.minor) + 1
            new_release = Release.create(**{
                "major": latest_release.major,
                "minor": next_minor,
                "client_id": client_id,
                "environment": environment
            })
            return Response(status=200, data={"version": new_release.version, "environment": new_release.environment})

        if not latest_release.build_number:
            next_patch = int(latest_release.patch) + 1
            new_release = Release.create(**{
                "major": latest_release.major, "minor": latest_release.minor, "patch": next_patch,
                "client_id": client_id, "environment": environment
            })
            return Response(status=200, data={"version": new_release.version, "environment": new_release.environment})

        next_build_number = int(latest_release.build_number) + 1
        new_release = Release.create(**{
            "major": latest_release.major, "minor": latest_release.minor, "patch": latest_release.patch,
            "build_number": next_build_number, "client_id": client_id, "environment": environment
        })
        return Response(status=200, data={"version": new_release.version, "environment": new_release.environment})

