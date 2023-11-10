from django.conf import settings
from django.db import connection

from locker_server.shared.constants.enterprise_members import E_MEMBER_ROLE_MEMBER, E_MEMBER_STATUS_INVITED, \
    E_MEMBER_STATUS_CONFIRMED, E_MEMBER_ROLE_ADMIN
from locker_server.shared.external_services.locker_background.background import LockerBackground
from locker_server.shared.external_services.requester.retry_requester import requester
from locker_server.shared.external_services.user_notification.list_jobs import PWD_VERIFY_DOMAIN_SUCCESS, \
    PWD_JOIN_YOUR_ORG, PWD_VERIFY_DOMAIN_FAILED
from locker_server.shared.external_services.user_notification.notification_sender import NotificationSender, \
    SENDING_SERVICE_MAIL
from locker_server.shared.utils.app import diff_list, now


API_NOTIFY_DOMAIN = "{}/micro_services/cystack_platform/pm/domains".format(settings.GATEWAY_API)
HEADERS = {
    'User-agent': 'Locker Password Manager API',
    "Authorization": settings.MICRO_SERVICE_USER_AUTH
}


class DomainBackground(LockerBackground):
    def domain_verified(self, owner_user_id: int, domain):
        from locker_server.containers.containers import user_service, enterprise_member_service
        try:
            enterprise = domain.enterprise
            enterprise_user_ids = enterprise_member_service.list_enterprise_member_user_ids(
                **{"enterprise_id": enterprise.enterprise_id}
            )
            existed_user_ids = [e for e in enterprise_user_ids if e is not None]

            if not settings.SELF_HOSTED:
                url = API_NOTIFY_DOMAIN + "/verified"
                notification_data = {
                    "owner": owner_user_id,
                    "domain": domain.domain,
                    "existed_user_ids": list(existed_user_ids),
                    "enterprise_name": enterprise.name,
                }
                res = requester(method="POST", url=url, headers=HEADERS, data_send=notification_data)
                if res.status_code != 200:
                    self.log_error(
                        func_name="domain_verified",
                        tb=f"Cannot get list locker users with this domain: {domain.domain}\n"
                           f"{url} {res.status_code} {res.status_code}"
                    )
                    return
                else:
                    member_user_ids = res.json().get("member_user_ids", [])
            else:
                domain_address = domain.domain
                org_name = enterprise.name
                # Sending mail
                NotificationSender(
                    job=PWD_VERIFY_DOMAIN_SUCCESS, scope=settings.SCOPE_PWD_MANAGER, services=[SENDING_SERVICE_MAIL]
                ).send(**{"user_ids": [owner_user_id], "domain": domain_address, "cc": []})

                # Finding all locker users who have domain mail
                if domain_address in settings.LOCKER_TEST_DOMAINS:
                    locker_user_ids = user_service.list_user_ids(**{
                        "exclude_user_ids": existed_user_ids,
                        "emails": [settings.LOCKER_TEST_DOMAIN_MEMBERS]
                    })

                else:
                    locker_user_ids = user_service.list_user_ids(**{
                        "exclude_user_ids": existed_user_ids,
                        "email_endswith": "@{}".format(domain)
                    })
                NotificationSender(
                    job=PWD_JOIN_YOUR_ORG, scope=settings.SCOPE_PWD_MANAGER, services=[SENDING_SERVICE_MAIL]
                ).send(**{"user_ids": list(locker_user_ids), "org_name": org_name})
                member_user_ids = list(set(locker_user_ids))

            existed_member_user_ids = enterprise_member_service.list_enterprise_member_user_ids(**{
                "user_ids": member_user_ids
            })
            non_existed_member_user_ids = diff_list(member_user_ids, existed_member_user_ids)

            user_ids = user_service.list_user_ids(**{"user_ids": non_existed_member_user_ids})

            members = []
            for user_id in user_ids:
                members.append({
                    "enterprise_id": enterprise.enterprise_id,
                    "user_id": user_id,
                    "role_id": E_MEMBER_ROLE_MEMBER,
                    "domain_id": domain.domain_id,
                    "status": E_MEMBER_STATUS_INVITED,
                    "is_default": False,
                    "is_primary": False,
                    "access_time": now()
                })
            return enterprise_member_service.create_multiple_members(members_data=members)
        except Exception as e:
            self.log_error(func_name="domain_verified")
        finally:
            if self.background:
                connection.close()

    def domain_unverified(self, owner_user_id: int, domain):
        from locker_server.containers.containers import user_service, enterprise_member_service
        try:
            enterprise = domain.enterprise
            member_user_ids = enterprise_member_service.list_enterprise_member_user_ids(
                **{"enterprise_id": enterprise.enterprise_id}
            )
            existed_user_ids = [e for e in member_user_ids if e is not None]
            admins = enterprise_member_service.list_enterprise_members(**{
                "enterprise_id": enterprise.enterprise_id,
                "statuses": [E_MEMBER_STATUS_CONFIRMED],
                "roles": [E_MEMBER_ROLE_ADMIN]
            })
            admins_user_ids = [m.user.user_id for m in admins if m.user and m.user.activated is True]

            if not settings.SELF_HOSTED:
                url = API_NOTIFY_DOMAIN + "/unverified"
                notification_data = {
                    "owner": owner_user_id,
                    "domain": domain.domain,
                    "existed_user_ids": existed_user_ids,
                    "enterprise_name": enterprise.name,
                    "cc": admins_user_ids
                }
                res = requester(method="POST", url=url, headers=HEADERS, data_send=notification_data)
                if res.status_code != 200:
                    self.log_error(
                        func_name="domain_unverified",
                        tb=f"Cannot send notify domain verification failed: {domain.domain}\n"
                           f"{url} {res.status_code} {res.status_code}"
                    )
            else:
                # Sending mail
                NotificationSender(
                    job=PWD_VERIFY_DOMAIN_FAILED, scope=settings.SCOPE_PWD_MANAGER, services=[SENDING_SERVICE_MAIL]
                ).send(**{"user_ids": [owner_user_id], "domain": domain.domain, "cc": admins_user_ids})
        except Exception as e:
            self.log_error(func_name="domain_unverified")
        finally:
            if self.background:
                connection.close()

    def domain_auto_approve(self, user_id_update_domain, domain, ip_address: str = None):
        from locker_server.containers.containers import enterprise_domain_service
        try:
            enterprise_domain_service.domain_auto_approve(
                user_id_update_domain=user_id_update_domain, domain=domain, ip_address=ip_address,
                scope=settings.SCOPE_PWD_MANAGER
            )
        except Exception as e:
            self.log_error(func_name="domain_auto_approve")
        finally:
            if self.background:
                connection.close()
