from django.db import models

from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.ciphers.folders import Folder


class CipherFolder(models.Model):
    cipher = models.ForeignKey(Cipher, on_delete=models.CASCADE, related_name="ciphers_folders")
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="ciphers_folders")

    class Meta:
        db_table = 'cs_ciphers_folders'
        unique_together = ('cipher', 'folder')

    @classmethod
    def retrieve_or_create(cls, cipher_id, folder_id):
        """
        Retrieve or create new CipherFolder object
        :param cipher_id: (str) Cipher id
        :param folder_id: (str) Folder id
        :return:
        """
        try:
            cipher_folder = cls.objects.get(cipher_id=cipher_id, folder_id=folder_id)
        except cls.DoesNotExist:
            cipher_folder = cls(cipher_id=cipher_id, folder_id=folder_id)
            cipher_folder.save()
        return cipher_folder

    @classmethod
    def create_multiple(cls, folder_id, *ciphers):
        cipher_folder = []
        for cipher in ciphers:
            cipher_folder.append(
                cls(cipher=cipher, folder_id=folder_id)
            )
        cls.objects.bulk_create(cipher_folder, ignore_conflicts=True)

