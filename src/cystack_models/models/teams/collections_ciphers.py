from django.db import models

from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.teams.collections import Collection


class CollectionCipher(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="collections_ciphers")
    cipher = models.ForeignKey(Cipher, on_delete=models.CASCADE, related_name="collections_ciphers")

    class Meta:
        db_table = 'cs_collections_ciphers'
        unique_together = ('collection', 'cipher')

    @classmethod
    def retrieve_or_create(cls, cipher_id, collection_id):
        try:
            collection_cipher = cls.objects.get(collection_id=collection_id, cipher_id=cipher_id)
        except cls.DoesNotExist:
            collection_cipher = cls(collection_id=collection_id, cipher_id=cipher_id)
            collection_cipher.save()
        return collection_cipher

    @classmethod
    def create_multiple(cls, cipher_id, *collection_ids):
        collection_ciphers = []
        for collection_id in collection_ids:
            collection_ciphers.append(
                cls(cipher_id=cipher_id, collection_id=collection_id)
            )
        cls.objects.bulk_create(collection_ciphers, ignore_conflicts=True)

    @classmethod
    def create_multiple_for_collection(cls, collection_id, *cipher_ids):
        collection_ciphers = []
        for cipher_id in cipher_ids:
            collection_ciphers.append(
                cls(collection_id=collection_id, cipher_id=cipher_id)
            )
        cls.objects.bulk_create(collection_ciphers, ignore_conflicts=True)