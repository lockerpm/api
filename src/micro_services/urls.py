from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from micro_services import views


router = DefaultRouter(trailing_slash=False)
router.register(r'sync/teams', views.SyncTeamViewSet, "teams")


urlpatterns = [
    url(r'^', include(router.urls))
]
