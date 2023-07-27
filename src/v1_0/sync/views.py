from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Count
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.decorators import action

from core.utils.data_helpers import camel_snake_data
from shared.constants.account import LOGIN_METHOD_PASSWORDLESS
from shared.constants.ciphers import CIPHER_TYPE_MASTER_PASSWORD
from shared.permissions.locker_permissions.sync_pwd_permission import SyncPwdPermission
from v1_0.sync.serializers import SyncProfileSerializer, SyncCipherSerializer, SyncFolderSerializer, \
    SyncCollectionSerializer, SyncPolicySerializer, SyncOrgDetailSerializer, SyncEnterprisePolicySerializer
from v1_0.general_view import PasswordManagerViewSet


class SyncPwdViewSet(PasswordManagerViewSet):
    permission_classes = (SyncPwdPermission, )
    http_method_names = ["head", "options", "get"]

    def get_cipher_obj(self):
        try:
            cipher = self.cipher_repository.get_by_id(cipher_id=self.kwargs.get("pk"))
            if cipher.team:
                self.check_object_permissions(request=self.request, obj=cipher)
            else:
                if cipher.user != self.request.user:
                    raise NotFound
            return cipher
        except ObjectDoesNotExist:
            raise NotFound

    def get_folder_obj(self):
        try:
            folder = self.folder_repository.get_by_id(folder_id=self.kwargs.get("pk"), user=self.request.user)
            return folder
        except ObjectDoesNotExist:
            raise NotFound

    def get_collection_obj(self):
        user = self.request.user
        try:
            collections = self.collection_repository.get_multiple_user_collections(
                user=user, exclude_team_ids=[]
            ).select_related('team')
            collection = collections.get(id=self.kwargs.get("pk"))
            return collection
        except ObjectDoesNotExist:
            raise NotFound

    @action(methods=["get"], detail=False)
    def sync(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)

        paging_param = self.request.query_params.get("paging", "0")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 50))
        page_param = self.check_int_param(self.request.query_params.get("page", 1))
        # if paging_param == "0":
        #     self.pagination_class = None
        # else:
        #     self.pagination_class.page_size = page_size_param if page_size_param else 50

        policies = self.team_repository.get_multiple_policy_by_user(user=user).select_related('enterprise')
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

        ciphers = self.cipher_repository.get_multiple_by_user(
            user=user, exclude_team_ids=block_team_ids, exclude_types=exclude_types
        ).order_by('-revision_date').prefetch_related('collections_ciphers')
        total_cipher = ciphers.count()
        not_deleted_ciphers = ciphers.filter(deleted_date__isnull=True)
        not_deleted_ciphers_statistic = not_deleted_ciphers.values('type').annotate(
            count=Count('type')
        ).order_by('-count')
        not_deleted_ciphers_count = {item["type"]: item["count"] for item in list(not_deleted_ciphers_statistic)}
        # ciphers_page = self.paginate_queryset(ciphers)
        if paging_param == "0":
            ciphers_page = ciphers
        else:
            try:
                paginator = Paginator(list(ciphers), page_size_param or 50)
                ciphers_page = paginator.page(page_param).object_list
            except EmptyPage:
                ciphers_page = []

        ciphers_serializer = SyncCipherSerializer(ciphers_page, many=True, context={"user": user})

        folders = self.folder_repository.get_multiple_by_user(user=user)
        collections = self.collection_repository.get_multiple_user_collections(
            user=user, exclude_team_ids=block_team_ids
        ).select_related('team')

        sync_data = {
            "object": "sync",
            "count": {
                "ciphers": total_cipher,
                "not_deleted_ciphers": {
                    "total": not_deleted_ciphers.count(),
                    "ciphers": not_deleted_ciphers_count
                },
            },
            "profile": SyncProfileSerializer(user, many=False).data,
            "ciphers": ciphers_serializer.data,
            "collections": SyncCollectionSerializer(collections, many=True, context={"user": user}).data,
            "folders": SyncFolderSerializer(folders, many=True).data,
            "domains": None,
            "policies": SyncEnterprisePolicySerializer(policies, many=True).data,
            "sends": []
        }
        sync_data = camel_snake_data(sync_data, snake_to_camel=True)
        return Response(status=200, data=sync_data)

    @action(methods=["get"], detail=False)
    def sync_cipher_detail(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        cipher = self.get_cipher_obj()
        cipher_obj = self.cipher_repository.get_multiple_by_user(
            user=user, filter_ids=[cipher.id]
        ).prefetch_related('collections_ciphers').first()
        serializer = SyncCipherSerializer(cipher_obj, context={"user": user}, many=False)
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=200, data=result)

    @action(methods=["get"], detail=False)
    def sync_folder_detail(self, request, *args, **kwargs):
        self.check_pwd_session_auth(request=request)
        folder = self.get_folder_obj()
        serializer = SyncFolderSerializer(folder, many=False)
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=200, data=result)

    @action(methods=["get"], detail=False)
    def sync_collection_detail(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        collection = self.get_collection_obj()
        serializer = SyncCollectionSerializer(collection, many=False, context={"user": user}).data
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=200, data=result)

    @action(methods=["get"], detail=False)
    def sync_profile_detail(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        serializer = SyncProfileSerializer(user, many=False)
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=200, data=result)

    @action(methods=["get"], detail=False)
    def sync_org_detail(self, request, *args, **kwargs):
        user = self.request.user
        self.check_pwd_session_auth(request=request)
        try:
            team_member = user.team_members.get(team_id=kwargs.get("pk"), team__key__isnull=False)
        except ObjectDoesNotExist:
            raise NotFound

        serializer = SyncOrgDetailSerializer(team_member, many=False)
        result = camel_snake_data(serializer.data, snake_to_camel=True)
        return Response(status=200, data=result)
