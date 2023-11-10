from locker_server.api_orm.model_parsers.model_parsers import ModelParser
from locker_server.settings import locker_server_settings


def get_model_parser() -> ModelParser:
    return locker_server_settings.MODEL_PARSER_CLASS
