import json
import humps


def camel_snake_data(json_data, camel_to_snake=False, snake_to_camel=False):
    """
    Get JSON response data from HTTPResponse
    :param json_data: (dict) The data is needed to convert
    :param camel_to_snake: (bool) Convert from camel case to snake case
    :param snake_to_camel: (bool) Convert from snake case to camel case
    :return: (dict)
    """
    try:
        if camel_to_snake is True:
            return humps.decamelize(json_data)
        if snake_to_camel is True:
            return humps.camelize(json_data)
        return json_data
    except json.decoder.JSONDecodeError:
        return json_data
