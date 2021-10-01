from django.db import models

from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.ciphers.folders import Folder


class CipherFolder(models.Model):
    cipher = models.ForeignKey(Cipher, on_delete=models.CASCADE, related_name="ciphers_folders")
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="ciphers_folders")

    class Meta:
        db_table = 'cs_ciphers_folders'
        unique_together = ('cipher', 'folder')

