import time
import logging

from django.db import connection


logger = logging.getLogger('stdout_service')


class QueriesDebugMiddleware(object):
    """
    This middleware will log the number of queries run
    and the total time taken for each request (with a
    status code of 200). It does not currently support
    multi-db setups.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        response = self.process_response(request, response)
        return response

    def process_request(self, request):
        """
        Set Request Start Time to measure time taken to service request.
        """
        request.start_time = time.time()

    def process_response(self, request, response):
        view_name = self._get_view_name(request)
        if response.status_code in [200, 201, 204]:
            total_time = 0
            for query in connection.queries:
                query_time = query.get('time')
                if query_time is None:
                    # The middleware patches the connection cursor wrapper and adds extra information
                    # in each item in connection.queries. The query time is stored under the key "duration" rather than
                    # "time" and is in milliseconds, not seconds.
                    query_time = query.get('duration', 0) / 1000
                total_time += float(query_time)

            total_response_time = time.time() - request.start_time
            logger.debug('%s: %s queries run, total %s seconds' % (
                view_name, len(connection.queries), round(total_response_time, 4)
            ))
        return response

    def _get_view_name(self, request):
        view_name = "<unnamed view>"
        if hasattr(request, "resolver_match"):
            if request.resolver_match is not None:
                if request.resolver_match.view_name is not None:
                    view_name = request.resolver_match.view_name
        return view_name
