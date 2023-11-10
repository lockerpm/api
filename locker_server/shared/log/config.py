import logging
import socket

from django.utils.log import DEFAULT_LOGGING


class SiteFilter(logging.Filter):
    def filter(self, record):
        record.site = socket.gethostname()
        return True


logging_config = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'site_filter': {
            '()': 'locker_server.shared.log.config.SiteFilter',
        }
    },
    'formatters': {
        'medium': {'format': '%(asctime)s %(site)s %(levelname)s %(message)s'},
        'short': {'format': '%(message)s'},
        'django.server': DEFAULT_LOGGING['formatters']['django.server'],
        'rq_console': {
            'format': '%(asctime)s %(levelname)s %(message)s',
            'datefmt': '%H:%M:%S',
        },
    },
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
            'formatter': 'medium',
            'level': logging.DEBUG
        },
        'slack': {
            'class': 'locker_server.shared.log.handlers.SlackHandler',
            'formatter': 'medium',
            'level': logging.DEBUG,
            'filters': ['site_filter']
        },
        'slack_new_users': {
            'class': 'locker_server.shared.log.handlers.SlackNewUserHandler',
            'formatter': 'medium',
            'level': logging.DEBUG,
            'filters': ['site_filter']
        },
        'console': {
            'level': logging.DEBUG,
            'class': 'logging.StreamHandler',
            'formatter': 'medium',
            'filters': ['site_filter']
        },
        'django.server': DEFAULT_LOGGING['handlers']['django.server'],
        'rq_console': {
            'level': 'DEBUG',
            'class': 'rq.logutils.ColorizingStreamHandler',
            'formatter': 'rq_console',
            # 'exclude': ['%(asctime)s'],
        },
    },
    'root': {
        'handlers': ['django.server'],
        'level': logging.DEBUG,
    },
    'loggers': {
        'slack_service': {
            'handlers': ['slack', ],
            'level': 'DEBUG',
            'propagate': True,
            'filters': ['site_filter']
        },
        'slack_new_users_service': {
            'handlers': ['slack_new_users', ],
            'level': 'DEBUG',
            'propagate': True,
            'filters': ['site_filter']
        },
        'stdout_service': {
            'level': 'DEBUG',
            'handlers': ['console', ],
            'propagate': True
        },
        # 'django.server': DEFAULT_LOGGING['loggers']['django.server'],
        'django.channels.server': DEFAULT_LOGGING['loggers']['django.server'],
        'rq.worker': {
            'level': 'DEBUG',
            'handlers': ['rq_console'],
        },
    }
}
