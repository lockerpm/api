from django.db import connection

from locker_server.shared.external_services.locker_background.background import LockerBackground
from locker_server.shared.external_services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_DELETE, SYNC_EVENT_CIPHER_RESTORE


class CipherBackground(LockerBackground):

    def multiple_delete(self, cipher_ids, user):
        from locker_server.containers.containers import cipher_service

        try:
            deleted_cipher_ids = cipher_service.delete_multiple_ciphers(
                cipher_ids=cipher_ids, user_id_deleted=user.user_id
            )
            # Sync event
            deleted_ciphers = cipher_service.get_multiple_by_ids(cipher_ids=deleted_cipher_ids)
            teams = [deleted_cipher.team for deleted_cipher in deleted_ciphers if deleted_cipher.team]
            PwdSync(event=SYNC_EVENT_CIPHER_DELETE, user_ids=[user.user_id], teams=teams, add_all=True).send(
                data={"ids": list(deleted_cipher_ids)}
            )
        except Exception as e:
            self.log_error(func_name="multiple_delete")
        finally:
            if self.background:
                connection.close()

    def multiple_restore(self, cipher_ids, user):
        from locker_server.containers.containers import cipher_service

        try:
            restored_cipher_ids = cipher_service.restore_multiple_ciphers(
                cipher_ids=cipher_ids, user_id_restored=user.user_id
            )

            # Sync event
            restored_ciphers = cipher_service.get_multiple_by_ids(cipher_ids=restored_cipher_ids)
            teams = [restored_cipher.team for restored_cipher in restored_ciphers if restored_cipher.team]
            PwdSync(event=SYNC_EVENT_CIPHER_RESTORE, user_ids=[user.user_id], teams=teams, add_all=True).send(
                data={"ids": list(restored_cipher_ids)}
            )
        except Exception as e:
            self.log_error(func_name="multiple_restore")
        finally:
            if self.background:
                connection.close()
