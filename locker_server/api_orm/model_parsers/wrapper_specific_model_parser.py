from locker_server.shared.utils.factory import class_name_to_snake_name


def get_specific_model_parser(specific_parser_name: str):
    from locker_server.api_orm.model_parsers.wrapper import get_model_parser
    try:
        return getattr(get_model_parser(), class_name_to_snake_name(specific_parser_name))()
    except AttributeError:
        try:
            return getattr(get_model_parser(), specific_parser_name)()
        except AttributeError:
            return None
