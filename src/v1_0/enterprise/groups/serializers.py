# from rest_framework import serializers
#
# from cystack_models.models.teams.groups import Group
#
#
# class GroupSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Group
#         fields = ('id', 'access_all', 'external_id', 'creation_date', 'revision_date', 'name')
#         read_only_fields = ('id', 'external_id', 'creation_date', 'revision_date')
#
#     def to_representation(self, instance):
#         data = super(GroupSerializer, self).to_representation(instance)
#         data["object"] = "group"
#         data["organization_id"] = instance.team_id
#         return data
#
#
# class UpdateGroupSerializer(serializers.Serializer):
#     name = serializers.CharField(required=True)
#     access_all = serializers.BooleanField()
#     collections = serializers.ListField(
#         child=serializers.CharField(max_length=128), allow_empty=True, allow_null=True
#     )
#
#     def validate(self, data):
#         access_all = data.get("access_all")
#         if access_all:
#             data["collections"] = []
#         else:
#             collections = data.get("collections", [])
#             data["collections"] = [{
#                 "id": collection_id,
#                 "hide_passwords": False,
#                 "read_only": False
#             } for collection_id in collections]
#         return data
#
