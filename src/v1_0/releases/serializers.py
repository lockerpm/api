from rest_framework import serializers

from shared.constants.device_type import CLIENT_ID_BROWSER, CLIENT_ID_DESKTOP, CLIENT_ID_CLI


class NewReleaseSerializer(serializers.Serializer):
    build = serializers.BooleanField()
    client_id = serializers.ChoiceField(
        choices=[CLIENT_ID_BROWSER, CLIENT_ID_DESKTOP, CLIENT_ID_CLI],
        default=CLIENT_ID_DESKTOP
    )
    environment = serializers.ChoiceField(choices=["prod", "staging"], default="prod")


class NextReleaseSerializer(serializers.Serializer):
    client_id = serializers.ChoiceField(
        choices=[CLIENT_ID_BROWSER, CLIENT_ID_DESKTOP, CLIENT_ID_CLI],
        default=CLIENT_ID_DESKTOP
    )
    environment = serializers.ChoiceField(choices=["prod", "staging"], default="prod")
