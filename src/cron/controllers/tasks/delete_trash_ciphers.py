from shared.utils.app import now
from cystack_models.models.ciphers.ciphers import Cipher


def delete_trash_ciphers():
    current_time = now()
    # Delete ciphers in trash if deleted time less than 30 days
    Cipher.objects.filter(deleted_date__lte=current_time-30*86400).delete()
