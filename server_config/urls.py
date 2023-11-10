from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static

urlpatterns = [
    url(r'^admin/', include('locker_server.api.v1_admin.urls')),
    url(r'^v3/', include('locker_server.api.sub.urls')),
    url(r'^v3/pm/ms/', include('locker_server.api.v1_micro_service.urls')),
    url(r'^v3/cystack_platform/pm/', include('locker_server.api.v1_0.urls')),
    url(r'^v3/cystack_platform/pm/enterprises/', include('locker_server.api.v1_enterprise.urls')),
    # url(r'^v3/cystack_platform/relay/', include('locker_server.api.relay.urls')),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
