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
            '()': 'shared.log.config.SiteFilter',
        }
    },
    'formatters': {
        'medium': {'format': '%(asctime)s %(site)s %(levelname)s %(message)s'},
        'short': {'format': '%(message)s'},
        'django.server': DEFAULT_LOGGING['formatters']['django.server'],
    },
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
            'formatter': 'medium',
            'level': logging.DEBUG
        },
        'slack': {
            'class': 'shared.log.handlers.SlackHandler',
            'formatter': 'medium',
            'level': logging.DEBUG,
            'filters': ['site_filter']
        },
        'slack_new_users': {
            'class': 'shared.log.handlers.SlackNewUserHandler',
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
        'django.server': DEFAULT_LOGGING['handlers']['django.server']
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
        'django.server': DEFAULT_LOGGING['loggers']['django.server'],
    }
}
