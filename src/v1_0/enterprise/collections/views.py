from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, When, Q, Case, IntegerField
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.team_collection_pwd_permission import TeamCollectionPwdPermission
from cystack_models.models.teams.teams import Team
from v1_0.enterprise.collections.serializers import CollectionSerializer
from v1_0.apps import PasswordManagerViewSet


class TeamCollectionPwdViewSet(PasswordManagerViewSet):
    permission_classes = (TeamCollectionPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    serializer_class = CollectionSerializer

    def get_serializer_class(self):
        if self.action in ["users"]:
            self.serializer_class = None

        return super(TeamCollectionPwdViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            team = self.team_repository.get_vault_team_by_id(team_id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=team)
            if self.action in ["create", "update"]:
                if self.team_repository.is_locked(team=team):
                    raise ValidationError({"non_field_errors": [gen_error("3003")]})
            return team
        except Team.DoesNotExist:
            raise NotFound

    def get_collection(self, team):
        try:
            team_collection = self.collection_repository.get_team_collection_by_id(
                collection_id=self.kwargs.get("folder_id"), team_id=team.id
            )
            return team_collection
        except ObjectDoesNotExist:
            raise NotFound

    def list(self, request, *args, **kwargs):
        team = self.get_object()
        collections = self.collection_repository.get_multiple_team_collections(team_id=team.id)
        serializer = self.get_serializer(collections, many=True)
        return Response(status=200, data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        team = self.get_object()
        collection = self.get_collection(team=team)
        serializer = self.get_serializer(collection, many=False)
        return Response(status=200, data=serializer.data)

    def create(self, request, *args, **kwargs):
        team = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        name = validated_data.get("name")
        new_collection = self.collection_repository.save_new_collection(
            team=team, name=name, is_default=False
        )
        return Response(status=200, data={"id": new_collection.id})

