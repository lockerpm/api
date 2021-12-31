from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from v1_0 import views

router = DefaultRouter(trailing_slash=False)


urlpatterns = [
    url(r'^', include(router.urls))
]


# ----------------------------------- Resources ----------------------------- #
urlpatterns += [
    url(r'^resources/plans$', views.ResourcePwdViewSet.as_view({'get': 'plans'})),
]


# ----------------------------------- Tools ----------------------------- #
urlpatterns += [
    url(r'^tools/breach$', views.ToolPwdViewSet.as_view({'post': 'breach'})),
]

# ----------------------------------- Users ----------------------------- #
urlpatterns += [
    url(r'^users/me$', views.UserPwdViewSet.as_view({'get': 'me', 'put': 'me'})),
    url(r'^users/me/revision_date$', views.UserPwdViewSet.as_view({'get': 'revision_date'})),
    url(r'^users/me/family', views.UserPwdViewSet.as_view({'get': 'family'})),
    url(r'^users/me/delete$', views.UserPwdViewSet.as_view({'post': 'delete_me'})),
    url(r'^users/me/purge$', views.UserPwdViewSet.as_view({'post': 'purge_me'})),
    url(r'^users/me/password$', views.UserPwdViewSet.as_view({'post': 'password'})),
    url(r'^users/me/fcm_id$', views.UserPwdViewSet.as_view({'post': 'fcm_id'})),
    url(r'^users/me/devices$', views.UserPwdViewSet.as_view({'get': 'devices'})),
    url(r'^users/password_hint$', views.UserPwdViewSet.as_view({'post': 'password_hint'})),
    url(r'^users/register$', views.UserPwdViewSet.as_view({'post': 'register'})),
    url(r'^users/prelogin$', views.UserPwdViewSet.as_view({'post': 'prelogin'})),
    url(r'^users/session$', views.UserPwdViewSet.as_view({'post': 'session'})),
    url(r'^users/session/revoke_all$', views.UserPwdViewSet.as_view({'post': 'revoke_all_sessions'})),
    url(r'^users/invitations$', views.UserPwdViewSet.as_view({'get': 'invitations'})),
    url(r'^users/invitations/(?P<pk>[a-z0-9\-]+)$', views.UserPwdViewSet.as_view({'put': 'invitation_update'})),

]


# -------------------------------- Sync ----------------------------------- #
urlpatterns += [
    url(r'^sync', views.SyncPwdViewSet.as_view({'get': 'sync'})),
]


