from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from relay import views


router = DefaultRouter(trailing_slash=False)
router.register(r'addresses', views.RelayAddressViewSet, 'addresses')


urlpatterns = [
    url(r'^', include(router.urls))
]


# ----------------------- Hooks ----------------------- #
urlpatterns += [
    url(r'^hook$', views.RelayHookViewSet.as_view({'post': 'sendgrid_hook'})),
]
