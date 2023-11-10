class NotificationCategory(object):
    def __init__(self, notification_category_id: str, name: str, name_vi: str,
                 notification: bool = True, mail: bool = True, order_number: int = None):
        self._notification_category_id = notification_category_id
        self._name = name
        self._name_vi = name_vi
        self._notification = notification
        self._mail = mail
        self._order_number = order_number

    @property
    def notification_category_id(self):
        return self._notification_category_id

    @property
    def name(self):
        return self._name

    @property
    def name_vi(self):
        return self._name_vi

    @property
    def notification(self):
        return self._notification

    @property
    def mail(self):
        return self._mail

    @property
    def order_number(self):
        return self._order_number
