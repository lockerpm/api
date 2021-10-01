from django.db import models

from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.users.users import User


class CipherFavorite(models.Model):
    cipher = models.ForeignKey(Cipher, on_delete=models.CASCADE, related_name="ciphers_favorites")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ciphers_favorites")

    class Meta:
        db_table = 'cs_ciphers_favorites'
        unique_together = ('cipher', 'user')
