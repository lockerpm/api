from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from locker_server.api.v1_admin import views

router = DefaultRouter(trailing_slash=False)
router.register(r'enterprises', views.AdminEnterpriseViewSet, "admin_enterprise")
router.register(
    r'enterprises/(?P<enterprise_id>[0-9a-z-]+)/members', views.AdminEnterpriseMemberViewSet,
    "admin_enterprise_member"
)
urlpatterns = [
    url(r'^', include(router.urls))
]

# ------------------------------- Mail Configuration ----------------------------- #
urlpatterns += [
    url(r'^mail_configuration$', views.AdminMailConfigurationViewSet.as_view({
        'get': 'mail_configuration', 'put': 'update_mail_configuration', 'delete': 'destroy_mail_configuration'
    })),
    url(r'^mail_configuration/test$', views.AdminMailConfigurationViewSet.as_view({'post': 'send_test_mail'}))
]
# ------------------------------- SSO Configuration ----------------------------- #
urlpatterns += [
    url(r'^sso_configuration$', views.AdminSSOConfigurationViewSet.as_view({
        'get': 'sso_configuration', 'put': 'update_sso_configuration', 'delete': 'destroy_sso_configuration'
    }))
]
