from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from shared.background import LockerBackgroundFactory, BG_EVENT
from shared.constants.event import *
from shared.constants.members import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.team_collection_pwd_permission import TeamCollectionPwdPermission
from cystack_models.models.teams.teams import Team
from shared.services.pm_sync import PwdSync, SYNC_EVENT_COLLECTION_UPDATE, SYNC_EVENT_COLLECTION_DELETE, \
    SYNC_EVENT_VAULT
from v1_0.enterprise.collections.serializers import CollectionSerializer, UpdateCollectionSerializer, \
    UpdateUserCollectionSerializer, DetailCollectionSerializer
from v1_0.enterprise.members.serializers import DetailMemberSerializer
from v1_0.apps import PasswordManagerViewSet


class TeamCollectionPwdViewSet(PasswordManagerViewSet):
    permission_classes = (TeamCollectionPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    serializer_class = CollectionSerializer

    def get_serializer_class(self):
        if self.action in ["users"]:
            self.serializer_class = UpdateUserCollectionSerializer
        elif self.action in ["update"]:
            self.serializer_class = UpdateCollectionSerializer
        elif self.action in ["retrieve"]:
            self.serializer_class = DetailCollectionSerializer

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

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        self.check_pwd_session_auth(request)
        collection_id = kwargs.get("collection_id")
        collection = self.collection_repository.get_multiple_user_collections(
            user=user, filter_ids=[collection_id]
        ).first()
        if not collection:
            raise NotFound
        serializer = DetailCollectionSerializer(collection, many=False, context={"user": user})
        return Response(status=200, data=serializer.data)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        self.check_pwd_session_auth(request)
        team = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        name = validated_data.get("name")
        new_collection = self.collection_repository.save_new_collection(
            team=team, name=name, is_default=False
        )
        PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=[request.user.user_id], team=team, add_all=True).send(
            data={"id": new_collection.id}
        )
        # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
        #     "team_id": team.id, "user_id": user.user_id, "acting_user_id": user.user_id,
        #     "type": EVENT_COLLECTION_CREATED, "collection_id": new_collection.id, "ip_address": ip
        # })
        return Response(status=200, data={"id": new_collection.id})

    def update(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        self.check_pwd_session_auth(request)
        team = self.get_object()
        collection = self.get_collection(team=team)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        name = validated_data.get("name")
        groups = validated_data.get("groups", [])
        valid_groups = team.groups.filter(id__in=groups).values_list('id', flat=True)
        collection = self.collection_repository.save_update_collection(
            collection=collection, name=name, groups=valid_groups
        )
        PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=[request.user.user_id], team=team, add_all=True).send(
            data={"id": collection.id}
        )
        # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
        #     "team_id": team.id, "user_id": user.user_id, "acting_user_id": user.user_id,
        #     "type": EVENT_COLLECTION_UPDATED, "collection_id": collection.id, "ip_address": ip
        # })
        return Response(status=200, data={"id": collection.id, "name": collection.name})

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        ip = request.data.get("ip")
        self.check_pwd_session_auth(request)
        team = self.get_object()
        collection = self.get_collection(team=team)
        self.collection_repository.destroy_collection(collection=collection)
        PwdSync(event=SYNC_EVENT_COLLECTION_DELETE, user_ids=[request.user.user_id], team=team, add_all=True).send()
        # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
        #     "team_id": team.id, "user_id": user.user_id, "acting_user_id": user.user_id,
        #     "type": EVENT_COLLECTION_DELETED, "collection_id": collection.id, "ip_address": ip
        # })
        return Response(status=204)

    @action(methods=["get", "put"], detail=False)
    def users(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request)
        team = self.get_object()
        collection = self.get_collection(team=team)

        if request.method == "GET":
            collection_members = collection.collections_members.all().values_list('member_id', flat=True)
            members = team.team_members.filter(
                Q(id__in=list(collection_members)) | Q(role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN])
            ).distinct()
            members_serializer = DetailMemberSerializer(members, many=True)
            return Response(status=200, data=members_serializer.data)

        elif request.method == "PUT":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            members = validated_data.get("members", [])
            members_obj = team.team_members.filter(
                role_id__in=[MEMBER_ROLE_MEMBER, MEMBER_ROLE_MANAGER],
                team__key__isnull=False,
                id__in=members
            )
            members_data = members_obj.values('id', 'role')
            self.collection_repository.save_update_user_collection(collection, *members_data)
            PwdSync(event=SYNC_EVENT_VAULT, user_ids=[request.user.user_id], team=team).send()
            return Response(status=200, data={"success": True})
