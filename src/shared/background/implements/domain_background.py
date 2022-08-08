from django.conf import settings
from django.db import connection

from shared.background.i_background import ILockerBackground
from shared.constants.enterprise_members import E_MEMBER_ROLE_MEMBER, E_MEMBER_STATUS_INVITED
from shared.external_request.requester import requester
from cystack_models.models.users.users import User
from cystack_models.models.enterprises.members.enterprise_members import EnterpriseMember
from shared.utils.app import diff_list


API_NOTIFY_DOMAIN = "{}/micro_services/cystack_platform/pm/domains".format(settings.GATEWAY_API)
HEADERS = {
    'User-agent': 'Locker Password Manager API',
    "Authorization": settings.MICRO_SERVICE_USER_AUTH
}


class DomainBackground(ILockerBackground):
    def domain_verified(self, owner_user_id: int, domain):
        try:
            url = API_NOTIFY_DOMAIN + "/verified"
            enterprise = domain.enterprise
            existed_user_ids = enterprise.enterprise_members.exclude(
                user_id__isnull=True
            ).values_list('user_id', flat=True)
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
            else:
                member_user_ids = res.json().get("member_user_ids", [])
                existed_member_user_ids = EnterpriseMember.objects.filter(
                    user_id__in=member_user_ids
                ).values_list('user_id', flat=True)
                non_existed_member_user_ids = diff_list(member_user_ids, existed_member_user_ids)
                users = User.objects.filter(user_id__in=non_existed_member_user_ids)
                members = []
                for user in users:
                    members.append(
                        EnterpriseMember(
                            enterprise=enterprise, user=user, role_id=E_MEMBER_ROLE_MEMBER, domain=domain,
                            status=E_MEMBER_STATUS_INVITED, is_default=False, is_primary=False
                        )
                    )
                EnterpriseMember.objects.bulk_create(members, ignore_conflicts=True, batch_size=50)

        except Exception as e:
            self.log_error(func_name="domain_verified")
        finally:
            if self.background:
                connection.close()
