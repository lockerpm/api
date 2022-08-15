from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from relay import views


router = DefaultRouter(trailing_slash=False)
router.register(r'addresses', views.RelayAddressViewSet, 'addresses')
router.register(r'subdomains', views.RelaySubdomainViewSet, 'subdomains')


urlpatterns = [
    url(r'^', include(router.urls))
]


# ----------------------- Hooks ----------------------- #
urlpatterns += [
    url(r'^hook$', views.RelayHookViewSet.as_view({'post': 'sendgrid_hook'})),
    url(r'^destination$', views.RelayHookViewSet.as_view({'get': 'destination'})),
    url(r'^reply$', views.RelayHookViewSet.as_view({'get': 'reply', 'post': 'reply'})),
]
