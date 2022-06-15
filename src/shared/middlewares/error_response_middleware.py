from django.http import JsonResponse

from shared.log.cylog import CyLog


class ErrorResponseMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        if response.status_code == 403:
            response = JsonResponse(status=403, data={
                "code": "0002",
                "message": "The account does not have enough permission to execute this operation"
            })

        if response.status_code == 404:
            response = JsonResponse(status=404, data={
                "code": "0001",
                "message": "The requested resource does not exist"
            })

        if response.status_code == 500:
            response = JsonResponse(status=500, data={
                "code": "0008",
                "message": "Unknown Error"
            })

        return response

    def process_exception(self, request, exception):
        import traceback
        tb = traceback.format_exc()
        CyLog.error(**{'message': tb})
