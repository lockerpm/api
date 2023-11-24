import dependency_injector.containers as containers
import dependency_injector.providers as providers

from locker_server.core.services import *
from locker_server.settings import locker_server_settings

RepositoryFactory = locker_server_settings.API_REPOSITORY_CLASS


class ServiceFactory(containers.DeclarativeContainer):
    """ IoC container of Services """

    auth_service = providers.Factory(
        AuthService,
        auth_repository=RepositoryFactory.auth_repository,
        device_access_token_repository=RepositoryFactory.device_access_token_repository,
    )

    resource_service = providers.Factory(
        ResourceService,
        plan_repository=RepositoryFactory.plan_repository,
        country_repository=RepositoryFactory.country_repository,
        mail_provider_repository=RepositoryFactory.mail_provider_repository
    )

    user_service = providers.Factory(
        UserService,
        user_repository=RepositoryFactory.user_repository,
        device_repository=RepositoryFactory.device_repository,
        device_access_token_repository=RepositoryFactory.device_access_token_repository,
        auth_repository=RepositoryFactory.auth_repository,
        user_plan_repository=RepositoryFactory.user_plan_repository,
        payment_repository=RepositoryFactory.payment_repository,
        plan_repository=RepositoryFactory.plan_repository,
        team_repository=RepositoryFactory.team_repository,
        team_member_repository=RepositoryFactory.team_member_repository,
        cipher_repository=RepositoryFactory.cipher_repository,
        enterprise_repository=RepositoryFactory.enterprise_repository,
        enterprise_member_repository=RepositoryFactory.enterprise_member_repository,
        enterprise_policy_repository=RepositoryFactory.enterprise_policy_repository,
        notification_setting_repository=RepositoryFactory.notification_setting_repository,
        factor2_method_repository=RepositoryFactory.factor2_method_repository,
    )
    device_service = providers.Factory(
        DeviceService,
        device_repository=RepositoryFactory.device_repository,
        device_access_token_repository=RepositoryFactory.device_access_token_repository,
    )
    family_service = providers.Factory(
        FamilyService,
        user_repository=RepositoryFactory.user_repository,
        user_plan_repository=RepositoryFactory.user_plan_repository,
    )

    emergency_access_service = providers.Factory(
        EmergencyAccessService,
        emergency_access_repository=RepositoryFactory.emergency_access_repository,
        device_repository=RepositoryFactory.device_repository,
        notification_setting_repository=RepositoryFactory.notification_setting_repository,
        user_repository=RepositoryFactory.user_repository,
        cipher_repository=RepositoryFactory.cipher_repository,
        team_member_repository=RepositoryFactory.team_member_repository,
    )

    exclude_domain_service = providers.Factory(
        ExcludeDomainService,
        exclude_domain_repository=RepositoryFactory.exclude_domain_repository
    )

    payment_service = providers.Factory(
        PaymentService,
        payment_repository=RepositoryFactory.payment_repository,
        user_plan_repository=RepositoryFactory.user_plan_repository,
        plan_repository=RepositoryFactory.plan_repository,
        user_repository=RepositoryFactory.user_repository,
        enterprise_member_repository=RepositoryFactory.enterprise_member_repository,
        education_email_repository=RepositoryFactory.education_email_repository,
        cipher_repository=RepositoryFactory.cipher_repository,
        relay_address_repository=RepositoryFactory.relay_address_repository
    )
    mobile_payment_service = providers.Factory(
        MobilePaymentService,
        payment_repository=RepositoryFactory.payment_repository,
        user_plan_repository=RepositoryFactory.user_plan_repository,
        user_repository=RepositoryFactory.user_repository
    )
    payment_hook_service = providers.Factory(
        PaymentHookService,
        payment_repository=RepositoryFactory.payment_repository,
        user_plan_repository=RepositoryFactory.user_plan_repository,
        user_repository=RepositoryFactory.user_repository
    )

    cipher_service = providers.Factory(
        CipherService,
        cipher_repository=RepositoryFactory.cipher_repository,
        folder_repository=RepositoryFactory.folder_repository,
        team_repository=RepositoryFactory.team_repository,
        team_member_repository=RepositoryFactory.team_member_repository,
        user_plan_repository=RepositoryFactory.user_plan_repository,
    )
    folder_service = providers.Factory(
        FolderService,
        folder_repository=RepositoryFactory.folder_repository,
        cipher_repository=RepositoryFactory.cipher_repository,
    )

    team_member_service = providers.Factory(
        TeamMemberService,
        team_member_repository=RepositoryFactory.team_member_repository,

    )
    collection_service = providers.Factory(
        CollectionService,
        collection_repository=RepositoryFactory.collection_repository
    )
    sharing_service = providers.Factory(
        SharingService,
        sharing_repository=RepositoryFactory.sharing_repository,
        team_repository=RepositoryFactory.team_repository,
        team_member_repository=RepositoryFactory.team_member_repository,
        team_group_repository=RepositoryFactory.team_group_repository,
        user_repository=RepositoryFactory.user_repository,
        notification_setting_repository=RepositoryFactory.notification_setting_repository,
        device_repository=RepositoryFactory.device_repository,
        enterprise_group_repository=RepositoryFactory.enterprise_group_repository,
        enterprise_group_member_repository=RepositoryFactory.enterprise_group_member_repository,
        cipher_repository=RepositoryFactory.cipher_repository,
        folder_repository=RepositoryFactory.folder_repository,
        enterprise_repository=RepositoryFactory.enterprise_repository,
    )

    quick_share_service = providers.Factory(
        QuickShareService,
        quick_share_repository=RepositoryFactory.quick_share_repository,
        cipher_repository=RepositoryFactory.cipher_repository,
        user_repository=RepositoryFactory.user_repository,
        enterprise_repository=RepositoryFactory.enterprise_repository,
    )

    enterprise_service = providers.Factory(
        EnterpriseService,
        enterprise_repository=RepositoryFactory.enterprise_repository,
        enterprise_member_repository=RepositoryFactory.enterprise_member_repository,
        enterprise_policy_repository=RepositoryFactory.enterprise_policy_repository,
        enterprise_billing_contact_repository=RepositoryFactory.enterprise_billing_contact_repository,
        enterprise_domain_repository=RepositoryFactory.enterprise_domain_repository,
        country_repository=RepositoryFactory.country_repository,
        user_repository=RepositoryFactory.user_repository,
    )
    enterprise_group_service = providers.Factory(
        EnterpriseGroupService,
        enterprise_group_repository=RepositoryFactory.enterprise_group_repository,
        enterprise_group_member_repository=RepositoryFactory.enterprise_group_member_repository,
        enterprise_member_repository=RepositoryFactory.enterprise_member_repository,
        user_repository=RepositoryFactory.user_repository
    )
    enterprise_member_service = providers.Factory(
        EnterpriseMemberService,
        enterprise_repository=RepositoryFactory.enterprise_repository,
        enterprise_member_repository=RepositoryFactory.enterprise_member_repository,
        enterprise_group_member_repository=RepositoryFactory.enterprise_group_member_repository,
        user_repository=RepositoryFactory.user_repository,
        user_plan_repository=RepositoryFactory.user_plan_repository
    )
    enterprise_domain_service = providers.Factory(
        EnterpriseDomainService,
        enterprise_domain_repository=RepositoryFactory.enterprise_domain_repository,
        enterprise_repository=RepositoryFactory.enterprise_repository,
        enterprise_member_repository=RepositoryFactory.enterprise_member_repository,
        event_repository=RepositoryFactory.event_repository,
        user_plan_repository=RepositoryFactory.user_plan_repository,
    )
    enterprise_billing_contact_service = providers.Factory(
        EnterpriseBillingContactService,
        enterprise_billing_contact_repository=RepositoryFactory.enterprise_billing_contact_repository,
    )

    event_service = providers.Factory(
        EventService,
        event_repository=RepositoryFactory.event_repository,
        user_repository=RepositoryFactory.user_repository
    )

    relay_address_service = providers.Factory(
        RelayAddressService,
        relay_address_repository=RepositoryFactory.relay_address_repository,
        user_repository=RepositoryFactory.user_repository,
        deleted_relay_address_repository=RepositoryFactory.deleted_relay_address_repository
    )
    relay_subdomain_service = providers.Factory(
        RelaySubdomainService,
        relay_subdomain_repository=RepositoryFactory.relay_subdomain_repository,
        user_repository=RepositoryFactory.user_repository,
        relay_address_repository=RepositoryFactory.relay_address_repository,
        deleted_relay_address_repository=RepositoryFactory.deleted_relay_address_repository
    )
    reply_service = providers.Factory(
        ReplyService,
        reply_repository=RepositoryFactory.reply_repository
    )

    affiliate_submission_service = providers.Factory(
        AffiliateSubmissionService,
        affiliate_submission_repository=RepositoryFactory.affiliate_submission_repository,
        country_repository=RepositoryFactory.country_repository
    )
    release_service = providers.Factory(
        ReleaseService,
        release_repository=RepositoryFactory.release_repository
    )
    notification_setting_service = providers.Factory(
        NotificationSettingService,
        notification_setting_repository=RepositoryFactory.notification_setting_repository,
        user_repository=RepositoryFactory.user_repository
    )
    user_reward_mission_service = providers.Factory(
        UserRewardMissionService,
        user_reward_mission_repository=RepositoryFactory.user_reward_mission_repository,
        user_repository=RepositoryFactory.user_repository,
        mission_repository=RepositoryFactory.mission_repository,
        promo_code_repository=RepositoryFactory.promo_code_repository
    )
    factor2_service = providers.Factory(
        Factor2Service,
        user_repository=RepositoryFactory.user_repository,
        auth_repository=RepositoryFactory.auth_repository,
        factor2_method_repository=RepositoryFactory.factor2_method_repository
    )

    notification_service = providers.Factory(
        NotificationService,
        notification_repository=RepositoryFactory.notification_repository,
        user_repository=RepositoryFactory.user_repository
    )

    mail_configuration_service = providers.Factory(
        MailConfigurationService,
        mail_configuration_repository=RepositoryFactory.mail_configuration_repository,
    )

    sso_configuration_service = providers.Factory(
        SSOConfigurationService,
        sso_configuration_repository=RepositoryFactory.sso_configuration_repository,
        user_repository=RepositoryFactory.user_repository
    )
    cron_task_service = providers.Factory(
        CronTaskService,
        event_repository=RepositoryFactory.event_repository,
        cipher_repository=RepositoryFactory.cipher_repository,
        enterprise_repository=RepositoryFactory.enterprise_repository,
        enterprise_domain_repository=RepositoryFactory.enterprise_domain_repository,
        enterprise_member_repository=RepositoryFactory.enterprise_member_repository,
        user_repository=RepositoryFactory.user_repository,
        user_plan_repository=RepositoryFactory.user_plan_repository,
        emergency_access_repository=RepositoryFactory.emergency_access_repository,
        payment_repository=RepositoryFactory.payment_repository,
    )
    backup_credential_service = providers.Factory(
        BackupCredentialService,
        user_repository=RepositoryFactory.user_repository,
        backup_credential_repository=RepositoryFactory.backup_credential_repository,

    )
