from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from v1_0 import views

router = DefaultRouter(trailing_slash=False)


urlpatterns = [
    url(r'^', include(router.urls))
]


# ----------------------------------- Users ----------------------------- #
urlpatterns += [
    # url(r'^users/me$', views.UserPwdViewSet.as_view({'get': 'me', 'put': 'me'})),
    # url(r'^users/me/family', views.UserPwdViewSet.as_view({'get': 'family'})),
    # url(r'^users/me/delete$', views.UserPwdViewSet.as_view({'post': 'delete_me'})),
    # url(r'^users/me/purge$', views.UserPwdViewSet.as_view({'post': 'purge_me'})),
    # url(r'^users/me/password$', views.UserPwdViewSet.as_view({'post': 'password'})),
    # url(r'^users/password_hint$', views.UserPwdViewSet.as_view({'post': 'password_hint'})),
    url(r'^users/register$', views.UserPwdViewSet.as_view({'post': 'register'})),
    url(r'^users/prelogin$', views.UserPwdViewSet.as_view({'post': 'prelogin'})),
    # url(r'^users/session$', views.UserPwdViewSet.as_view({'post': 'session'})),
    # url(r'^users/session/revoke_all$', views.UserPwdViewSet.as_view({'post': 'revoke_all_sessions'})),
    # url(r'^users/profile$', views.UserPwdViewSet.as_view({'get': 'profile'})),
    # url(r'^users/(?P<pk>[0-9]+)/public_key$', views.UserPwdViewSet.as_view({'get': 'public_key'})),
    # url(r'^users/invitations$', views.UserPwdViewSet.as_view({'get': 'invitation'})),
    # url(r'^users/invitations/(?P<pk>[0-9]+)$', views.UserPwdViewSet.as_view({'put': 'invitation_update'})),

]
