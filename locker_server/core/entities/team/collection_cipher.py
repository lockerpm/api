from locker_server.core.entities.cipher.cipher import Cipher
from locker_server.core.entities.team.collection import Collection


class CollectionCipher(object):
    def __init__(self, collection_cipher_id: int, collection: Collection, cipher: Cipher):
        self._collection_cipher_id = collection_cipher_id
        self._collection = collection
        self._cipher = cipher

    @property
    def collection_cipher_id(self):
        return self._collection_cipher_id

    @property
    def collection(self):
        return self._collection

    @property
    def cipher(self):
        return self._cipher
