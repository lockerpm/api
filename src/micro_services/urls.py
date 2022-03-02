from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from micro_services import views


router = DefaultRouter(trailing_slash=False)
router.register(r'sync/teams', views.SyncTeamViewSet, "teams")
router.register(r'users', views.UserViewSet, "users")


urlpatterns = [
    url(r'^', include(router.urls))
]


# ----------------------- Payments --------------------------- #
urlpatterns += [
    url(r'^payments/webhook/invoices$', views.PaymentViewSet.as_view({'post': 'webhook_create'})),
    url(r'^payments/webhook/invoices/(?P<pk>[A-Z0-9]+)/status$',
        views.PaymentViewSet.as_view({'post': 'webhook_set_status'})),
    url(r'^payments/webhook/customers/(?P<pk>[a-zA-Z0-9\_]+)$',
        views.PaymentViewSet.as_view({'post': 'webhook_unpaid_subscription', 'put': 'webhook_cancel_subscription'})),
    url(r'^payments/banking/callback$', views.PaymentViewSet.as_view({'post': 'banking_callback'})),
    url(r'^payments/referral$', views.PaymentViewSet.as_view({'post': 'referral_payment'})),

    url(r'^payments/webhook/ios/validate$', views.MobilePaymentViewSet.as_view({'post': 'upgrade_plan'})),
]