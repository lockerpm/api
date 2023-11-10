from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from locker_server.api.v1_micro_service import views
from locker_server.shared.caching.api_cache_page import LONG_TIME_CACHE


router = DefaultRouter(trailing_slash=False)
router.register(r'users', views.UserViewSet, "users")


urlpatterns = [
    url(r'^', include(router.urls))
]

# ----------------------- Payments --------------------------- #
urlpatterns += [

]

