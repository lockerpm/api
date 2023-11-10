from datetime import datetime
from typing import NoReturn, List

import requests
import stripe
import stripe.error
from django.core.exceptions import ObjectDoesNotExist

from locker_server.core.entities.payment.payment import Payment
from locker_server.core.exceptions.payment_exception import PaymentMethodNotSupportException
from locker_server.core.repositories.cipher_repository import CipherRepository
from locker_server.core.repositories.emergency_access_repository import EmergencyAccessRepository
from locker_server.core.repositories.enterprise_domain_repository import EnterpriseDomainRepository
from locker_server.core.repositories.enterprise_member_repository import EnterpriseMemberRepository
from locker_server.core.repositories.enterprise_repository import EnterpriseRepository
from locker_server.core.repositories.event_repository import EventRepository
from locker_server.core.repositories.payment_repository import PaymentRepository
from locker_server.core.repositories.user_plan_repository import UserPlanRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from locker_server.shared.constants.event import *
from locker_server.shared.constants.transactions import *
from locker_server.shared.external_services.hibp.hibp_service import HibpService
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_DOMAIN, BG_NOTIFY
from locker_server.shared.external_services.locker_background.impl import NotifyBackground
from locker_server.shared.external_services.payment_method.payment_method_factory import PaymentMethodFactory
from locker_server.shared.external_services.spreadsheet.spreadsheet import API_USERS, HEADERS
from locker_server.shared.external_services.user_notification.list_jobs import PWD_ASKING_FEEDBACK
from locker_server.shared.log.cylog import CyLog
from locker_server.shared.utils.app import now, convert_readable_date