# -------------------------------- Ciphers ------------------------------- #
urlpatterns += [
    url(r'^ciphers/vaults$', views.CipherPwdViewSet.as_view({'post': 'vaults'})),
    url(r'^ciphers/permanent_delete$', views.CipherPwdViewSet.as_view({'put': 'multiple_permanent_delete'})),
    url(r'^ciphers/delete$', views.CipherPwdViewSet.as_view({'put': 'multiple_delete'})),
    url(r'^ciphers/restore$', views.CipherPwdViewSet.as_view({'put': 'multiple_restore'})),
    url(r'^ciphers/move$', views.CipherPwdViewSet.as_view({'put': 'multiple_move'})),
    url(r'^ciphers/import$', views.CipherPwdViewSet.as_view({'post': 'import_data'})),
    url(r'^ciphers/sync/offline$', views.CipherPwdViewSet.as_view({'post': 'sync_offline'})),
    url(r'^ciphers/(?P<pk>[0-9a-z\-]+)$', views.CipherPwdViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    url(r'^ciphers/(?P<pk>[0-9a-z\-]+)/share$', views.CipherPwdViewSet.as_view({'put': 'share'})),

]


# -------------------------------- Cipher Sharing ------------------------------- #
urlpatterns += [
    url(r'^sharing/public_key$', views.SharingPwdViewSet.as_view({'post': 'public_key'})),
    url(r'^sharing/invitations$', views.SharingPwdViewSet.as_view({'get': 'invitations'})),
    url(r'^sharing/invitations/(?P<pk>[a-z0-9\-]+)$',
        views.SharingPwdViewSet.as_view({'put': 'invitation_update'})),
    url(r'^sharing$', views.SharingPwdViewSet.as_view({'put': 'share'})),
    url(r'^sharing/(?P<pk>[0-9]+)/members/(?P<member_id>[0-9a-z\-]+)$',
        views.SharingPwdViewSet.as_view({'post': 'invitation_confirm'})),
    url(r'^sharing/(?P<pk>[0-9]+)/members/(?P<member_id>[0-9a-z\-]+)/stop$',
        views.SharingPwdViewSet.as_view({'post': 'stop_share'})),
    url(r'^sharing/(?P<pk>[0-9]+)/leave$',  views.SharingPwdViewSet.as_view({'post': 'leave'})),
    url(r'^sharing/my_share$', views.SharingPwdViewSet.as_view({'get': 'my_share'})),

]


# -------------------------------- Folders ------------------------------- #
urlpatterns += [
    url(r'^folders$', views.FolderPwdViewSet.as_view({'post': 'create'})),
    url(r'^folders/(?P<pk>[0-9a-z\-]+)$',
        views.FolderPwdViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
]


# -------------------------------- Emergency Access ------------------------------- #
urlpatterns += [
    url(r'^emergency_access/trusted$', views.EmergencyAccessPwdViewSet.as_view({'get': 'trusted'})),
    url(r'^emergency_access/granted$', views.EmergencyAccessPwdViewSet.as_view({'get': 'granted'})),
    url(r'^emergency_access/invite$', views.EmergencyAccessPwdViewSet.as_view({'post': 'invite'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)$', views.EmergencyAccessPwdViewSet.as_view({'delete': 'destroy'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/reinvite$',
        views.EmergencyAccessPwdViewSet.as_view({'post': 'reinvite'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/public_key$',
        views.EmergencyAccessPwdViewSet.as_view({'get': 'public_key'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/accept$',
        views.EmergencyAccessPwdViewSet.as_view({'post': 'accept'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/confirm$',
        views.EmergencyAccessPwdViewSet.as_view({'post': 'confirm'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/initiate$',
        views.EmergencyAccessPwdViewSet.as_view({'post': 'initiate'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/approve$',
        views.EmergencyAccessPwdViewSet.as_view({'post': 'approve'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/reject$',
        views.EmergencyAccessPwdViewSet.as_view({'post': 'reject'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/view$',
        views.EmergencyAccessPwdViewSet.as_view({'post': 'view'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/takeover$',
        views.EmergencyAccessPwdViewSet.as_view({'post': 'takeover'})),
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/password$',
        views.EmergencyAccessPwdViewSet.as_view({'post': 'password'})),
]


# ------------------------------- Payment ------------------------------------- #
urlpatterns += [
    url(r'^admin/payments/invoices$', views.PaymentPwdViewSet.as_view({'get': 'list'})),
    url(r'^admin/payments/invoices/(?P<pk>[A-Z0-9]+)$', views.PaymentPwdViewSet.as_view({'put': 'set_invoice_status'})),

    url(r'^payments/calc$', views.PaymentPwdViewSet.as_view({'post': 'calc'})),
    url(r'^payments/plan$', views.PaymentPwdViewSet.as_view({'get': 'current_plan', 'post': 'upgrade_plan'})),
    url(r'^payments/plan/cancel$', views.PaymentPwdViewSet.as_view({'post': 'cancel_plan'})),

    url(r'^payments/invoices$', views.PaymentPwdViewSet.as_view({'get': 'invoices'})),
    url(r'^payments/invoices/(?P<pk>[A-Z0-9]+)$',
        views.PaymentPwdViewSet.as_view({'get': 'retrieve_invoice', 'post': 'retry_invoice'})),
    url(r'^payments/invoices/(?P<pk>[A-Z0-9]+)/processing$',
        views.PaymentPwdViewSet.as_view({'post': 'invoice_processing'})),
    url(r'^payments/invoices/(?P<pk>[A-Z0-9]+)/cancel$',
        views.PaymentPwdViewSet.as_view({'post': 'invoice_cancel'})),
]


# -------------------------------- ENTERPRISE ------------------------------ #
""" Teams Management """
urlpatterns += [
    url(r'^teams$', views.TeamPwdViewSet.as_view({'get': 'list'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)$', views.TeamPwdViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/dashboard$', views.TeamPwdViewSet.as_view({'get': 'dashboard'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/delete$', views.TeamPwdViewSet.as_view({'post': 'destroy'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/purge$', views.TeamPwdViewSet.as_view({'post': 'purge'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/import$', views.TeamPwdViewSet.as_view({'post': 'import_data'})),
]


""" Folder Management """
urlpatterns += [
    url(r'^collections/(?P<collection_id>[0-9a-z\-]+)$', views.TeamCollectionPwdViewSet.as_view({'get': 'retrieve'})),

    url(r'^teams/(?P<pk>[0-9a-z\-]+)/folders$',
        views.TeamCollectionPwdViewSet.as_view({'post': 'create'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/folders/(?P<folder_id>[0-9a-z\-]+)$',
        views.TeamCollectionPwdViewSet.as_view({'put': 'update'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/folders/(?P<folder_id>[0-9a-z\-]+)/delete$',
        views.TeamCollectionPwdViewSet.as_view({'post': 'destroy'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/folders/(?P<folder_id>[0-9a-z\-]+)/users$',
        views.TeamCollectionPwdViewSet.as_view({'get': 'users', 'put': 'users'}))
]


""" Member Management """
urlpatterns += [
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members$', views.MemberPwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/invitation$',
        views.MemberPwdViewSet.as_view({'post': 'invitation_member'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/revoke$',
        views.MemberPwdViewSet.as_view({'post': 'revoke_invitation'})),
    url(r'^teams/members/invitation/confirmation$',
        views.MemberPwdViewSet.as_view({'get': 'invitation_confirmation'})),

    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/(?P<member_id>[a-z0-9\-]+)$',
        views.MemberPwdViewSet.as_view({'post': 'confirm', 'put': 'update', 'delete': 'destroy'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/(?P<member_id>[a-z0-9\-]+)/reinvite$',
        views.MemberPwdViewSet.as_view({'post': 'reinvite'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/(?P<member_id>[a-z0-9\-]+)/public_key$',
        views.MemberPwdViewSet.as_view({'get': 'public_key'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/(?P<member_id>[a-z0-9\-]+)/groups$',
        views.MemberPwdViewSet.as_view({'get': 'groups', 'put': 'groups'})),

]


""" Group Management """
urlpatterns += [
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/groups$', views.GroupPwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/groups/(?P<group_id>[0-9a-z\-]+)$',
        views.GroupPwdViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/groups/(?P<group_id>[0-9a-z\-]+)/users$',
        views.GroupPwdViewSet.as_view({'get': 'users', 'put': 'users'})),
]


""" Policy """
urlpatterns += [
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/policy$', views.PolicyPwdViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
]


""" Event Logs """
urlpatterns += [
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/logs$', views.ActivityLogViewSet.as_view({'get': 'list'})),
]


# # -------------------------------- Members ----------------------------------- #
# urlpatterns += [
#     url(r'^members/share$', views.MemberPwdViewSet.as_view({'post': 'create_member_share'})),
#     url(r'^invitations/share$', views.MemberPwdViewSet.as_view({'post': 'create_invitation_share'})),
# ]
