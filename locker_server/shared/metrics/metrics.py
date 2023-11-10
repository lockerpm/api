from prometheus_client import Histogram, Counter


class Metrics:
    # number_query = Histogram(
    #     'request_number_query',
    #     'The queries number of the request',
    #     ['view', 'method']
    # )
    number_queries = Counter(
        'request_number_queries',
        'The number queries of the request',
        ['view', 'method']
    )
