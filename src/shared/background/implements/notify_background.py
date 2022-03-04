import requests

from django.conf import settings
from django.db import connection

from core.settings import CORE_CONFIG
from shared.background.i_background import ILockerBackground
from shared.constants.transactions import PAYMENT_STATUS_PAID


API_NOTIFY_PAYMENT = "{}/micro_services/cystack_platform/payments".format(settings.GATEWAY_API)
HEADERS = {
    'User-agent': 'CyStack Cloud Security',
    "Authorization": settings.MICRO_SERVICE_USER_AUTH
}


class NotifyBackground(ILockerBackground):
    def downgrade_plan(self, user_id, old_plan, downgrade_time, scope, **metadata):
        try:
            url = API_NOTIFY_PAYMENT + "/notify_downgrade"
            notification_data = {
                "user_id": user_id,
                "old_plan": old_plan,
                "downgrade_time": downgrade_time,
                "payment_data": metadata.get("payment_data"),
                "scope": scope
            }
            requests.post(url=url, headers=HEADERS, json=notification_data, verify=False)
        except Exception as e:
            self.log_error(func_name="downgrade_plan")
        finally:
            if self.background:
                connection.close()

    def cancel_plan(self, user_id, old_plan, expired_date=None, scope=settings.SCOPE_PWD_MANAGER):
        try:
            url = API_NOTIFY_PAYMENT + "/notify_cancel"
            notification_data = {
                "user_id": user_id,
                "old_plan": old_plan,
                "expired_date": expired_date,
                "scope": scope
            }
            requests.post(url=url, headers=HEADERS, json=notification_data, verify=False)
        except Exception as e:
            self.log_error(func_name="cancel_plan")
        finally:
            if self.background:
                connection.close()

    def banking_expiring(self, user_id, current_plan, start_period, end_period, payment_method, scope):
        try:
            url = API_NOTIFY_PAYMENT + "/notify_expiring"
            notification_data = {
                "user_id": user_id,
                "current_plan": current_plan,
                "start_period": start_period,
                "end_period": end_period,
                "payment_method": payment_method,
                "scope": scope,
                "demo": False
            }
            requests.post(url=url, headers=HEADERS, json=notification_data, verify=False)
        except Exception as e:
            self.log_error(func_name="banking_expiring")
        finally:
            if self.background:
                connection.close()

    def pay_successfully(self, payment):
        """
        Notify when a payment invoice was paid
        :param payment: (obj) Payment invoice
        :return:
        """
        url = API_NOTIFY_PAYMENT + "/notify_payment_success"
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        try:
            scope = payment.scope
            metadata = payment.get_metadata()
            number_members = metadata.get("number_members")
            user = payment.user
            current_plan = user_repository.get_current_plan(user=user, scope=scope)
            primary_team = user_repository.get_default_team(user=user)
            payment_data = {
                "team_id": primary_team.id if primary_team else None,
                "team_name": primary_team.name if primary_team else None,
                "plan_name": current_plan.get_plan_type_name(),
                "plan_price": current_plan.pm_plan.get_price(currency=payment.currency, duration=payment.duration),
                "number_members": number_members
            }
            subtotal = payment.total_price + payment.discount
            notification_data = {
                "success": True,
                "user_id": payment.user.user_id,
                "status": payment.status,
                "paid": True if payment.status == PAYMENT_STATUS_PAID else False,
                "scope": payment.scope,
                "payment_id": payment.payment_id,
                "order_date": payment.get_created_time_str(),
                "total": payment.total_price,
                "subtotal": subtotal,
                "discount": payment.discount,
                "currency": payment.currency,
                "duration": payment.duration,
                "plan": payment.plan,
                "customer": payment.get_customer_dict(),
                "payment_method": payment.payment_method,
                "payment_data": payment_data
            }
            requests.post(url=url, headers=HEADERS, json=notification_data, verify=False)

        except Exception:
            self.log_error(func_name="notify_pay_successfully")
        finally:
            if self.background:
                connection.close()
