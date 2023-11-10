from rest_framework import serializers


class ListActivityLogSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.event_id,
            "type": instance.event_type,
            "creation_date": instance.creation_date,
            "ip_address": instance.ip_address,
            "cipher_id": instance.cipher_id,
            "collection_id": instance.collection_id,
            "device_type": instance.device_type,
            "group_id": instance.group_id,
            "enterprise_id": instance.team_id,
            "enterprise_member_id": instance.team_member_id,
            "metadata": instance.get_metadata(),
        }
        if instance.user:
            user = instance.user
            data.update({
                "user": {
                    "id": instance.user_id,
                    "name": user.full_name,
                    "email": user.email,
                    #TODO: add username, avatar
                    # "username": user.username,
                    # "avatar": user.avatar,
                }
            })
        else:
            data.update({
                "user": None
            })
        if instance.acting_user:
            acting_user = instance.acting_user
            data.update({
                "acting_user": {
                    "id": instance.acting_user,
                    "name": acting_user.full_name,
                    "email": acting_user.email,
                    #TODO: add username, avatar
                    # "username": acting_user.username,
                    # "avatar": acting_user.avatar,
                }
            })
        else:
            data.update({
                "acting_user": {
                    "name": "System",
                    "email": None,
                    "username": "System",
                    "avatar": None,
                }
            })
        use_html = self.context.get("use_html", True)
        data.update({
            "description": instance.get_description(use_html=use_html)
        })
        return data


class DetailActivityLogSerializer(ListActivityLogSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


class ExportActivityLogSerializer(ListActivityLogSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)


class ExportEmailActivityLogSerializer(serializers.Serializer):
    cc = serializers.ListSerializer(child=serializers.EmailField(), allow_empty=True, required=False)

    def to_internal_value(self, data):
        if data.get("cc") is None:
            data["cc"] = []
        return super(ExportEmailActivityLogSerializer, self).to_internal_value(data)
