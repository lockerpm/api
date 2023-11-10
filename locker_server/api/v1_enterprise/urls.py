from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from locker_server.api.v1_enterprise import views

router = DefaultRouter(trailing_slash=False)
router.register(r'', views.EnterprisePwdViewSet, 'enterprises')

urlpatterns = [
    url(r'^', include(router.urls))
]

# ----------------------------------- Members ------------------------- #
urlpatterns += [
    url(r'^(?P<pk>[0-9a-z]+)/members$', views.MemberPwdViewSet.as_view({'get': 'list'})),
    url(r'^(?P<pk>[0-9a-z]+)/members/multiple$', views.MemberPwdViewSet.as_view({'post': 'create_multiple'})),
    url(r'^(?P<pk>[0-9a-z]+)/members/invitation$', views.MemberPwdViewSet.as_view({'post': 'invitation_multiple'})),
    url(r'^(?P<pk>[0-9a-z]+)/members/(?P<member_id>[a-z0-9\-]+)$',
        views.MemberPwdViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    url(r'^(?P<pk>[0-9a-z]+)/members/(?P<member_id>[a-z0-9\-]+)/reinvite$',
        views.MemberPwdViewSet.as_view({'post': 'reinvite'})),
    url(r'^(?P<pk>[0-9a-z]+)/members/(?P<member_id>[a-z0-9\-]+)/activated$',
        views.MemberPwdViewSet.as_view({'put': 'activated'})),
    url(r'^(?P<pk>[0-9a-z]+)/members/(?P<member_id>[a-z0-9\-]+)/unblock$',
        views.MemberPwdViewSet.as_view({'put': 'unblock'})),

    url(r'^(?P<pk>[0-9a-z]+)/members_groups/search$',
        views.MemberPwdViewSet.as_view({'post': 'search_members_groups'})),
    url(r'^members/invitation/confirmation$', views.MemberPwdViewSet.as_view({'get': 'invitation_confirmation'})),
    url(r'^members/invitations$', views.MemberPwdViewSet.as_view({'get': 'user_invitations'})),
    url(r'^members/invitations/(?P<pk>[a-z0-9\-]+)$',
        views.MemberPwdViewSet.as_view({'put': 'user_invitation_update'})),
]

# ----------------------------------- Policy ------------------------- #
urlpatterns += [
    url(r'^(?P<pk>[0-9a-z]+)/policy$', views.PolicyPwdViewSet.as_view({'get': 'list'})),
    url(r'^(?P<pk>[0-9a-z]+)/policy/(?P<policy_type>[a-z0-9_]+)$',
        views.PolicyPwdViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
]

# ----------------------------------- Groups ------------------------- #
urlpatterns += [
    url(r'^(?P<pk>[0-9a-z]+)/groups$', views.GroupPwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^(?P<pk>[0-9a-z]+)/groups/(?P<group_id>[a-zA-Z0-9\-]+)$',
        views.GroupPwdViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    url(r'^(?P<pk>[0-9a-z]+)/groups/(?P<group_id>[a-zA-Z0-9\-]+)/members$',
        views.GroupPwdViewSet.as_view({'get': 'members', 'put': 'members'})),
    url(r'user_groups$', views.GroupPwdViewSet.as_view({'get': 'user_groups'})),
    url(r'user_groups/(?P<group_id>[a-zA-Z0-9\-]+)/members$',
        views.GroupPwdViewSet.as_view({'get': 'members_list'})),
]

# ----------------------------------- Billing Contacts ------------------------- #
urlpatterns += [
    url(r'^(?P<pk>[0-9a-z]+)/billing_contacts$',
        views.BillingContactViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^(?P<pk>[0-9a-z]+)/billing_contacts/(?P<contact_id>[0-9]+)$',
        views.BillingContactViewSet.as_view({'delete': 'destroy', 'get': 'retrieve'}))
]

# ----------------------------------- Activity Log ------------------------- #
urlpatterns += [
    url(r'^(?P<pk>[0-9a-z]+)/activity$', views.ActivityLogPwdViewSet.as_view({'get': 'list'})),
    url(r'^(?P<pk>[0-9a-z]+)/activity/export$',
        views.ActivityLogPwdViewSet.as_view({'get': 'export', 'post': 'export_to_email'})),
]

# ----------------------------------- Payments ------------------------- #
urlpatterns += [
    url(r'^payments/calc$', views.PaymentPwdViewSet.as_view({'post': 'calc_public'})),
    url(r'^payments/plan$', views.PaymentPwdViewSet.as_view({'post': 'upgrade_plan_public'})),

    url(r'^(?P<pk>[0-9a-z]+)/payments/plan$',
        views.PaymentPwdViewSet.as_view({'get': 'current_plan', 'post': 'upgrade_plan'})),
    url(r'^(?P<pk>[0-9a-z]+)/payments/next_attempt$',
        views.PaymentPwdViewSet.as_view({'get': 'next_attempt'})),
    url(r'^(?P<pk>[0-9a-z]+)/payments/calc$', views.PaymentPwdViewSet.as_view({'post': 'calc'})),
    url(r'^(?P<pk>[0-9a-z]+)/payments/cards$',
        views.PaymentPwdViewSet.as_view({'get': 'cards', 'post': 'add_card_subscription'})),
    url(r'^(?P<pk>[0-9a-z]+)/payments/cards/(?P<card_id>[0-9a-zA-Z_]+)$',
        views.PaymentPwdViewSet.as_view({'put': 'card_set_default'})),
    url(r'^(?P<pk>[0-9a-z]+)/payments/billing_address$',
        views.PaymentPwdViewSet.as_view({'get': 'billing_address', 'put': 'billing_address'})),
    url(r'^(?P<pk>[0-9a-z]+)/payments/invoices$', views.PaymentPwdViewSet.as_view({'get': 'list'})),
    url(r'^(?P<pk>[0-9a-z]+)/payments/invoices/(?P<payment_id>[0-9A-Z]+)$',
        views.PaymentPwdViewSet.as_view({'get': 'retrieve'})),
]
