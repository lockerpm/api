from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.factor2 import FA2_METHOD_SMART_OTP, FA2_METHOD_MAIL_OTP
from locker_server.shared.utils.app import now


class Factor2MethodORM(models.Model):
    method = models.CharField(max_length=64)
    is_activate = models.BooleanField()
    activate_code = models.CharField(max_length=16, blank=True, default="")
    code_expired_time = models.IntegerField(default=0)
    updated_time = models.IntegerField(default=0)
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="factor2_methods"
    )

    class Meta:
        db_table = 'cs_factor2_methods'
        unique_together = ('method', 'user')

    @classmethod
    def retrieve_or_create(cls, user_id: int, **data):
        method = data.get("method")
        factor2_method, is_created = cls.objects.get_or_create(
            user_id=user_id, method=method,
            defaults={
                "user_id": user_id,
                "method": method,
                "is_activate": data.get("is_activated", False),
                "updated_time": now()
            }
        )
        return factor2_method

    @classmethod
    def user_retrieve_or_create_factor2(cls, user):
        methods = [FA2_METHOD_SMART_OTP, FA2_METHOD_MAIL_OTP]
        fa2_methods_obj = []
        for method in methods:
            factor2_method = cls.retrieve_or_create(user, **{
                "method": method,
                "is_activate": False
            })
            fa2_methods_obj.append(factor2_method)
        return tuple(fa2_methods_obj)

    @classmethod
    def update_or_create(cls, user_id: int, **data):
        method = data.get("method")
        factor2_method, is_created = cls.objects.update_or_create(
            user_id=user_id, method=method,
            defaults={
                "user_id": user_id, "method": method,
                "is_activate": data.get("is_activated", False),
                "updated_time": now()
            }
        )
        return factor2_method
