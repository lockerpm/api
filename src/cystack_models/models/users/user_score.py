from django.db import models

from cystack_models.models.users.users import User


class UserScore(models.Model):
    user = models.OneToOneField(
        User, to_field='user_id', primary_key=True, related_name="user_score", on_delete=models.CASCADE
    )
    cipher0 = models.FloatField(default=0)
    cipher1 = models.FloatField(default=0)
    cipher2 = models.FloatField(default=0)
    cipher3 = models.FloatField(default=0)
    cipher4 = models.FloatField(default=0)

    class Meta:
        db_table = 'cs_user_score'

    @classmethod
    def create(cls, user: User):
        new_bw_user_score = cls(user=user)
        new_bw_user_score.save()
        return new_bw_user_score
