from django.db import models

from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.teams.collections import Collection


class CollectionCipher(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="collections_ciphers")
    cipher = models.ForeignKey(Cipher, on_delete=models.CASCADE, related_name="collections_ciphers")

    class Meta:
        db_table = 'cs_collections_ciphers'
        unique_together = ('collection', 'cipher')
