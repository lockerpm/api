from django.db import models

from locker_server.settings import locker_server_settings


class PaymentItemORM(models.Model):
    id = models.AutoField(primary_key=True)
    quantity = models.IntegerField(default=1)
    team_id = models.CharField(max_length=128, blank=True, null=True, default=None)
    payment = models.ForeignKey(
        locker_server_settings.LS_PAYMENT_MODEL, on_delete=models.CASCADE, related_name="payment_items"
    )

    class Meta:
        db_table = 'cs_payment_items'

    @classmethod
    def create_multiple(cls, payment, *items):
        """
        Create multiple payment item
        :param payment: (obj) Payment object
        :param items: (list) List of dict payment item data:
                      [{"quantity":xxx, "team_id": xxx, ...]
        :return:
        """
        list_payment_items = []
        for item in items:
            team_id = item.get("team_id")
            list_payment_items.append(cls(
                payment=payment, team_id=team_id, quantity=item.get("quantity", 1)
            ))
        cls.objects.bulk_create(list_payment_items, ignore_conflicts=True)
