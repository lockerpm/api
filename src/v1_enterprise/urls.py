from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from v1_enterprise import views


router = DefaultRouter(trailing_slash=False)
router.register(r'', views.EnterprisePwdViewSet, 'enterprises')

urlpatterns = [
    url(r'^', include(router.urls))
]


# ----------------------------------- Domain ------------------------- #
urlpatterns += [
    url(r'^(?P<pk>[0-9a-z]+)/domains$', views.DomainPwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^(?P<pk>[0-9a-z]+)/domains/(?P<domain_id>[0-9]+)$',
        views.DomainPwdViewSet.as_view({'put': 'update', 'delete': 'destroy'})),
    url(r'^(?P<pk>[0-9a-z]+)/domains/(?P<domain_id>[0-9]+)/verification$',
        views.DomainPwdViewSet.as_view({'get': 'verification', 'post': 'verification'})),
]


# ----------------------------------- Members ------------------------- #
urlpatterns += [
    url(r'^(?P<pk>[0-9a-z]+)/members$', views.MemberPwdViewSet.as_view({'get': 'list'})),
    url(r'^(?P<pk>[0-9a-z]+)/members/multiple$', views.MemberPwdViewSet.as_view({'post': 'create_multiple'})),
    url(r'^(?P<pk>[0-9a-z]+)/members/invitation$', views.MemberPwdViewSet.as_view({'post': 'invitation_multiple'})),
    url(r'^(?P<pk>[0-9a-z]+)/members/(?P<member_id>[a-z0-9\-]+)$',
        views.MemberPwdViewSet.as_view({'put': 'update', 'delete': 'destroy'})),
    url(r'^(?P<pk>[0-9a-z]+)/members/(?P<member_id>[a-z0-9\-]+)/reinvite$',
        views.MemberPwdViewSet.as_view({'post': 'reinvite'})),

    url(r'^members/invitation/confirmation$', views.MemberPwdViewSet.as_view({'get': 'invitation_confirmation'})),
    url(r'^members/invitations$', views.MemberPwdViewSet.as_view({'get': 'user_invitations'})),
    url(r'^members/invitations/(?P<pk>[a-z0-9\-]+)$', views.MemberPwdViewSet.as_view({'put': 'user_invitation_update'})),
]


# ----------------------------------- Policy ------------------------- #
urlpatterns += [
    url(r'^(?P<pk>[0-9a-z]+)/policy$', views.PolicyPwdViewSet.as_view({'get': 'list'})),
    url(r'^(?P<pk>[0-9a-z]+)/policy/(?P<policy_type>[a-z_]+)$',
        views.PolicyPwdViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
]
