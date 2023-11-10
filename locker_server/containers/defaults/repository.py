import dependency_injector.containers as containers
import dependency_injector.providers as providers

from locker_server.api_orm.repositories import *


class RepositoryFactory(containers.DeclarativeContainer):
    """ IoC container of Repositories """

    auth_repository = providers.Factory(AuthORMRepository)
    user_repository = providers.Factory(UserORMRepository)
    plan_repository = providers.Factory(PlanORMRepository)
    user_plan_repository = providers.Factory(UserPlanORMRepository)
    education_email_repository = providers.Factory(EducationEmailORMRepository)
    backup_credential_repository = providers.Factory(BackupCredentialORMRepository)

    payment_repository = providers.Factory(PaymentORMRepository)
    country_repository = providers.Factory(CountryORMRepository)

    emergency_access_repository = providers.Factory(EmergencyAccessORMRepository)

    exclude_domain_repository = providers.Factory(ExcludeDomainORMRepository)

    device_repository = providers.Factory(DeviceORMRepository)
    device_access_token_repository = providers.Factory(DeviceAccessTokenORMRepository)

    cipher_repository = providers.Factory(CipherORMRepository)
    folder_repository = providers.Factory(FolderORMRepository)

    team_repository = providers.Factory(TeamORMRepository)
    team_member_repository = providers.Factory(TeamMemberORMRepository)
    team_group_repository = providers.Factory(TeamGroupORMRepository)
    collection_repository = providers.Factory(CollectionORMRepository)
    sharing_repository = providers.Factory(SharingORMRepository)

    quick_share_repository = providers.Factory(QuickShareORMRepository)

    enterprise_repository = providers.Factory(EnterpriseORMRepository)
    enterprise_member_repository = providers.Factory(EnterpriseMemberORMRepository)
    enterprise_group_repository = providers.Factory(EnterpriseGroupORMRepository)
    enterprise_policy_repository = providers.Factory(EnterprisePolicyORMRepository)
    enterprise_group_member_repository = providers.Factory(EnterpriseGroupMemberORMRepository)
    enterprise_billing_contact_repository = providers.Factory(EnterpriseBillingContactORMRepository)
    enterprise_domain_repository = providers.Factory(EnterpriseDomainORMRepository)

    event_repository = providers.Factory(EventORMRepository)

    notification_category_repository = providers.Factory(NotificationCategoryORMRepository)
    notification_setting_repository = providers.Factory(NotificationSettingORMRepository)
    notification_repository = providers.Factory(NotificationORMRepository)
    relay_address_repository = providers.Factory(RelayAddressORMRepository)
    deleted_relay_address_repository = providers.Factory(DeletedRelayAddressORMRepository)
    relay_subdomain_repository = providers.Factory(RelaySubdomainORMRepository)
    reply_repository = providers.Factory(ReplyORMRepository)

    affiliate_submission_repository = providers.Factory(AffiliateSubmissionORMRepository)

    release_repository = providers.Factory(ReleaseORMRepository)

    user_reward_mission_repository = providers.Factory(UserRewardMissionORMRepository)
    mission_repository = providers.Factory(MissionORMRepository)
    promo_code_repository = providers.Factory(PromoCodeORMRepository)

    factor2_method_repository = providers.Factory(Factor2MethodORMRepository)
    device_factor2_repository = providers.Factory(DeviceFactor2ORMRepository)

    mail_provider_repository = providers.Factory(MailProviderORMRepository)
    mail_configuration_repository = providers.Factory(MailConfigurationORMRepository)

    sso_configuration_repository = providers.Factory(SSOConfigurationORMRepository)
