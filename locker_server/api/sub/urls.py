from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from locker_server.api.sub import views
from locker_server.shared.caching.api_cache_page import LONG_TIME_CACHE

router = DefaultRouter(trailing_slash=False)

urlpatterns = [
    url(r'^', include(router.urls))
]

urlpatterns += [
    url(r'^resources/countries$', LONG_TIME_CACHE(views.ResourcePwdViewSet.as_view({'get': 'countries'}))),
    url(r'^resources/server_type$', views.ResourcePwdViewSet.as_view({'get': 'server_type'})),
    url(r'^resources/cystack_platform/pm/plans$', views.ResourcePwdViewSet.as_view({'get': 'plans'})),
    url(r'^resources/cystack_platform/pm/enterprise/plans$',
        views.ResourcePwdViewSet.as_view({'get': 'enterprise_plans'})),
    url(r'^resources/cystack_platform/pm/mail_providers$',
        views.ResourcePwdViewSet.as_view({'get': 'mail_providers'})),
]

""" User """
urlpatterns += [
    url(r'^me$', views.UserViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    url(r'^users/logout$', views.UserViewSet.as_view({'post': 'logout'})),
]

""" Factor2 """
urlpatterns += [
    url(r'^sso/auth/otp/mail$', views.Factor2ViewSet.as_view({'post': 'auth_otp_mail'})),
    url(r'^sso/me/factor2$', views.Factor2ViewSet.as_view({'get': 'factor2', 'post': 'factor2'})),
    url(r'^sso/me/factor2/activate_code$', views.Factor2ViewSet.as_view({'post': 'factor2_activate_code'})),
    url(r'^sso/me/factor2/activate$', views.Factor2ViewSet.as_view({'post': 'factor2_is_activate'})),
]

""" Notification """
urlpatterns += [
    url(r'^notifications$', views.NotificationViewSet.as_view({'get': 'list'})),
    url(r'^notifications/read_all$', views.NotificationViewSet.as_view({'get': 'read_all'})),
    url(r'^notifications/(?P<id>[0-9a-z-]+)$', views.NotificationViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
]

""" SSO Configuration """
urlpatterns += [
    url(r'^sso_configuration/check_exists$', views.SSOConfigurationViewSet.as_view({'get': 'check_exists'})),
    url(r'^sso_configuration/get_user$', views.SSOConfigurationViewSet.as_view({'post': 'get_user_by_code'}))

]

""" Teams Management """
urlpatterns += [
    url(r'^teams$', views.TeamPwdViewSet.as_view({'get': 'list'}))
]
