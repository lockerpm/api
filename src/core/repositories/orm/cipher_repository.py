from core.repositories import ICipherRepository

from shared.utils.app import now
from cystack_models.models.ciphers.ciphers import Cipher


class CipherRepository(ICipherRepository):
    def get_favorite_users(self, cipher: Cipher):
        pass

    def get_folder_ids(self, cipher: Cipher):
        pass

    def save_new_cipher(self, cipher_data):
        cipher = Cipher(
            creation_date=cipher_data.get("creation_date", now()),
            revision_date=cipher_data.get("revision_date", now()),
            deleted_date=cipher_data.get("deleted_date"),
            reprompt=cipher_data.get("reprompt", 0),
            score=cipher_data.get("score", 0),
            type=cipher_data.get("type"),
            data=cipher_data.get("data"),
            favorites=cipher_data.get("favorites"),

        )