from datetime import datetime
import requests

from django.conf import settings
from django.db import connection

from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.shared.constants.transactions import PAYMENT_STATUS_PAID
from locker_server.shared.external_services.locker_background.background import LockerBackground
from locker_server.shared.external_services.requester.retry_requester import requester
from locker_server.shared.external_services.user_notification.list_jobs import PWD_ACCOUNT_DOWNGRADE, \
    PWD_CARD_PAYMENT_FAILED, PWD_BANK_TRANSFER_EXPIRED, PWD_ENTERPRISE_NEXT_PAYMENT_CYCLE
from locker_server.shared.external_services.user_notification.notification_sender import NotificationSender, \
    SENDING_SERVICE_MAIL
from locker_server.shared.utils.app import now


API_NOTIFY_PAYMENT = "{}/micro_services/cystack_platform/payments".format(settings.GATEWAY_API)
API_NOTIFY_LOCKER = "{}/micro_services/cystack_platform/pm/notify".format(settings.GATEWAY_API)
HEADERS = {
    'User-agent': 'Locker Password Manager API',
    "Authorization": settings.MICRO_SERVICE_USER_AUTH
}


class NotifyBackground(LockerBackground):
    def downgrade_plan(self, user_id, old_plan, downgrade_time, scope, **metadata):
        from locker_server.containers.containers import user_service
        try:
            try:
                user_plan = user_service.get_current_plan(user=user_service.retrieve_by_id(user_id=user_id))
                current_plan = f"{user_plan.pm_plan.name} Plan"
                # Don't notify if the current plan is the same old plan
                if user_plan.pm_plan.name == old_plan or current_plan == old_plan:
                    return
            except UserDoesNotExistException:
                current_plan = "Free Plan"

            if not settings.SELF_HOSTED:
                url = API_NOTIFY_PAYMENT + "/notify_downgrade"
                notification_data = {
                    "user_id": user_id,
                    "old_plan": old_plan,
                    "current_plan": current_plan,
                    "downgrade_time": downgrade_time,
                    "payment_data": metadata.get("payment_data"),
                    "scope": scope
                }
                requester(method="POST", url=url, headers=HEADERS, data_send=notification_data)
            else:
                try:
                    user_obj = user_service.retrieve_by_id(user_id=user_id)
                    downgrade_time_str = "{} (UTC)".format(
                        datetime.utcfromtimestamp(downgrade_time).strftime('%H:%M:%S %d-%m-%Y')
                    )
                    NotificationSender(job=PWD_ACCOUNT_DOWNGRADE, scope=scope, services=[SENDING_SERVICE_MAIL]).send(**{
                        "user_ids": [user_id],
                        "email": user_obj.email,
                        "prior_plan": old_plan,
                        "downgrade_time": downgrade_time_str,
                        "current_plan": current_plan
                    })
                except UserDoesNotExistException:
                    pass

        except requests.ConnectionError:
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
            requester(method="POST", url=url, headers=HEADERS, data_send=notification_data)
        except requests.ConnectionError:
            self.log_error(func_name="cancel_plan")
        finally:
            if self.background:
                connection.close()

    def banking_expiring(self, user_id, current_plan, start_period, end_period, payment_method, scope,
                         payment_url=None):
        from locker_server.containers.containers import user_service
        try:
            url = API_NOTIFY_PAYMENT + "/notify_expiring"
            notification_data = {
                "user_id": user_id,
                "current_plan": current_plan,
                "start_period": start_period,
                "end_period": end_period,
                "payment_method": payment_method,
                "scope": scope,
                "payment_url": payment_url,
                "demo": False
            }
            if not settings.SELF_HOSTED:
                requester(method="POST", url=url, headers=HEADERS, data_send=notification_data)
            else:
                try:
                    user_obj = user_service.retrieve_by_id(user_id=user_id)
                    NotificationSender(
                        job=PWD_BANK_TRANSFER_EXPIRED, scope=scope,services=[SENDING_SERVICE_MAIL]
                    ).send(**{
                        "user_ids": [user_id],
                        "account": user_obj.email,
                        "plan": current_plan,
                        "email": user_obj.email,
                        "start_date": "{} (UTC)".format(
                            datetime.utcfromtimestamp(start_period).strftime('%H:%M:%S %d-%m-%Y')
                        ),
                        "expire_date": "{} (UTC)".format(
                            datetime.utcfromtimestamp(end_period).strftime('%H:%M:%S %d-%m-%Y')
                        ),
                        "payment_method": payment_method,
                        "payment_url": payment_url
                    })
                except UserDoesNotExistException:
                    pass

        except requests.ConnectionError:
            self.log_error(func_name="banking_expiring")
        finally:
            if self.background:
                connection.close()

    def trial_successfully(self, user_id: int, plan: str, payment_method: str, duration: str):
        url = API_NOTIFY_PAYMENT + "/notify_trial"
        try:
            notification_data = {
                "user_id": user_id,
                "scope": settings.SCOPE_PWD_MANAGER,
                "plan": plan,
                "payment_method": payment_method,
                "duration": duration
            }
            requester(method="POST", url=url, headers=HEADERS, data_send=notification_data)
        except requests.ConnectionError:
            self.log_error(func_name="trial_successfully")
        finally:
            if self.background:
                connection.close()

    def trial_enterprise_successfully(self, user_id: int, scope: str = None):
        url = API_NOTIFY_PAYMENT + "/notify_trial_enterprise"
        try:
            notification_data = {"user_id": user_id, "scope": scope or settings.SCOPE_PWD_MANAGER}
            requester(method="POST", url=url, headers=HEADERS, data_send=notification_data)
        except requests.ConnectionError:
            self.log_error(func_name="trial_enterprise_successfully")
        finally:
            if self.background:
                connection.close()

    def pay_successfully(self, payment, payment_platform="Stripe"):
        """
        Notify when a payment invoice was paid
        :param payment: (obj) Payment invoice
        :param payment_platform: (str)
        :return:
        """
        url = API_NOTIFY_PAYMENT + "/notify_payment_success"

        try:
            scope = payment.scope
            metadata = payment.metadata
            number_members = metadata.get("number_members") or 1
            user = payment.user

            from locker_server.containers.containers import user_service
            current_plan = user_service.get_current_plan(user=user)
            enterprise = user_service.get_default_enterprise(user_id=user.user_id)
            payment_data = {
                "enterprise_id": enterprise.enterprise_id if enterprise else None,
                "enterprise_name": enterprise.name if enterprise else None,
                "stripe_invoice_id": payment.stripe_invoice_id,
                "plan_name": current_plan.pm_plan.name,
                "plan_price": current_plan.pm_plan.get_price(currency=payment.currency, duration=payment.duration),
                "number_members": int(number_members),
                "start_period": current_plan.start_period,
                "end_period": current_plan.end_period
            }
            subtotal = payment.total_price + payment.discount
            notification_data = {
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
                "payment_data": payment_data,
                "payment_platform": payment_platform
            }
            requester(method="POST", url=url, headers=HEADERS, data_send=notification_data)
        except Exception:
            self.log_error(func_name="notify_pay_successfully")
        finally:
            if self.background:
                connection.close()

    def pay_failed(self, **data):
        from locker_server.containers.containers import user_service

        url = API_NOTIFY_PAYMENT + "/notify_payment_failed"
        try:
            notification_data = {
                "scope": data.get("scope"),
                "user_id": data.get("user_id"),
                "check_time": "{} (UTC)".format(
                    datetime.utcfromtimestamp(now()).strftime('%H:%M:%S %d-%m-%Y')
                ),
                "current_attempt": data.get("current_attempt"),
                "next_attempt": data.get("next_attempt"),
            }
            if not settings.SELF_HOSTED:
                requester(method="POST", url=url, headers=HEADERS, data_send=notification_data)
            else:
                user_id = data.get("user_id")
                try:
                    user_obj = user_service.retrieve_by_id(user_id=user_id)
                    mail_data = notification_data.copy()
                    mail_data.update({
                        "user_ids": [user_id],
                        "account": user_obj.email,
                        "email": user_obj.email,
                        "user_fullname": user_obj.full_name,
                        "language": user_obj.language,
                    })
                    mail_data.pop("scope", None)
                    NotificationSender(
                        job=PWD_CARD_PAYMENT_FAILED, scope=data.get("scope"), services=[SENDING_SERVICE_MAIL]
                    ).send(**notification_data)
                except UserDoesNotExistException:
                    pass
        except Exception:
            self.log_error(func_name="notify_pay_failed")
        finally:
            if self.background:
                connection.close()

    def notify_tutorial(self, job, user_ids):
        url = API_NOTIFY_LOCKER + "/tutorial"
        try:
            notification_data = {"job": job, "user_ids": user_ids}
            if not settings.SELF_HOSTED:
                requester(
                    method="POST", url=url, headers=HEADERS, data_send=notification_data,
                    retry=True, max_retries=3, timeout=5
                )
            else:
                NotificationSender(
                    job=job, scope=settings.SCOPE_PWD_MANAGER, services=[SENDING_SERVICE_MAIL]
                ).send(**{"user_ids": user_ids, "cc": notification_data.get("cc", [])})
        except Exception:
            self.log_error(func_name="notify_tutorial")
        finally:
            if self.background:
                connection.close()

    def notify_add_group_member_to_share(self, data):
        url = API_NOTIFY_LOCKER + "/group_member_to_share"
        try:
            if not settings.SELF_HOSTED:
                requester(
                    method="POST", url=url, headers=HEADERS, data_send=data,
                    retry=True, max_retries=3, timeout=5
                )
        except Exception:
            self.log_error(func_name="notify_tutorial")
        finally:
            if self.background:
                connection.close()

    def notify_enterprise_next_cycle(self, data):
        url = API_NOTIFY_LOCKER + "/enterprise_next_cycle"
        try:
            if not settings.SELF_HOSTED:
                requester(
                    method="POST", url=url, headers=HEADERS, data_send=data,
                    retry=True, max_retries=3, timeout=5
                )
            else:
                NotificationSender(
                    job=PWD_ENTERPRISE_NEXT_PAYMENT_CYCLE, scope=settings.SCOPE_PWD_MANAGER,
                    services=[SENDING_SERVICE_MAIL]
                ).send(**data)
        except Exception:
            self.log_error(func_name="notify_enterprise_next_cycle")
        finally:
            if self.background:
                connection.close()

    def notify_enterprise_export(self, data):
        url = API_NOTIFY_LOCKER + "/enterprise_export"
        try:
            requester(
                method="POST", url=url, headers=HEADERS, data_send=data,
                retry=True, max_retries=3, timeout=5
            )
        except Exception:
            self.log_error(func_name="notify_enterprise_export")
        finally:
            if self.background:
                connection.close()

    def notify_locker_mail(self, **data):
        url = API_NOTIFY_LOCKER + "/mail"
        try:
            if "scope" not in data:
                data.update({"scope": settings.SCOPE_PWD_MANAGER})
            if not settings.SELF_HOSTED:
                requester(method="POST", url=url, headers=HEADERS, data_send=data, retry=True, max_retries=3, timeout=5)
            else:
                mail_data = data.copy()
                job = mail_data.get("job")
                scope = mail_data.get("scope", settings.SCOPE_PWD_MANAGER)
                services = mail_data.get("services", [SENDING_SERVICE_MAIL])
                mail_data.pop("job", None)
                mail_data.pop("scope", None)
                mail_data.pop("services", None)
                NotificationSender(job=job, scope=scope, services=services).send(**mail_data)
        except Exception:
            self.log_error(func_name="notify_locker_mail")
        finally:
            if self.background:
                connection.close()

    def notify_sending(self, **kwargs):
        services = kwargs.get("services", [SENDING_SERVICE_MAIL])
        if not services:
            return
        try:
            job = kwargs.get("job")
            NotificationSender(job=job, services=services, background=False).send(**kwargs)
        except Exception:
            self.log_error(func_name="notify_sending")
        finally:
            if self.background:
                connection.close()
