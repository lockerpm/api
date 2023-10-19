from django.db import connection

from core.settings import CORE_CONFIG
from shared.background.i_background import ILockerBackground
from shared.services.pm_sync import PwdSync, SYNC_EVENT_VAULT, SYNC_EVENT_CIPHER_DELETE, SYNC_EVENT_CIPHER_RESTORE


class CipherBackground(ILockerBackground):
    team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
    cipher_repository = CORE_CONFIG["repositories"]["ICipherRepository"]()

    def multiple_delete(self, cipher_ids, user):
        try:
            deleted_cipher_ids = self.cipher_repository.delete_multiple_cipher(
                cipher_ids=cipher_ids, user_deleted=user
            )
            # Sync event
            deleted_ciphers = self.cipher_repository.get_multiple_by_ids(cipher_ids=deleted_cipher_ids)
            teams = self.team_repository.get_multiple_team_by_ids(deleted_ciphers.values_list('team_id', flat=True))
            PwdSync(event=SYNC_EVENT_CIPHER_DELETE, user_ids=[user.user_id], teams=teams, add_all=True).send(
                data={"ids": list(deleted_cipher_ids)}
            )
        except Exception as e:
            self.log_error(func_name="multiple_delete")
        finally:
            if self.background:
                connection.close()

    def multiple_restore(self, cipher_ids, user):
        try:
            restored_cipher_ids = self.cipher_repository.restore_multiple_cipher(
                cipher_ids=cipher_ids, user_restored=user
            )
            # Sync event
            restored_ciphers = self.cipher_repository.get_multiple_by_ids(cipher_ids=restored_cipher_ids)
            teams = self.team_repository.get_multiple_team_by_ids(list(restored_ciphers.values_list('team_id', flat=True)))
            PwdSync(event=SYNC_EVENT_CIPHER_RESTORE, user_ids=[user.user_id], teams=teams, add_all=True).send(
                data={"ids": list(restored_cipher_ids)}
            )
        except Exception as e:
            self.log_error(func_name="multiple_restore")
        finally:
            if self.background:
                connection.close()
