from locker_server.core.entities.payment.payment import Payment


class PaymentItem(object):
    def __init__(self, payment_item_id: int, quantity: int = 1, team_id: str = None, payment: Payment = None):
        self._payment_item_id = payment_item_id
        self._quantity = quantity
        self._team_id = team_id
        self._payment = payment

    @property
    def payment_item_id(self):
        return self._payment_item_id

    @property
    def quantity(self):
        return self._quantity

    @property
    def team_id(self):
        return self._team_id

    @property
    def payment(self):
        return self._payment
