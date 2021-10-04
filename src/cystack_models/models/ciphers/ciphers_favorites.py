from django.db import models

from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.users.users import User


class CipherFavorite(models.Model):
    cipher = models.ForeignKey(Cipher, on_delete=models.CASCADE, related_name="ciphers_favorites")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ciphers_favorites")

    class Meta:
        db_table = 'cs_ciphers_favorites'
        unique_together = ('cipher', 'user')

    @classmethod
    def retrieve_or_create(cls, cipher_id, user_id):
        """
        Create new CipherFavorite object
        :param cipher_id: Cipher id
        :param user_id: User id
        :return:
        """
        try:
            cipher_favorite = cls.objects.get(cipher_id=cipher_id, user_id=user_id)
        except cls.DoesNotExist:
            cipher_favorite = cls(cipher_id=cipher_id, user_id=user_id)
            cipher_favorite.save()
        return cipher_favorite
