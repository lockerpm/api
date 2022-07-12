from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from v1_enterprise import views


router = DefaultRouter(trailing_slash=False)
router.register(r'teams', views.TeamPwdViewSet, 'teams')

urlpatterns = [
    url(r'^', include(router.urls))
]


# ----------------------------------- Domain ------------------------- #
urlpatterns += [
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/domains$', views.DomainPwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/domains/(?P<domain_id>[0-9]+)$',
        views.DomainPwdViewSet.as_view({'delete': 'destroy'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/domains/(?P<domain_id>[0-9]+)/verification$',
        views.DomainPwdViewSet.as_view({'get': 'verification', 'post': 'verification'})),

]
