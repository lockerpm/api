# from django.core.exceptions import ObjectDoesNotExist
# from django.db.models import Q
# from rest_framework.response import Response
# from rest_framework.decorators import action
# from rest_framework.exceptions import NotFound, ValidationError
#
# from shared.background import LockerBackgroundFactory, BG_EVENT
# from shared.constants.event import *
# from shared.constants.members import *
# from shared.error_responses.error import gen_error
# from shared.permissions.locker_permissions.group_pwd_permission import GroupPwdPermission
# from shared.services.pm_sync import PwdSync, SYNC_EVENT_GROUP_CREATE, SYNC_EVENT_GROUP_DELETE, SYNC_EVENT_GROUP_UPDATE
# from v1_0.enterprise.groups.serializers import GroupSerializer, UpdateGroupSerializer
# from v1_0.enterprise.members.serializers import DetailMemberSerializer
# from v1_0.apps import PasswordManagerViewSet
#
#
# class GroupPwdViewSet(PasswordManagerViewSet):
#     permission_classes = (GroupPwdPermission, )
#     http_method_names = ["head", "options", "get", "post", "put", "delete"]
#     serializer_class = GroupSerializer
#
#     def get_serializer_class(self):
#         if self.action in ["create", "update"]:
#             self.serializer_class = UpdateGroupSerializer
#         return super(GroupPwdViewSet, self).get_serializer_class()
#
#     def get_object(self):
#         try:
#             team = self.team_repository.get_vault_team_by_id(team_id=self.kwargs.get("pk"))
#             self.check_object_permissions(request=self.request, obj=team)
#             if self.action in ["create", "update"]:
#                 if self.team_repository.is_locked(team=team):
#                     raise ValidationError({"non_field_errors": [gen_error("3003")]})
#             return team
#         except ObjectDoesNotExist:
#             raise NotFound
#
#     def get_group(self, team):
#         try:
#             team_group = self.group_repository.get_team_group_by_id(
#                 group_id=self.kwargs.get("group_id"), team_id=team.id
#             )
#             return team_group
#         except ObjectDoesNotExist:
#             raise NotFound
#
#     def list(self, request, *args, **kwargs):
#         self.check_pwd_session_auth(request)
#         team = self.get_object()
#         groups = self.group_repository.get_multiple_by_team_id(team_id=team.id)
#         serializer = self.get_serializer(groups, many=True)
#         return Response(status=200, data=serializer.data)
#
#     def create(self, request, *args, **kwargs):
#         user = self.request.user
#         ip = request.data.get("ip")
#         self.check_pwd_session_auth(request)
#         team = self.get_object()
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         validated_data = serializer.validated_data
#         name = validated_data.get("name")
#         access_all = validated_data.get("access_all")
#         collections = validated_data.get("collections", [])
#         new_group = self.group_repository.save_new_group(
#             team=team, name=name, access_all=access_all, collections=collections
#         )
#         PwdSync(event=SYNC_EVENT_GROUP_CREATE, user_ids=[request.user.user_id], team=team, add_all=True).send()
#         # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
#         #     "team_id": team.id, "user_id": user.user_id, "acting_user_id": user.user_id,
#         #     "type": EVENT_GROUP_CREATED, "collection_id": new_group.id, "ip_address": ip
#         # })
#         return Response(status=200, data={"id": new_group.id})
#
#     def retrieve(self, request, *args, **kwargs):
#         self.check_pwd_session_auth(request)
#         team = self.get_object()
#         group = self.get_group(team=team)
#         result = {
#             "object": "groupDetails",
#             "id": group.id,
#             "name": group.name,
#             "external_id": group.external_id,
#             "access_all": group.access_all,
#             "organization_id": group.team_id,
#             "collections": group.collections_groups.all().values_list('collection_id', flat=True)
#         }
#         return Response(status=200, data=result)
#
#     def update(self, request, *args, **kwargs):
#         user = self.request.user
#         ip = request.data.get("ip")
#         self.check_pwd_session_auth(request)
#         team = self.get_object()
#         group = self.get_group(team=team)
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         validated_data = serializer.validated_data
#         name = validated_data.get("name")
#         access_all = validated_data.get("access_all")
#         collections = validated_data.get("collections", [])
#         updated_group = self.group_repository.save_update_group(
#             group=group, name=name, access_all=access_all, collections=collections
#         )
#         PwdSync(event=SYNC_EVENT_GROUP_UPDATE, user_ids=[request.user.user_id], team=team, add_all=True).send()
#         # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
#         #     "team_id": team.id, "user_id": user.user_id, "acting_user_id": user.user_id,
#         #     "type": EVENT_GROUP_UPDATED, "group_id": group.id, "ip_address": ip
#         # })
#         return Response(status=200, data={"id": updated_group.id})
#
#     def destroy(self, request, *args, **kwargs):
#         user = self.request.user
#         ip = request.data.get("ip")
#         self.check_pwd_session_auth(request)
#         team = self.get_object()
#         group = self.get_group(team=team)
#         group_id = group.id
#         group.delete()
#         PwdSync(event=SYNC_EVENT_GROUP_DELETE, user_ids=[request.user.user_id], team=team, add_all=True).send()
#         # LockerBackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create", **{
#         #     "team_id": team.id, "user_id": user.user_id, "acting_user_id": user.user_id,
#         #     "type": EVENT_GROUP_DELETED, "collection_id": group_id, "ip_address": ip
#         # })
#         return Response(status=204)
#
#     @action(methods=["get", "put"], detail=False)
#     def users(self, request, *args, **kwargs):
#         self.check_pwd_session_auth(request)
#         team = self.get_object()
#         group = self.get_group(team=team)
#
#         if request.method == "GET":
#             group_members = list(group.groups_members.all().order_by('member_id').values_list('member_id', flat=True))
#             members = team.team_members.filter(
#                 Q(id__in=list(group_members)) | Q(role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN])
#             ).distinct()
#             serializer = DetailMemberSerializer(members, many=True)
#             return Response(status=200, data=serializer.data)
#
#         elif request.method == "PUT":
#             # List member ids
#             members = request.data.get("members", [])
#             member_ids = team.team_members.filter(
#                 role_id__in=[MEMBER_ROLE_MEMBER, MEMBER_ROLE_MANAGER],
#                 team__key__isnull=False,
#                 id__in=members
#             ).values_list('id', flat=True)
#             updated_group = self.group_repository.save_update_user_group(group, list(member_ids))
#             return Response(status=200, data={"success": True})
