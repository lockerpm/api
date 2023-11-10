from rest_framework import serializers

from locker_server.shared.constants.lang import LANG_ENGLISH, LANG_VIETNAM


class UserMeSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "email": instance.email,
            "full_name": instance.full_name,
            "language": instance.language,
            "avatar": instance.get_avatar()
        }
        return data


class UpdateMeSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=[LANG_ENGLISH, LANG_VIETNAM], required=False)
    full_name = serializers.CharField(required=False)
