import traceback
import logging.config

from rest_framework.views import exception_handler
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework import status

from shared.error_responses.error import refer_error, gen_error


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context['request']

    if isinstance(exc, ParseError):
        return Response(status=400, data={"code": "0004",
                                          "message": "Invalid data",
                                          "details": {}})

    try:
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_detail = response.data    # Dict errors
            response.data = dict()
            response.data['details'] = error_detail

            if "non_field_errors" in error_detail:
                error_detail = refer_error(error_detail["non_field_errors"][0])
                response.data['message'] = error_detail["message"]
                response.data['code'] = error_detail["code"]
                response.data['details'] = error_detail.get("details", {})
            else:
                response.data.update(refer_error(gen_error("0004")))

        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            response.data = refer_error(gen_error("0000"))
            response.data['details'] = {}
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            response.data = refer_error(gen_error("0002"))
            response.data['details'] = {}
        elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            response.data = refer_error(gen_error("0005"))
            response.data['details'] = {}
        if response is not None:
            pass
    except TypeError:
        response = Response(status=400, data={"code": "0004",
                                              "message": "Invalid data"})
    except Exception as e:
        from shared.log.config import logging_config
        logging.config.dictConfig(logging_config)
        logger = logging.getLogger('slack_service')
        tb = traceback.format_exc()
        logger.debug(tb)
        logger.debug("Request: {} {} - {}\nRequest data: {}".format(
            request.user,
            request.method,
            request.build_absolute_uri(),
            request.data
        ))
    return response
