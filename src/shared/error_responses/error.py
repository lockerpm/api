import json

from shared.constants.error_code import get_app_code_content


def gen_error(err_code):
    message = get_app_code_content(err_code)
    return json.dumps({"code": err_code, "message": message})


def refer_error(err):
    try:
        return json.loads(err)
    except:
        return err
