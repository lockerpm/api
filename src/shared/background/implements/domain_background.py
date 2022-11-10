from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection


from shared.background.i_background import ILockerBackground
from shared.constants.enterprise_members import *
from shared.constants.event import EVENT_E_MEMBER_CONFIRMED
from shared.constants.transactions import PAYMENT_METHOD_CARD
from shared.external_request.requester import requester
from cystack_models.models.users.users import User
from cystack_models.models.events.events import Event
from cystack_models.models.enterprises.members.enterprise_members import EnterpriseMember
from shared.utils.app import diff_list, now


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
                            status=E_MEMBER_STATUS_INVITED, is_default=False, is_primary=False,
                            access_time=now()
                        )
                    )
                new_members_obj = EnterpriseMember.objects.bulk_create(members, ignore_conflicts=True, batch_size=50)
                return len(new_members_obj)

        except Exception as e:
            self.log_error(func_name="domain_verified")
        finally:
            if self.background:
                connection.close()

    def domain_unverified(self, owner_user_id: int, domain):
        try:
            url = API_NOTIFY_DOMAIN + "/unverified"
            enterprise = domain.enterprise
            existed_user_ids = enterprise.enterprise_members.exclude(
                user_id__isnull=True
            ).values_list('user_id', flat=True)
            admins = list(enterprise.enterprise_members.filter(
                role_id=E_MEMBER_ROLE_ADMIN, status=E_MEMBER_STATUS_CONFIRMED, is_activated=True
            ).values_list('user_id', flat=True))

            notification_data = {
                "owner": owner_user_id,
                "domain": domain.domain,
                "existed_user_ids": list(existed_user_ids),
                "enterprise_name": enterprise.name,
                "cc": admins
            }
            res = requester(method="POST", url=url, headers=HEADERS, data_send=notification_data)
            if res.status_code != 200:
                self.log_error(
                    func_name="domain_unverified",
                    tb=f"Cannot send notify domain verification failed: {domain.domain}\n"
                       f"{url} {res.status_code} {res.status_code}"
                )
        except Exception as e:
            self.log_error(func_name="domain_unverified")
        finally:
            if self.background:
                connection.close()

    def domain_auto_approve(self, user_id_update_domain, domain, ip_address: str = None):
        try:
            enterprise = domain.enterprise
            primary_admin_user = enterprise.get_primary_admin_user()
            user_plan = primary_admin_user.pm_user_plan
            from_param = user_plan.start_period if user_plan.start_period else enterprise.creation_date
            to_param = user_plan.end_period if user_plan.end_period else now()

            # Get the number of billing members
            members = domain.enterprise_members.filter(status=[E_MEMBER_STATUS_REQUESTED])
            member_events_data = []
            billing_members = 0
            for member in members:
                if enterprise.is_billing_members_added(
                    member_user_id=member.user_id, from_param=from_param, to_param=to_param
                ) is True:
                    billing_members += 1
                member_events_data.append({
                    "acting_user_id": user_id_update_domain,
                    "user_id": member.user_id,
                    "team_id": enterprise.id,
                    "team_member_id": member.id,
                    "type": EVENT_E_MEMBER_CONFIRMED,
                    "ip_address": ip_address
                })

            # Update the Stripe subscription
            if billing_members > 0:
                from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory
                from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodNotSupportException
                try:
                    PaymentMethodFactory.get_method(
                        user=enterprise.get_primary_admin_user(), scope=settings.SCOPE_PWD_MANAGER,
                        payment_method=PAYMENT_METHOD_CARD
                    ).update_quantity_subscription(amount=billing_members)
                except (PaymentMethodNotSupportException, ObjectDoesNotExist):
                    pass
            # Auto accept all requested members
            members.update(status=E_MEMBER_STATUS_CONFIRMED)
            # Log events
            Event.create_multiple_by_enterprise_members(member_events_data)
        except Exception as e:
            self.log_error(func_name="domain_auto_approve")
        finally:
            if self.background:
                connection.close()