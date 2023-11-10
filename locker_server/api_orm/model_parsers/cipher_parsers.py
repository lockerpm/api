from locker_server.api_orm.model_parsers.wrapper_specific_model_parser import get_specific_model_parser
from locker_server.api_orm.models import *
from locker_server.core.entities.cipher.cipher import Cipher
from locker_server.core.entities.cipher.folder import Folder


class CipherParser:
    @classmethod
    def parse_cipher(cls, cipher_orm: CipherORM, parse_collection_ids=False) -> Cipher:
        user_parser = get_specific_model_parser("UserParser")
        team_parser = get_specific_model_parser("TeamParser")
        try:
            view_password = getattr(cipher_orm, "view_password")
        except AttributeError:
            view_password = True
        cipher = Cipher(
            cipher_id=cipher_orm.id,
            creation_date=cipher_orm.creation_date,
            revision_date=cipher_orm.revision_date,
            deleted_date=cipher_orm.deleted_date,
            last_use_date=cipher_orm.last_use_date,
            num_use=cipher_orm.num_use,
            reprompt=cipher_orm.reprompt,
            score=cipher_orm.score,
            cipher_type=cipher_orm.type,
            data=cipher_orm.get_data(),
            folders=cipher_orm.get_folders(),
            favorites=cipher_orm.get_favorites(),
            view_password=view_password,
            user=user_parser.parse_user(user_orm=cipher_orm.user) if cipher_orm.user else None,
            created_by=user_parser.parse_user(user_orm=cipher_orm.created_by) if cipher_orm.created_by else None,
            team=team_parser.parse_team(team_orm=cipher_orm.team) if cipher_orm.team else None,
        )
        if parse_collection_ids is True:
            collection_ids = []
            try:
                if cipher_orm.collections_ciphers.exists():
                    collection_ids = list(cipher_orm.collections_ciphers.values_list('collection_id', flat=True))
            except AttributeError:
                pass
            cipher.collection_ids = collection_ids
        return cipher

    @classmethod
    def parse_folder(cls, folder_orm: FolderORM) -> Folder:
        user_parser = get_specific_model_parser("UserParser")
        return Folder(
            folder_id=folder_orm.id,
            name=folder_orm.name,
            creation_date=folder_orm.creation_date,
            revision_date=folder_orm.revision_date,
            user=user_parser.parse_user(user_orm=folder_orm.user)
        )

