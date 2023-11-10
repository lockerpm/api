from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.locker_permissions.affiliate_submission_pwd_permission import \
    AffiliateSubmissionPwdPermission
from locker_server.core.exceptions.affiliate_submission_exception import AffiliateSubmissionDoesNotExistException
from locker_server.core.exceptions.country_exception import CountryDoesNotExistException
from .serializers import ListAffiliateSubmissionSerializer, DetailAffiliateSubmissionSerializer, \
    UpdateAffiliateSubmissionSerializer, CreateAffiliateSubmissionSerializer


class AffiliateSubmissionPwdViewSet(APIBaseViewSet):
    permission_classes = (AffiliateSubmissionPwdPermission,)
    http_method_names = ["head", "options", "get", "post", "put", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            self.serializer_class = ListAffiliateSubmissionSerializer
        elif self.action == "retrieve":
            self.serializer_class = DetailAffiliateSubmissionSerializer
        elif self.action == "update":
            self.serializer_class = UpdateAffiliateSubmissionSerializer
        elif self.action == "create":
            self.serializer_class = CreateAffiliateSubmissionSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        q_param = self.request.query_params.get("q")
        affiliate_submissions = self.affiliate_submission_service.list_affiliate_submissions(**{
            "q": q_param.lower()
        })
        return affiliate_submissions

    def get_object(self):
        try:
            affiliate_submission = self.affiliate_submission_service.get_affiliate_submission_by_id(
                affiliate_submission_id=self.kwargs.get("pk")
            )
            self.check_object_permissions(request=self.request, obj=affiliate_submission)
            return affiliate_submission
        except AffiliateSubmissionDoesNotExistException:
            raise NotFound

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        size_param = self.request.query_params.get("size", 20)
        page_size_param = self.check_int_param(size_param)
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param or 20
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            new_affiliate_submission = self.affiliate_submission_service.create_affiliate_submission(
                affiliate_submission_create_data=validated_data
            )
        except CountryDoesNotExistException:
            raise ValidationError(detail={"country": ["The country does not exist"]})
        data = DetailAffiliateSubmissionSerializer(new_affiliate_submission, many=False).data
        return Response(status=status.HTTP_201_CREATED, data=data)

    def update(self, request, *args, **kwargs):
        affiliate_submission = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            self.affiliate_submission_service.update_affiliate_submission(
                affiliate_submission_id=affiliate_submission.affiliate_submission_id,
                affiliate_submission_update_data=validated_data
            )
        except AffiliateSubmissionDoesNotExistException:
            raise NotFound
        return Response(status=status.HTTP_200_OK, data={"success": True})

    def destroy(self, request, *args, **kwargs):
        affiliate_submission = self.get_object()
        try:
            self.affiliate_submission_service.delete_affiliate_submission(
                affiliate_submission_id=affiliate_submission.affiliate_submission_id
            )
        except AffiliateSubmissionDoesNotExistException:
            raise NotFound
        return Response(status=status.HTTP_204_NO_CONTENT)
