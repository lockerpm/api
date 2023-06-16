from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from cystack_models.models.form_submissions.affiliate_submissions import AffiliateSubmission
from shared.permissions.locker_permissions.form_submission_permission import FormSubmissionPermission
from v1_0.general_view import PasswordManagerViewSet
from v1_0.form_submissions.affiliate_submissions.serializers import AffiliateSubmissionSerializer, \
    UpdateStatusSerializer


class AffiliateSubmissionPwdViewSet(PasswordManagerViewSet):
    permission_classes = (FormSubmissionPermission, )
    http_method_names = ["head", "options", "get", "post", "put", "delete"]
    serializer_class = AffiliateSubmissionSerializer

    def get_serializer_class(self):
        if self.action == "update":
            self.serializer_class = UpdateStatusSerializer
        return super(AffiliateSubmissionPwdViewSet, self).get_serializer_class()

    def get_queryset(self):
        affiliate_submissions = AffiliateSubmission.objects.all().order_by('-created_time')
        q_param = self.request.query_params.get("q")
        if q_param:
            affiliate_submissions = affiliate_submissions.filter(full_name__icontains=q_param.lower())
        return affiliate_submissions

    def get_object(self):
        try:
            affiliate_submission = AffiliateSubmission.objects.get(id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=affiliate_submission)
            return affiliate_submission
        except AffiliateSubmission.DoesNotExist:
            raise NotFound

    def list(self, request, *args, **kwargs):
        page_size_param = self.check_int_param(self.request.query_params.get("size", 20))
        self.pagination_class.page_size = page_size_param if page_size_param else 20
        return super(AffiliateSubmissionPwdViewSet, self).list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        return super(AffiliateSubmissionPwdViewSet, self).retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        new_affiliate_submission = AffiliateSubmission(**validated_data)
        new_affiliate_submission.save()
        return Response(status=201, data={
            "id": new_affiliate_submission.id,
            "full_name": new_affiliate_submission.full_name,
            "email": new_affiliate_submission.email,
            "phone": new_affiliate_submission.phone,
            "company": new_affiliate_submission.company,
            "country": new_affiliate_submission.country
        })

    def update(self, request, *args, **kwargs):
        affiliate_submission = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        status = validated_data.get("status")
        affiliate_submission.status = status
        affiliate_submission.save()
        return Response(status=200, data={"success": True})

    def destroy(self, request, *args, **kwargs):
        affiliate_submission = self.get_object()
        affiliate_submission.delete()
        return Response(status=204)
