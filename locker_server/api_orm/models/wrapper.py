from django.apps import apps

from locker_server.settings import locker_server_settings


def get_user_model():
    """ Return the User model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_USER_MODEL)


def get_device_model():
    """ Return the Device model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_DEVICE_MODEL)


def get_device_access_token_model():
    """ Return the DeviceAccessToken model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_DEVICE_ACCESS_TOKEN_MODEL)


def get_plan_type_model():
    """ Return the PlanType model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_PLAN_TYPE_MODEL)


def get_plan_model():
    """ Return the PMPlan model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_PLAN_MODEL)


def get_promo_code_type_model():
    """ Return the PromoCodeType model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_PROMO_CODE_TYPE_MODEL)


def get_promo_code_model():
    """ Return the PromoCode model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_PROMO_CODE_MODEL)


def get_payment_model():
    """ Return the Payment model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_PAYMENT_MODEL)


def get_user_plan_model():
    """ Return the PMUserPlan model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_USER_PLAN_MODEL)


def get_notification_category_model():
    """ Return the NotificationCategory model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_NOTIFICATION_CATEGORY_MODEL)


def get_notification_setting_model():
    """ Return the NotificationSetting model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_NOTIFICATION_SETTING_MODEL)


def get_event_model():
    """ Return the Event model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_EVENT_MODEL)


def get_emergency_access_model():
    """ Return the EmergencyAccess model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_EMERGENCY_ACCESS_MODEL)


def get_mission_model():
    """ Return the Mission model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_MISSION_MODEL)


def get_relay_reply_model():
    """ Return the Reply model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_RELAY_REPLY_MODEL)


def get_relay_domain_model():
    """ Return the RelayDomain model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_RELAY_DOMAIN_MODEL)


def get_relay_subdomain_model():
    """ Return the RelaySubdomain model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_RELAY_SUBDOMAIN_MODEL)


def get_relay_deleted_address_model():
    """ Return the DeletedRelayAddress model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_RELAY_DELETED_ADDRESS_MODEL)


def get_relay_address_model():
    """ Return the RelayAddress model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_RELAY_ADDRESS_MODEL)


def get_team_model():
    """ Return the Team model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_TEAM_MODEL)


def get_cipher_model():
    """ Return the Cipher model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_CIPHER_MODEL)


def get_folder_model():
    """ Return the Folder model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_FOLDER_MODEL)


def get_member_role_model():
    """ Return the MemberRole model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_MEMBER_ROLE_MODEL)


def get_team_member_model():
    """ Return the TeamMember model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_TEAM_MEMBER_MODEL)


def get_collection_model():
    """ Return the Collection model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_COLLECTION_MODEL)


def get_collection_cipher_model():
    """ Return the CollectionCipher model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_COLLECTION_CIPHER_MODEL)


def get_collection_member_model():
    """ Return the CollectionMember model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_COLLECTION_MEMBER_MODEL)


def get_group_model():
    """ Return the Group model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_GROUP_MODEL)


def get_group_member_model():
    """ Return the GroupMember model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_GROUP_MEMBER_MODEL)


def get_enterprise_model():
    """ Return the Enterprise model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_ENTERPRISE_MODEL)


def get_enterprise_domain_model():
    """ Return the Domain model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_ENTERPRISE_DOMAIN_MODEL)


def get_enterprise_member_role_model():
    """ Return the EnterpriseMemberRole model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_ENTERPRISE_MEMBER_ROLE_MODEL)


def get_enterprise_member_model():
    """ Return the EnterpriseMember model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_ENTERPRISE_MEMBER_MODEL)


def get_enterprise_group_model():
    """ Return the EnterpriseGroup model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_ENTERPRISE_GROUP_MODEL)


def get_enterprise_group_member_model():
    """ Return the EnterpriseGroupMember model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_ENTERPRISE_GROUP_MEMBER_MODEL)


def get_enterprise_policy_model():
    """ Return the EnterprisePolicy model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_ENTERPRISE_POLICY_MODEL)


def get_enterprise_avatar_model():
    """ Return the EnterpriseAvatar model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_ENTERPRISE_AVATAR_MODEL)


def get_quick_share_model():
    """ Return the QuickShare model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_QUICK_SHARE_MODEL)


def get_quick_share_email_model():
    """ Return the QuickShareEmail model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_QUICK_SHARE_EMAIL_MODEL)


def get_affiliate_submission_model():
    """ Return the AffiliateSubmission model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_AFFILIATE_SUBMISSION_MODEL)


def get_release_model():
    """ Return the Release model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_RELEASE_MODEL)


def get_user_reward_mission_model():
    """ Return the UserRewardMission model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_USER_REWARD_MISSION_MODEL)


def get_notification_model():
    """ Return the Notification model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_NOTIFICATION_MODEL)


def get_factor2_method_model():
    """ Return the Notification model that is active in this LockerServer """
    return apps.get_model(locker_server_settings.LS_FACTOR2_METHOD_MODEL)


def get_sso_configuration_model():
    """ Return the SSOConfiguration model that is active in this LockerServer"""
    return apps.get_model(locker_server_settings.LS_SSO_CONFIGURATION_MODEL)


def get_backup_credential_model():
    """ Return the BackupCredential model that is active in this LockerServer"""
    return apps.get_model(locker_server_settings.LS_BACKUP_CREDENTIAL_MODEL)
