from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.decorators import action

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.sync_pwd_permission import SyncPwdPermission
from locker_server.core.exceptions.cipher_exception import FolderDoesNotExistException, CipherDoesNotExistException
from locker_server.core.exceptions.collection_exception import CollectionDoesNotExistException
from locker_server.core.exceptions.team_member_exception import TeamMemberDoesNotExistException
from locker_server.shared.caching.sync_cache import SYNC_CACHE_TIMEOUT
from locker_server.shared.constants.account import LOGIN_METHOD_PASSWORDLESS
from locker_server.shared.constants.ciphers import CIPHER_TYPE_MASTER_PASSWORD
from locker_server.shared.constants.members import MEMBER_ROLE_MEMBER
from locker_server.shared.utils.app import camel_snake_data
from .serializers import SyncFolderSerializer, SyncCollectionSerializer, SyncEnterprisePolicySerializer, \
    SyncCipherSerializer, SyncProfileSerializer, SyncOrgDetailSerializer


class SyncPwdViewSet(APIBaseViewSet):
    permission_classes = (SyncPwdPermission,)
    http_method_names = ["head", "options", "get"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["list_group_member_roles_func"] = self.team_member_service.list_group_member_roles
        context["list_member_by_user_func"] = self.team_member_service.list_member_by_user
        return context

    def get_cipher_obj(self):
        try:
            cipher = self.cipher_service.get_by_id(cipher_id=self.kwargs.get("pk"))
            if cipher.team:
                self.check_object_permissions(request=self.request, obj=cipher)
            else:
                if cipher.user and cipher.user.user_id != self.request.user.user_id:
                    raise NotFound
            return cipher
        except CipherDoesNotExistException:
            raise NotFound

    def get_folder_obj(self):
        try:
            folder = self.folder_service.get_by_id(folder_id=self.kwargs.get("pk"))
            if folder.user.user_id != self.request.user.user_id:
                raise NotFound
            return folder
        except FolderDoesNotExistException:
            raise NotFound

    def get_collection_obj(self):
        user = self.request.user
        try:
            user_collections = self.collection_service.list_user_collections(user_id=user.user_id, exclude_team_ids=[])
            for collection in user_collections:
                if collection.collection_id == self.kwargs.get("pk"):
                    return collection
            raise NotFound
        except CollectionDoesNotExistException:
            raise NotFound

    @action(methods=["get"], detail=False)
    def sync(self, request, *args, **kwargs):
        user = self.request.user
        access_token = self.request.auth.access_token
        decode_token = self.auth_service.decode_token(value=access_token, secret=settings.SECRET_KEY)
        self.check_pwd_session_auth(request=request)

        paging_param = self.request.query_params.get("paging", "0")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 50))
        page_param = self.check_int_param(self.request.query_params.get("page", 1))

        # Get sync data from cache
        cache_key = self.user_service.get_sync_cache_key(user_id=user.user_id, page=page_param, size=page_size_param)
        response_cache_data = cache.get(cache_key)
        if response_cache_data:
            return Response(status=status.HTTP_200_OK, data=response_cache_data)

        policies = self.enterprise_service.list_policies_by_user(user_id=user.user_id)

        # Check team policies
        block_team_ids = []

        # Check the login method to exclude
        exclude_types = []
        if user.login_method == LOGIN_METHOD_PASSWORDLESS:
            exclude_types = [CIPHER_TYPE_MASTER_PASSWORD]

        sync_statistic_ciphers = self.cipher_service.sync_and_statistic_ciphers(
            user_id=user.user_id, exclude_team_ids=block_team_ids, exclude_types=exclude_types
        )
        statistic_count = sync_statistic_ciphers.get("count")
        ciphers = sync_statistic_ciphers.get("ciphers")

        if paging_param == "0":
            ciphers_page = ciphers
        else:
            try:
                paginator = Paginator(list(ciphers), page_size_param or 50)
                ciphers_page = paginator.page(page_param).object_list
            except EmptyPage:
                ciphers_page = []

        ciphers_serializer = SyncCipherSerializer(ciphers_page, many=True, context={"user": user})
        folders = self.folder_service.get_multiple_by_user(user_id=user.user_id)
        collections = self.collection_service.list_user_collections(
            user_id=user.user_id, exclude_team_ids=block_team_ids
        )
        sync_data = {
            "object": "sync",
            "count": statistic_count,
            "profile": SyncProfileSerializer(user, many=False, context=self.get_serializer_context()).data,
            "ciphers": ciphers_serializer.data,
            "collections": SyncCollectionSerializer(collections, many=True, context={"user": user}).data,
            "folders": SyncFolderSerializer(folders, many=True).data,
            "domains": None,
            "policies": SyncEnterprisePolicySerializer(policies, many=True).data,
            "sends": []
        }
        if settings.SELF_HOSTED:
            sync_data["profile"]["email"] = user.email
            sync_data["profile"]["name"] = user.full_name
        sync_data["profile"].update({
            "key": decode_token.get("credential_key", user.key)
        })
        sync_data = camel_snake_data(sync_data, snake_to_camel=True)
        cache.set(cache_key, sync_data, SYNC_CACHE_TIMEOUT)
        return Response(status=status.HTTP_200_OK, data=sync_data)

    @action(methods=["get"], detail=False)
    def sync_count(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        # Check team policies
        block_team_ids = []
        # Check the login method to exclude
        exclude_types = []
        if user.login_method == LOGIN_METHOD_PASSWORDLESS:
            exclude_types = [CIPHER_TYPE_MASTER_PASSWORD]

        sync_statistic_ciphers = self.cipher_service.sync_and_statistic_ciphers(
            user_id=user.user_id, exclude_team_ids=block_team_ids, exclude_types=exclude_types
        )
        statistic_count = sync_statistic_ciphers.get("count")
        total_folders = len(self.folder_service.get_multiple_by_user(user_id=user.user_id))
        total_collections = len(self.collection_service.list_user_collections(
            user_id=user.user_id, exclude_team_ids=block_team_ids
        ))
        statistic_count.update({
            "folders": total_folders,
            "collections": total_collections
        })
        sync_count_data = {
            "object": "sync_count",
            "count": statistic_count
        }
        sync_count_data = camel_snake_data(sync_count_data, snake_to_camel=True)
        return Response(status=status.HTTP_200_OK, data=sync_count_data)

    @action(methods=["get"], detail=False)
    def sync_ciphers(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)

        paging_param = self.request.query_params.get("paging", "0")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 50))
        page_param = self.check_int_param(self.request.query_params.get("page", 1))
        # Check team policies
        block_team_ids = []
        # for policy in policies:
        #     check_policy = self.team_repository.check_team_policy(request=request, team=policy.team)
        #     if check_policy is False:
        #         block_team_ids.append(policy.team_id)

        # Check the login method to exclude
        exclude_types = []
        if user.login_method == LOGIN_METHOD_PASSWORDLESS:
            exclude_types = [CIPHER_TYPE_MASTER_PASSWORD]

        sync_statistic_ciphers = self.cipher_service.sync_and_statistic_ciphers(
            user_id=user.user_id, exclude_team_ids=block_team_ids, exclude_types=exclude_types
        )
        ciphers = sync_statistic_ciphers.get("ciphers")

        if paging_param == "0":
            ciphers_page = ciphers
        else:
            try:
                paginator = Paginator(list(ciphers), page_size_param or 50)
                ciphers_page = paginator.page(page_param).object_list
            except EmptyPage:
                ciphers_page = []
        serializer = SyncCipherSerializer(ciphers_page, many=True, context={"user": user})
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def sync_cipher_detail(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        cipher = self.get_cipher_obj()
        # Check permission
        try:
            cipher_obj = self.cipher_service.get_multiple_by_user(
                user_id=user.user_id, filter_ids=[cipher.cipher_id]
            )[0]
        except IndexError:
            raise NotFound
        serializer = SyncCipherSerializer(cipher_obj, context={"user": user}, many=False)
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def sync_folders(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        user = self.request.user
        folders = self.folder_service.get_multiple_by_user(user_id=user.user_id)
        serializer = SyncFolderSerializer(folders, many=True)
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def sync_folder_detail(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        folder = self.get_folder_obj()
        serializer = SyncFolderSerializer(folder, many=False)
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def sync_collections(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        # Check team policies
        block_team_ids = []
        collections = self.collection_service.list_user_collections(
            user_id=user.user_id, exclude_team_ids=block_team_ids
        )
        serializer = SyncCollectionSerializer(collections, many=True, context={"user": user})
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def sync_collection_detail(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        collection = self.get_collection_obj()
        serializer = SyncCollectionSerializer(collection, many=False, context={"user": user})
        serializer_data = serializer.data
        role_id = self.team_member_service.get_role_notify(
            user_id=user.user_id, team_id=collection.team.team_id
        ).get("role")
        serializer_data["read_only"] = True if role_id == MEMBER_ROLE_MEMBER else False
        result = camel_snake_data(serializer_data, snake_to_camel=True)
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def sync_profile_detail(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        access_token = self.request.auth.access_token
        decode_token = self.auth_service.decode_token(value=access_token, secret=settings.SECRET_KEY)
        serializer = SyncProfileSerializer(user, many=False, context=self.get_serializer_context())
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        if settings.SELF_HOSTED:
            result["email"] = user.email
            result["name"] = user.full_name
        result.update({
            "key": decode_token.get("credential_key", user.key)
        })
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def sync_org_detail(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        try:
            team_member = self.team_member_service.get_team_member(user_id=user.user_id, team_id=kwargs.get("pk"))
        except TeamMemberDoesNotExistException:
            raise NotFound
        serializer = SyncOrgDetailSerializer(team_member, many=False, context=self.get_serializer_context())
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=status.HTTP_200_OK, data=result)

    @action(methods=["get"], detail=False)
    def sync_policies(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        policies = self.enterprise_service.list_policies_by_user(user_id=user.user_id)
        serializer = SyncEnterprisePolicySerializer(policies, many=True)
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=status.HTTP_200_OK, data=result)
