"""Utilities for managing application logging."""
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'core': {
            'format': '%(asctime)s (%(levelname)s:stackzilla-%(component)s) %(message)s'
        },
        'provider': {
            'format': '%(asctime)s (%(levelname)s:%(provider)s) %(message)s'
        },
    },
    'handlers': {
        'core': {
            'level': 'DEBUG',
            'formatter': 'core',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'provider': {
            'level': 'DEBUG',
            'formatter': 'provider',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['core'],
            'level': 'WARNING',
            'propagate': False
        },
        'stackzilla.importer': {
            'handlers': ['core'],
            'level': 'INFO',
            'propagate': False
        },
        'stackzilla.StackzillaSQLiteDB': {
            'handlers': ['core'],
            'level': 'DEBUG',
            'propagate': False
        },
        'stackzilla.graph': {
            'handlers': ['core'],
            'level': 'DEBUG',
            'propagate': False
        },
        'stackzilla.resource': {
            'handlers': ['core'],
            'level': 'DEBUG',
            'propagate': False
        },
        'stackzilla-test:volume': {
            'handlers': ['provider'],
            'level': 'DEBUG',
            'propagate': False
        },
         'linode.volume': {
            'handlers': ['provider'],
            'level': 'DEBUG',
            'propagate': False
        },
         'linode.instance': {
            'handlers': ['provider'],
            'level': 'DEBUG',
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['core'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}

def setup_logging():
    """Initialize the logging subsystem."""
    logging.config.dictConfig(LOGGING_CONFIG)