class CronTaskService:
    """
    This class represents Use Cases related affiliate submission
    """

    def __init__(self, event_repository: EventRepository,
                 cipher_repository: CipherRepository,
                 enterprise_repository: EnterpriseRepository,
                 enterprise_domain_repository: EnterpriseDomainRepository,
                 enterprise_member_repository: EnterpriseMemberRepository,
                 user_repository: UserRepository,
                 user_plan_repository: UserPlanRepository,
                 emergency_access_repository: EmergencyAccessRepository,
                 payment_repository: PaymentRepository
                 ):
        self.event_repository = event_repository
        self.cipher_repository = cipher_repository
        self.enterprise_repository = enterprise_repository
        self.enterprise_domain_repository = enterprise_domain_repository
        self.enterprise_member_repository = enterprise_member_repository
        self.user_repository = user_repository
        self.user_plan_repository = user_plan_repository
        self.emergency_access_repository = emergency_access_repository
        self.payment_repository = payment_repository

    def delete_old_events(self, creation_date_pivot) -> NoReturn:
        return self.event_repository.delete_old_events(creation_date_pivot=creation_date_pivot)

    def delete_trash_ciphers(self, deleted_date_pivot: float) -> NoReturn:
        return self.cipher_repository.delete_trash_ciphers(deleted_date_pivot=deleted_date_pivot)

    def domain_verification(self) -> NoReturn:
        current_time = now()
        unverified_domains = self.enterprise_domain_repository.list_domains(**{
            "verification": False
        })
        for unverified_domain in unverified_domains:
            is_verify = self.enterprise_domain_repository.check_verification(
                domain_id=unverified_domain.domain_id
            )
            # If this domain is verified => Send notification
            if is_verify is True:
                enterprise_id = unverified_domain.enterprise.enterprise_id
                owner_user_id = self.enterprise_member_repository.get_primary_member(
                    enterprise_id=enterprise_id
                ).user.user_id
                BackgroundFactory.get_background(bg_name=BG_DOMAIN, background=False).run(
                    func_name="domain_verified", **{
                        "owner_user_id": owner_user_id,
                        "domain": unverified_domain
                    }
                )
            else:
                # Check the domain is added more than one day?
                if current_time >= unverified_domain.created_time + 86400 and \
                        unverified_domain.is_notify_failed is False:
                    enterprise_id = unverified_domain.enterprise.enterprise_id
                    owner_user_id = self.enterprise_member_repository.get_primary_member(
                        enterprise_id=enterprise_id
                    ).user.user_id
                    BackgroundFactory.get_background(bg_name=BG_DOMAIN, background=False).run(
                        func_name="domain_unverified", **{
                            "owner_user_id": owner_user_id,
                            "domain": unverified_domain
                        }
                    )
                    self.enterprise_domain_repository.update_domain(
                        domain_id=unverified_domain.domain_id,
                        domain_update_data={"is_notify_failed": True}
                    )

    def downgrade_plan(self, scope: str) -> NoReturn:
        downgrade_user_plans = self.user_plan_repository.list_downgrade_plans()
        for pm_user_plan in downgrade_user_plans:
            user = pm_user_plan.user
            pm_plan = pm_user_plan.pm_plan
            current_plan_name = pm_plan.name

            # If user cancels at the end of period => Downgrade
            if pm_user_plan.cancel_at_period_end is True:
                self.user_plan_repository.update_plan(
                    user_id=user.user_id, plan_type_alias=PLAN_TYPE_PM_FREE, scope=scope
                )
                BackgroundFactory.get_background(
                    bg_name=BG_NOTIFY, background=False
                ).run(func_name="downgrade_plan", **{
                    "user_id": user.user_id, "old_plan": current_plan_name, "downgrade_time": now(),
                    "scope": scope
                })
                continue
            # If the subscription by mobile app => Continue
            if pm_user_plan.default_payment_method in [PAYMENT_METHOD_MOBILE]:
                continue

            # Else, check the attempts number
            # Attempts only apply for the Enterprise plan
            if pm_user_plan.pm_plan.is_team_plan and pm_user_plan.attempts < MAX_ATTEMPTS:
                end_period = pm_user_plan.get_next_attempts_duration(
                    current_number_attempts=pm_user_plan.attempts
                ) + now()
                attempts = pm_user_plan.attempts + 1
                updated_pm_user_plan = self.user_plan_repository.update_user_plan_by_id(
                    user_plan_id=pm_user_plan.pm_user_plan_id,
                    user_plan_update_data={
                        "attempts": attempts,
                        "end_period": end_period
                    }
                )
                # Notify for user here
                BackgroundFactory.get_background(
                    bg_name=BG_NOTIFY, background=False
                ).run(func_name="pay_failed", **{
                    "user_id": user.user_id,
                    "current_attempt": updated_pm_user_plan.attempts,
                    "next_attempt": updated_pm_user_plan.get_next_attempts_day_str(
                        current_number_attempts=updated_pm_user_plan.attempts
                    ),
                    "scope": scope
                })
            else:
                # Cancel the subscription of the user and notify for this user
                updated_pm_user_plan = self.user_plan_repository.update_plan(
                    user_id=user.user_id,
                    plan_type_alias=PLAN_TYPE_PM_FREE,
                    scope=scope
                )
                BackgroundFactory.get_background(
                    bg_name=BG_NOTIFY, background=False
                ).run(func_name="downgrade_plan", **{
                    "user_id": user.user_id, "old_plan": current_plan_name, "downgrade_time": now(),
                    "scope": scope
                })

    def auto_approve_emergency_accesses(self):
        return self.emergency_access_repository.auto_approve_emergency_accesses()

    def change_billing_enterprise_member(self, scope):
        current_time = now()
        enterprises = self.enterprise_repository.list_enterprises(**{
            "locked": False
        })
        for enterprise in enterprises:
            primary_member = self.enterprise_member_repository.get_primary_member(
                enterprise_id=enterprise.enterprise_id
            )
            if not primary_member:
                continue
            user_plan = self.user_plan_repository.get_user_plan(user_id=primary_member.user.user_id)
            # Only accept stripe subscription
            stripe_subscription = user_plan.get_stripe_subscription()
            if not stripe_subscription or not user_plan.start_period or not user_plan.end_period:
                continue
            if user_plan.member_billing_updated_time:
                member_billing_updated_time = user_plan.member_billing_updated_time
            else:
                member_billing_updated_time = current_time - 86400
            pm_plan = user_plan.pm_plan
            pm_plan_price = pm_plan.get_price(duration=user_plan.duration, currency="USD")

            # Calc added event
            added_events = self.event_repository.list_events(**{
                "team_id": enterprise.enterprise_id,
                "types": [EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_CONFIRMED],
                "from": member_billing_updated_time,
                "to": current_time
            })
            quantity = len(added_events)
            if quantity == 0:
                continue
            pay_quantity = quantity
            if (enterprise.init_seats and enterprise.init_seats_expired_time
                    and current_time < enterprise.init_seats_expired_time):
                num_active_members = self.enterprise_member_repository.count_enterprise_members(**{
                    "enterprise_id": enterprise.enterprise_id,
                    "status": E_MEMBER_STATUS_CONFIRMED,
                    "is_activated": True
                })
                pay_quantity = max(num_active_members - enterprise.init_seats, 0)
            if pay_quantity <= 0:
                self.user_plan_repository.update_user_plan_by_id(
                    user_plan_id=user_plan.pm_user_plan_id,
                    user_plan_update_data={
                        "member_billing_updated_time": current_time
                    }
                )
                continue
            added_user_ids = list(set([added_event.user_id for added_event in added_events]))
            added_user_ids_str = ",".join(str(v) for v in added_user_ids)
            # Calc prorations
            diff_days = round((user_plan.end_period - current_time) / 86400, 0)
            unit_amount = pm_plan_price * (
                    diff_days / (Payment.get_duration_month_number(duration=user_plan.duration) * 30)
            )

            # Adding invoice items for future invoice
            # https://stripe.com/docs/billing/invoices/subscription#adding-upcoming-invoice-items
            new_added_invoice_item = stripe.InvoiceItem.create(
                customer=stripe_subscription.customer,
                description=f"{pay_quantity} member(s) added into Locker Enterprise",
                unit_amount=int(unit_amount * 100),
                currency="USD",
                quantity=pay_quantity,
                subscription=stripe_subscription.id,
                metadata={
                    "scope": scope,
                    "user_id": primary_member.user.user_id,
                    "category": "member_changes",
                    "added_user_ids": added_user_ids_str
                }
            )
            print(new_added_invoice_item)

            if user_plan.duration == DURATION_YEARLY:
                # Create new invoice and pay immediately
                new_change_member_invoice = stripe.Invoice.create(
                    customer=stripe_subscription.customer,
                    # Auto collect all-pending invoice item
                    collection_method="charge_automatically",
                    pending_invoice_items_behavior="include",
                    metadata={
                        "scope": scope,
                        "user_id": primary_member.user.user_id,
                        "category": "member_changes",
                        "added_user_ids": added_user_ids_str,
                        # The invoice is one-time invoice and the `subscription` property of the invoice object is null
                        # So that we need to set `stripe_subscription_id` in the metadata
                        "stripe_subscription_id": user_plan.pm_stripe_subscription
                    }
                )
                try:
                    paid_invoice = stripe.Invoice.pay(new_change_member_invoice.get("id"))
                    print(paid_invoice)
                except stripe.error.CardError:
                    # Payment failed => Disable members
                    disabled_members = self.enterprise_member_repository.update_batch_enterprise_members_by_user_ids(
                        user_ids=added_user_ids,
                        **{
                            "is_activated": False
                        }
                    )

                    try:
                        PaymentMethodFactory.get_method(
                            user_plan=user_plan, scope=scope,
                            payment_method=PAYMENT_METHOD_CARD
                        ).update_quantity_subscription(amount=-disabled_members)
                    except (PaymentMethodNotSupportException, ObjectDoesNotExist):
                        pass
            else:
                pass
            self.user_plan_repository.update_user_plan_by_id(
                user_plan_id=user_plan.pm_user_plan_id,
                user_plan_update_data={
                    "member_billing_updated_time": current_time
                }
            )

    def pm_expiring_notify(self, scope):
        expiring_plans = self.user_plan_repository.list_expiring_plans()
        for pm_user_plan in expiring_plans:
            user = pm_user_plan.user
            pm_plan = pm_user_plan.pm_plan
            plan_name = pm_plan.name
            if pm_plan.is_team_plan:
                payment_url = "https://enterprise.locker.io/admin/billing/payment-method"
            else:
                payment_url = "https://locker.io/settings/plans-billing"
            BackgroundFactory.get_background(
                bg_name=BG_NOTIFY, background=False
            ).run(func_name="banking_expiring", **{
                "user_id": user.user_id,
                "current_plan": plan_name,
                "start_period": pm_user_plan.start_period,
                "end_period": pm_user_plan.end_period,
                "payment_method": pm_user_plan.get_default_payment_method(),
                "scope": scope,
                "payment_url": payment_url
            })

    def pm_enterprise_reminder(self):
        expiring_enterprise_plans = self.user_plan_repository.list_expiring_enterprise_plans()
        for enterprise_plan in expiring_enterprise_plans:
            stripe_subscription = enterprise_plan.get_stripe_subscription()
            if not stripe_subscription:
                continue
            enterprise = self.user_plan_repository.get_default_enterprise(
                user_id=enterprise_plan.user.user_id
            )
            if not enterprise:
                continue
            start_period = enterprise_plan.start_period
            end_period = enterprise_plan.end_period
            added_events = self.event_repository.list_events(**{
                "team_id": enterprise.enterprise_id,
                "types": [EVENT_E_MEMBER_ENABLED, EVENT_E_MEMBER_CONFIRMED],
                "from": start_period,
                "to": end_period
            })
            removed_events = self.event_repository.list_events(**{
                "team_id": enterprise.enterprise_id,
                "types": [EVENT_E_MEMBER_REMOVED, EVENT_E_MEMBER_DISABLED],
                "from": start_period,
                "to": end_period
            })

            added_members = list(set([event.user_id for event in added_events]))
            removed_members = list(set([event.user_id for event in removed_events]))

            current_active_members = self.enterprise_member_repository.count_enterprise_members(**{
                "enterprise_id": enterprise.enterprise_id,
                "status": E_MEMBER_STATUS_CONFIRMED,
                "is_activated": True
            })

            upcoming_invoice = stripe.Invoice.upcoming(subscription=stripe_subscription.id)
            lines = upcoming_invoice.lines.data
            old_active_members = None
            for line in lines:
                if line.get("plan"):
                    old_active_members = line.get("quantity")
                    break
            next_payment_date = end_period + Payment.get_duration_month_number(
                duration=enterprise_plan.duration
            ) * 30 * 86400
            next_amount = current_active_members * enterprise_plan.pm_plan.get_price(duration=enterprise_plan.duration)
            payment_method = stripe_subscription.default_payment_method or stripe_subscription.default_source

            last4 = None
            if payment_method:
                last4 = stripe.PaymentMethod.retrieve(payment_method).get("card", {}).get("last4")
            NotifyBackground(background=False).notify_enterprise_next_cycle(data={
                "user_ids": [enterprise_plan.user.user_id],
                "date_1": convert_readable_date(start_period, datetime_format="%d/%m/%Y"),
                "date_2": convert_readable_date(end_period, datetime_format="%d/%m/%Y"),
                "date_3": convert_readable_date(next_payment_date, datetime_format="%d/%m/%Y"),
                "active_member_count_first_date": old_active_members,
                "added_member_count": len(added_members),
                "removed_member_count": len(removed_members),
                "billed_member_count_next_cycle": current_active_members,
                "next_cycle_cost": next_amount,
                "card_ending": last4,
            })

    def log_new_users(self):
        current_time_str = datetime.fromtimestamp(now()).strftime("%d-%b-%Y")
        total_user = self.user_repository.count_users(**{
            "activated": True
        })
        new_users = self.user_repository.list_new_users()
        user_ids = [new_user.get("user_id") for new_user in new_users]
        users_res = requests.post(url=API_USERS, headers=HEADERS, json={"ids": user_ids, "emails": []})
        if users_res.status_code != 200:
            CyLog.error(**{"message": "[log_new_users] Get users from Gateway error: {} {}".format(
                users_res.status_code, users_res.text
            )})
            users_data = []
        else:
            users_data = users_res.json()

        notification = ""
        for new_user in new_users:
            user_data = next(
                (item for item in users_data if item["id"] == new_user.get("user_id")), {}
            )
            notification += "{} - {} - {}\n".format(
                user_data.get("email") or new_user.get("user_id"),
                new_user.get("first_device_client_id"),
                new_user.get("first_device_name"),
            )

        CyLog.info(**{
            "message": "Date: {}\nTotal: {}\nNew users: {}\n{}".format(
                current_time_str, total_user, len(new_users), notification
            ),
            "output": ["slack_new_users"]
        })

    def tutorial_reminder(self, duration_unit):
        user_ids_dict = self.user_repository.list_user_ids_tutorial_reminder(duration_unit=duration_unit)
        user_ids_3days = user_ids_dict.get("user_ids_3days")
        user_ids_5days = user_ids_dict.get("user_ids_5days")
        user_ids_7days = user_ids_dict.get("user_ids_7days")
        user_ids_13days = user_ids_dict.get("user_ids_13days")
        user_ids_20days = user_ids_dict.get("user_ids_20days")

        BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_tutorial", **{
                "job": "tutorial_day_3_add_items", "user_ids": user_ids_3days,
            }
        )
        BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_tutorial", **{
                "job": "tutorial_day_5_download", "user_ids": user_ids_5days,
            }
        )
        BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_tutorial", **{
                "job": "tutorial_day_7_autofill", "user_ids": user_ids_7days,
            }
        )
        BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_tutorial", **{
                "job": "tutorial_day_13_trial_end", "user_ids": user_ids_13days,
            }
        )
        BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_tutorial", **{
                "job": "tutorial_day_20_refer_friend", "user_ids": user_ids_20days,
            }
        )

    def breach_scan(self):
        enterprises = self.enterprise_repository.list_enterprises(**{
            "locked": False
        })
        for enterprise in enterprises:
            members = self.enterprise_member_repository.list_enterprise_members(**{
                "enterprise_id": enterprise.enterprise_id
            })
            for member in members:
                user = member.user
                if user.is_leaked:
                    continue
                email = self.user_repository.get_from_cystack_id(user_id=user.user_id).get("email")
                if not email:
                    continue
                hibp_check = HibpService().check_breach(email=email)
                if hibp_check:
                    self.user_repository.update_user(
                        user_id=user.user_id,
                        user_update_data={
                            "is_leaked": True
                        }

                    )

    def asking_for_feedback_after_subscription(self, scope):
        users_feedback = self.payment_repository.list_feedback_after_subscription(after_days=30)
        for user in users_feedback:
            if user.get("first_payment_plan") == PLAN_TYPE_PM_ENTERPRISE:
                review_url = "https://www.g2.com/products/locker-password-manager/reviews#reviews"
            else:
                review_url = "https://www.trustpilot.com/review/locker.io?sort=recency&utm_medium=trustbox&utm_source=MicroReviewCount"
            BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                func_name="notify_locker_mail", **{
                    "user_ids": [user.get("user_id")],
                    "job": PWD_ASKING_FEEDBACK,
                    "scope": scope,
                    "review_url": review_url,
                }
            )
