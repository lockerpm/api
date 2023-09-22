from rest_framework import serializers

from shared.constants.device_type import *


class NewReleaseSerializer(serializers.Serializer):
    build = serializers.BooleanField()
    client_id = serializers.ChoiceField(
        choices=[CLIENT_ID_BROWSER, CLIENT_ID_DESKTOP, CLIENT_ID_CLI,
                 CLIENT_ID_SDK_PYTHON, CLIENT_ID_SDK_NODEJS, CLIENT_ID_SDK_DOTNET],
        default=CLIENT_ID_DESKTOP
    )
    environment = serializers.ChoiceField(choices=["prod", "staging"], default="prod")


class NextReleaseSerializer(serializers.Serializer):
    client_id = serializers.ChoiceField(
        choices=[CLIENT_ID_BROWSER, CLIENT_ID_DESKTOP, CLIENT_ID_CLI,
                 CLIENT_ID_SDK_PYTHON, CLIENT_ID_SDK_NODEJS, CLIENT_ID_SDK_DOTNET],
        default=CLIENT_ID_DESKTOP
    )
    environment = serializers.ChoiceField(choices=["prod", "staging"], default="prod")
