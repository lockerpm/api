from rest_framework import serializers


class ClaimSerializer(serializers.Serializer):
    referred_by = serializers.IntegerField()
    count = serializers.IntegerField(default=1)

