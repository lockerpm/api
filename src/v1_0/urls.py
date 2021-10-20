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


# ----------------------------------- Users ----------------------------- #
urlpatterns += [
    url(r'^users/me$', views.UserPwdViewSet.as_view({'get': 'me', 'put': 'me'})),
    url(r'^users/me/family', views.UserPwdViewSet.as_view({'get': 'family'})),
    url(r'^users/me/delete$', views.UserPwdViewSet.as_view({'post': 'delete_me'})),
    url(r'^users/me/purge$', views.UserPwdViewSet.as_view({'post': 'purge_me'})),
    url(r'^users/me/password$', views.UserPwdViewSet.as_view({'post': 'password'})),
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
    url(r'^ciphers/(?P<pk>[0-9a-z\-]+)$', views.CipherPwdViewSet.as_view({'put': 'update'})),
    url(r'^ciphers/(?P<pk>[0-9a-z\-]+)/share$', views.CipherPwdViewSet.as_view({'put': 'share'})),

]


# -------------------------------- Folders ------------------------------- #
urlpatterns += [
    url(r'^folders$', views.FolderPwdViewSet.as_view({'post': 'create'})),
    url(r'^folders/(?P<pk>[0-9a-z\-]+)$', views.FolderPwdViewSet.as_view({'put': 'update', 'delete': 'destroy'})),
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
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/folders$',
        views.TeamCollectionPwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/folders/(?P<folder_id>[0-9a-z\-]+)$',
        views.TeamCollectionPwdViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/folders/(?P<folder_id>[0-9a-z\-]+)/delete$',
        views.TeamCollectionPwdViewSet.as_view({'post': 'destroy'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/folders/(?P<folder_id>[0-9a-z\-]+)/users$',
        views.TeamCollectionPwdViewSet.as_view({'get': 'users', 'put': 'users'})),
    # url(r'^teams/(?P<pk>[0-9a-z\-]+)/folders/(?P<folder_id>[0-9a-z\-]+)/groups$',
    #     views.TeamPwdFolderViewSet.as_view({'get': 'groups', 'put': 'groups'})),
]


""" Member Management """
urlpatterns += [
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members$', views.MemberPwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/(?P<member_id>[a-z0-9\-]+)$',
        views.MemberPwdViewSet.as_view({'post': 'confirm', 'put': 'update', 'delete': 'destroy'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/(?P<member_id>[a-z0-9\-]+)/reinvite$',
        views.MemberPwdViewSet.as_view({'post': 'reinvite'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/(?P<member_id>[a-z0-9\-]+)/public_key$',
        views.MemberPwdViewSet.as_view({'get': 'public_key'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/(?P<member_id>[a-z0-9\-]+)/groups$',
        views.MemberPwdViewSet.as_view({'get': 'groups', 'put': 'groups'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/invitation$',
        views.MemberPwdViewSet.as_view({'post': 'invitation_member'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/members/revoke$',
        views.MemberPwdViewSet.as_view({'post': 'revoke_invitation'})),
    url(r'^teams/members/invitation/confirmation$',
        views.MemberPwdViewSet.as_view({'get': 'invitation_confirmation'})),
]


""" Group Management """
urlpatterns += [
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/groups$', views.GroupPwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/groups/(?P<group_id>[0-9a-z\-]+)$',
        views.GroupPwdViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    url(r'^teams/(?P<pk>[0-9a-z\-]+)/groups/(?P<group_id>[0-9a-z\-]+)/users$',
        views.GroupPwdViewSet.as_view({'get': 'users', 'put': 'users'})),
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
