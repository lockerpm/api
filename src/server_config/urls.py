from django.conf.urls import url, include


urlpatterns = [
    url(r'^pm/', include('v1_0.urls')),
    url(r'^pm/ms/', include('micro_services.urls')),
    url(r'^relay/', include('relay.urls')),
]
