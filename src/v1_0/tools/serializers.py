from rest_framework import serializers


class BreachSerializer(serializers.Serializer):
    email = serializers.EmailField()