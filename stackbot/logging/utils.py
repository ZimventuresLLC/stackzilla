"""Utilities for managing application logging."""
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'core': {
            'format': '%(asctime)s (%(levelname)s:stackbot-%(component)s) %(message)s'
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
        'stackbot.importer': {
            'handlers': ['core'],
            'level': 'DEBUG',
            'propagate': False
        },
        'stackbot.StackBotSQLiteDB': {
            'handlers': ['core'],
            'level': 'DEBUG',
            'propagate': False
        },
        'stackbot.graph': {
            'handlers': ['core'],
            'level': 'DEBUG',
            'propagate': False
        },
        'stackbot-test:volume': {
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
    # TODO: Add support for a logging configuration file to be passed in on the CLI
    logging.config.dictConfig(LOGGING_CONFIG)
