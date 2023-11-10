import os

from locker_server.settings import locker_server_settings

env = os.getenv("PROD_ENV", "dev")
if env != "dev":
    ServiceFactory = locker_server_settings.API_SERVICE_CLASS
else:
    from locker_server.containers.defaults.service import ServiceFactory

resource_service = ServiceFactory.resource_service()

auth_service = ServiceFactory.auth_service()
user_service = ServiceFactory.user_service()
device_service = ServiceFactory.device_service()
family_service = ServiceFactory.family_service()
backup_credential_service = ServiceFactory.backup_credential_service()

emergency_access_service = ServiceFactory.emergency_access_service()

exclude_domain_service = ServiceFactory.exclude_domain_service()

payment_service = ServiceFactory.payment_service()
mobile_payment_service = ServiceFactory.mobile_payment_service()
payment_hook_service = ServiceFactory.payment_hook_service()

cipher_service = ServiceFactory.cipher_service()
folder_service = ServiceFactory.folder_service()

team_member_service = ServiceFactory.team_member_service()
collection_service = ServiceFactory.collection_service()
sharing_service = ServiceFactory.sharing_service()

quick_share_service = ServiceFactory.quick_share_service()

enterprise_service = ServiceFactory.enterprise_service()
enterprise_member_service = ServiceFactory.enterprise_member_service()
enterprise_group_service = ServiceFactory.enterprise_group_service()
enterprise_domain_service = ServiceFactory.enterprise_domain_service()
enterprise_billing_contact_service = ServiceFactory.enterprise_billing_contact_service()

event_service = ServiceFactory.event_service()
relay_address_service = ServiceFactory.relay_address_service()
relay_subdomain_service = ServiceFactory.relay_subdomain_service()
reply_service = ServiceFactory.reply_service()

affiliate_submission_service = ServiceFactory.affiliate_submission_service()

release_service = ServiceFactory.release_service()

notification_setting_service = ServiceFactory.notification_setting_service()

user_reward_mission_service = ServiceFactory.user_reward_mission_service()

factor2_service = ServiceFactory.factor2_service()

notification_service = ServiceFactory.notification_service()

mail_configuration_service = ServiceFactory.mail_configuration_service()

sso_configuration_service = ServiceFactory.sso_configuration_service()

cron_task_service = ServiceFactory.cron_task_service()
