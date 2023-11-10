from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from locker_server.api.v1_0 import views
from locker_server.shared.caching.api_cache_page import LONG_TIME_CACHE

router = DefaultRouter(trailing_slash=False)

urlpatterns = [
    url(r'^', include(router.urls))
]

# ------------------------------- Management Command ----------------------------- #
urlpatterns += [

]

# ----------------------------------- Resources ----------------------------- #
urlpatterns += [
    url(r'^resources/plans$', LONG_TIME_CACHE(views.ResourcePwdViewSet.as_view({'get': 'plans'}))),
    url(r'^resources/enterprise/plans$',
        LONG_TIME_CACHE(views.ResourcePwdViewSet.as_view({'get': 'enterprise_plans'}))),
    url(r'^resources/mail_providers$', views.ResourcePwdViewSet.as_view({'get': 'mail_providers'})),
    url(r'^resources/market_banners$', views.ResourcePwdViewSet.as_view({'get': 'market_banners'})),
]

# ----------------------------------- Tools ----------------------------- #
urlpatterns += [
    url(r'^tools/breach$', views.ToolPwdViewSet.as_view({'post': 'breach'})),
    url(r'^tools/public/breach$', views.ToolPwdViewSet.as_view({'post': 'public_breach'})),
]

# ----------------------------------- Exclude domains ----------------------------- #
urlpatterns += [
    url(r'^exclude_domains$', views.ExcludeDomainPwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^exclude_domains/(?P<pk>[a-z0-9\-]+)$',
        views.ExcludeDomainPwdViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
]

# ----------------------------------- Users ----------------------------- #
urlpatterns += [
    url(r'^users/me$', views.UserPwdViewSet.as_view({'get': 'me', 'put': 'me'})),
    url(r'^users/me/revision_date$', views.UserPwdViewSet.as_view({'get': 'revision_date'})),
    url(r'^users/me/onboarding_process$',
        views.UserPwdViewSet.as_view({'get': 'onboarding_process', 'put': 'onboarding_process'})),
    url(r'^users/me/block_by_2fa$', views.UserPwdViewSet.as_view({'get': 'block_by_2fa_policy'})),
    url(r'^users/me/login_method$', views.UserPwdViewSet.as_view({'get': 'login_method_me'})),
    url(r'^users/me/passwordless_require$', views.UserPwdViewSet.as_view({'get': 'passwordless_require'})),
    url(r'^users/me/violation$', views.UserPwdViewSet.as_view({'get': 'violation_me'})),
    url(r'^users/me/family', views.UserPwdViewSet.as_view({'get': 'family'})),
    url(r'^users/me/delete$', views.UserPwdViewSet.as_view({'post': 'delete_me'})),
    url(r'^users/me/purge$', views.UserPwdViewSet.as_view({'post': 'purge_me'})),
    url(r'^users/me/password$', views.UserPwdViewSet.as_view({'post': 'password'})),
    url(r'^users/me/new_password$', views.UserPwdViewSet.as_view({'post': 'new_password'})),
    url(r'^users/me/check_password$', views.UserPwdViewSet.as_view({'post': 'check_password'})),
    url(r'^users/me/fcm_id$', views.UserPwdViewSet.as_view({'post': 'fcm_id'})),
    url(r'^users/me/devices$', views.UserPwdViewSet.as_view({'get': 'devices'})),
    url(r'^users/password_hint$', views.UserPwdViewSet.as_view({'post': 'password_hint'})),
    url(r'^users/register$', views.UserPwdViewSet.as_view({'post': 'register'})),
    url(r'^users/session$', views.UserPwdViewSet.as_view({'post': 'session'})),
    url(r'^users/session/otp$', views.UserPwdViewSet.as_view({'post': 'session_otp'})),
    url(r'^users/session/revoke_all$', views.UserPwdViewSet.as_view({'post': 'revoke_all_sessions'})),
    url(r'^users/invitations/confirmation$', views.UserPwdViewSet.as_view({'get': 'invitation_confirmation'})),
    url(r'^users/invitations$', views.UserPwdViewSet.as_view({'get': 'invitations'})),
    url(r'^users/invitations/(?P<pk>[a-z0-9\-]+)$', views.UserPwdViewSet.as_view({'put': 'invitation_update'})),
    url(r'^users/check_exist$', views.UserPwdViewSet.as_view({'get': 'check_exist'})),
    url(r'^users/prelogin$', views.UserPwdViewSet.as_view({'post': 'prelogin'})),
    url(r'^users/reset_password$', views.UserPwdViewSet.as_view({'post': 'reset_password'})),
    url(r'^users/backup_credentials$', views.BackupCredentialPwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^users/backup_credentials/(?P<pk>[a-zA-Z0-9\-]+)$',
        views.BackupCredentialPwdViewSet.as_view({'get': 'retrieve', 'delete': "destroy"})),

]

# ----------------------------------- Passwordless ----------------------------- #
urlpatterns += [
    url(r'^passwordless/credential$',
        views.PasswordlessPwdViewSet.as_view({'get': 'credential', 'post': 'credential'})),
]

# -------------------------------- Notification Settings ------------------ #
urlpatterns += [
    url(r'^notification/settings$', views.NotificationSettingPwdViewSet.as_view({'get': 'list'})),
    url(r'^notification/settings/(?P<category_id>[a-z_]+)$',
        views.NotificationSettingPwdViewSet.as_view({'put': 'update'})),
]

# -------------------------------- Sync ----------------------------------- #
urlpatterns += [
    url(r'^sync$', views.SyncPwdViewSet.as_view({'get': 'sync'})),
    url(r'^sync/count$', views.SyncPwdViewSet.as_view({'get': 'sync_count'})),
    url(r'^sync/ciphers$', views.SyncPwdViewSet.as_view({'get': 'sync_ciphers'})),
    url(r'^sync/ciphers/(?P<pk>[0-9a-z\-]+)$', views.SyncPwdViewSet.as_view({'get': 'sync_cipher_detail'})),
    url(r'^sync/folders$', views.SyncPwdViewSet.as_view({'get': 'sync_folders'})),
    url(r'^sync/folders/(?P<pk>[0-9a-z\-]+)$', views.SyncPwdViewSet.as_view({'get': 'sync_folder_detail'})),
    url(r'^sync/collections$', views.SyncPwdViewSet.as_view({'get': 'sync_collections'})),
    url(r'^sync/collections/(?P<pk>[0-9a-z\-]+)$', views.SyncPwdViewSet.as_view({'get': 'sync_collection_detail'})),
    url(r'^sync/profile$', views.SyncPwdViewSet.as_view({'get': 'sync_profile_detail'})),
    url(r'^sync/organizations/(?P<pk>[0-9a-z\-]+)$', views.SyncPwdViewSet.as_view({'get': 'sync_org_detail'})),
    url(r'^sync/policies$', views.SyncPwdViewSet.as_view({'get': 'sync_policies'})),
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
    url(r'^ciphers/(?P<pk>[0-9a-z\-]+)/use$', views.CipherPwdViewSet.as_view({'put': 'cipher_use'})),
]

# -------------------------------- Cipher Sharing ------------------------------- #
urlpatterns += [
    url(r'^sharing/public_key$', views.SharingPwdViewSet.as_view({'post': 'public_key'})),
    url(r'^sharing/invitations$', views.SharingPwdViewSet.as_view({'get': 'invitations'})),
    url(r'^sharing/invitations/(?P<pk>[a-z0-9\-]+)$',
        views.SharingPwdViewSet.as_view({'put': 'invitation_update'})),
    url(r'^sharing$', views.SharingPwdViewSet.as_view({'put': 'share'})),
    url(r'^sharing/multiple$', views.SharingPwdViewSet.as_view({'put': 'multiple_share'})),
    url(r'^sharing/(?P<pk>[0-9]+)/members/(?P<member_id>[0-9a-z\-]+)$',
        views.SharingPwdViewSet.as_view({'post': 'invitation_confirm', 'put': 'update_role'})),
    url(r'^sharing/(?P<pk>[0-9]+)/groups/(?P<group_id>[0-9a-z\-]+)$',
        views.SharingPwdViewSet.as_view({'post': 'invitation_group_confirm', 'put': 'update_group_role'})),

    url(r'^sharing/(?P<pk>[0-9]+)/members/(?P<member_id>[0-9a-z\-]+)/stop$',
        views.SharingPwdViewSet.as_view({'post': 'stop_share'})),
    url(r'^sharing/(?P<pk>[0-9]+)/groups/(?P<group_id>[0-9a-z\-]+)/stop$',
        views.SharingPwdViewSet.as_view({'post': 'stop_share'})),
    url(r'^sharing/(?P<pk>[0-9]+)/leave$', views.SharingPwdViewSet.as_view({'post': 'leave'})),
    url(r'^sharing/(?P<pk>[0-9]+)/stop$',
        views.SharingPwdViewSet.as_view({'post': 'stop_share_cipher_folder'})),

    url(r'^sharing/(?P<pk>[0-9]+)/members$', views.SharingPwdViewSet.as_view({'post': 'add_member'})),
    url(r'^sharing/(?P<pk>[0-9]+)/folders/(?P<folder_id>[0-9a-z\-]+)$',
        views.SharingPwdViewSet.as_view({'put': 'update_share_folder'})),
    url(r'^sharing/(?P<pk>[0-9]+)/folders/(?P<folder_id>[0-9a-z\-]+)/delete$',
        views.SharingPwdViewSet.as_view({'post': 'delete_share_folder'})),
    url(r'^sharing/(?P<pk>[0-9]+)/folders/(?P<folder_id>[0-9a-z\-]+)/stop$',
        views.SharingPwdViewSet.as_view({'post': 'stop_share_folder'})),

    url(r'^sharing/(?P<pk>[0-9]+)/folders/(?P<folder_id>[0-9a-z\-]+)/items$',
        views.SharingPwdViewSet.as_view({'post': 'add_item_share_folder', 'put': 'remove_item_share_folder'})),
    url(r'^sharing/my_share$', views.SharingPwdViewSet.as_view({'get': 'my_share'})),

]

# ------------------------------ Quick Shares --------------------------------- #
urlpatterns += [
    url(r'^quick_shares$', views.QuickSharePwdViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^quick_shares/(?P<pk>[0-9a-z-]+)$',
        views.QuickSharePwdViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    url(r'^quick_shares/(?P<pk>[0-9A-Z]+)/public$', views.QuickSharePwdViewSet.as_view({'post': 'public'})),
    url(r'^quick_shares/(?P<pk>[0-9A-Z]+)/access$',
        views.QuickSharePwdViewSet.as_view({'get': 'access', 'post': 'access'})),
    url(r'^quick_shares/(?P<pk>[0-9A-Z]+)/otp$', views.QuickSharePwdViewSet.as_view({'post': 'otp'})),
]

# -------------------------------- Folders ------------------------------- #
urlpatterns += [
    url(r'^folders$', views.FolderPwdViewSet.as_view({'post': 'create'})),
    url(r'^folders/(?P<pk>[0-9a-z\-]+)$',
        views.FolderPwdViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
]

# -------------------------------- Import ------------------------------- #
urlpatterns += [
    url(r'^import/folders$', views.ImportDataPwdViewSet.as_view({'post': 'import_folders'})),
    url(r'^import/ciphers$', views.ImportDataPwdViewSet.as_view({'post': 'import_ciphers'})),
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
    url(r'^emergency_access/(?P<pk>[0-9a-z\-]+)/id_password$',
        views.EmergencyAccessPwdViewSet.as_view({'post': 'id_password'})),
]

# ------------------------------- Payment ------------------------------------- #
urlpatterns += [
    url(r'^payments/calc$', views.PaymentPwdViewSet.as_view({'post': 'calc'})),
    url(r'^payments/trial$', views.PaymentPwdViewSet.as_view({'get': 'check_trial', 'post': 'upgrade_trial'})),
    url(r'^payments/trial/enterprise$', views.PaymentPwdViewSet.as_view({
        'post': 'upgrade_trial_enterprise_by_code', 'put': 'generate_trial_enterprise_code'
    })),
    url(r'^payments/plan$', views.PaymentPwdViewSet.as_view({'get': 'current_plan', 'post': 'upgrade_plan'})),
    url(r'^payments/next_attempt$', views.PaymentPwdViewSet.as_view({'get': 'next_attempt'})),
    url(r'^payments/plan/limit$', views.PaymentPwdViewSet.as_view({'get': 'plan_limit'})),
    url(r'^payments/plan/cancel$', views.PaymentPwdViewSet.as_view({'post': 'cancel_plan'})),

    url(r'^payments/invoices$', views.PaymentPwdViewSet.as_view({'get': 'invoices'})),
    url(r'^payments/invoices/(?P<pk>[A-Z0-9]+)$',
        views.PaymentPwdViewSet.as_view({'get': 'retrieve_invoice', 'post': 'retry_invoice'})),
]

# -------------------------------- Family Plan members  ------------------------------------- #
urlpatterns += [
    url(r'^family/members$', views.FamilyPwdViewSet.as_view({'get': 'member_list', 'post': 'member_create'})),
    url(r'^family/members/(?P<member_id>[0-9]+)$', views.FamilyPwdViewSet.as_view({'delete': 'member_destroy'})),
]

# -------------------------------- Releases  ------------------------------------- #
urlpatterns += [
    url(r'^releases$', views.ReleasePwdViewSet.as_view({'get': 'list'})),
    url(r'^releases/(?P<client_id>[0-9a-zA-Z_-]+)/(?P<version>[0-9.]+)$',
        LONG_TIME_CACHE(views.ReleasePwdViewSet.as_view({'get': 'retrieve'}))),
    url(r'^releases/current$', views.ReleasePwdViewSet.as_view({'get': 'current', 'post': 'current'})),
    url(r'^releases/current_version$', views.ReleasePwdViewSet.as_view({'get': 'current_version'})),
    url(r'^releases/new$', views.ReleasePwdViewSet.as_view({'post': 'new'}))
]

# --------------------------------- Form submission ---------------------------- #
urlpatterns += [
    url(r'^affiliate_submissions$', views.AffiliateSubmissionPwdViewSet.as_view({'post': 'create'})),
]

# ----------------------------------- Admin --------------------------------- #
urlpatterns += [
    url(r'^admin/payments/invoices$', views.PaymentPwdViewSet.as_view({'get': 'list'})),
    url(r'^admin/payments/invoices/(?P<pk>[A-Z0-9]+)$', views.PaymentPwdViewSet.as_view({'put': 'set_invoice_status'})),

    url(r'^admin/users/ids$', views.UserPwdViewSet.as_view({'get': 'list_user_ids'})),
    url(r'^admin/users$', views.UserPwdViewSet.as_view({'get': 'list_users'})),
    url(r'^admin/users/dashboard$', views.UserPwdViewSet.as_view({'get': 'dashboard'})),
    url(r'^admin/users/(?P<pk>[0-9]+)$', views.UserPwdViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    url(r'^admin/users/(?P<pk>[0-9]+)/invoices$', views.PaymentPwdViewSet.as_view({'get': 'user_invoices'})),
    url(r'^admin/users/(?P<pk>[0-9]+)/plan$', views.PaymentPwdViewSet.as_view({'post': 'admin_upgrade_plan'})),

    url(r'^admin/affiliate_submissions$', views.AffiliateSubmissionPwdViewSet.as_view({'get': 'list'})),
    url(r'^admin/affiliate_submissions/(?P<pk>[0-9]+)$',
        views.AffiliateSubmissionPwdViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

]

# ------------------------------- Management Command ----------------------------- #
urlpatterns += [
    url(r'^managements/commands/(?P<pk>[a-z_]+)$', views.ManagementCommandPwdViewSet.as_view({'post': 'commands'})),
    url(r'^managements/statistics/users$', views.ManagementCommandPwdViewSet.as_view({'get': 'users'})),
]

# ----------------------------------- User Reward missions ----------------- ------------ #
urlpatterns += [
    url(r'^reward/claim$', views.UserRewardMissionPwdViewSet.as_view({'get': 'claim'})),
    url(r'^reward/claim/promo_codes$',
        views.UserRewardMissionPwdViewSet.as_view({'get': 'list_promo_codes', 'post': 'claim_promo_code'})),
    url(r'^reward/missions$', views.UserRewardMissionPwdViewSet.as_view({'get': 'list'})),
    url(r'^reward/missions/(?P<pk>[a-z0-9_]+)/completed$',
        views.UserRewardMissionPwdViewSet.as_view({'post': 'completed'})),
]
