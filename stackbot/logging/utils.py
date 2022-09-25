"""Utilities for managing application logging."""
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s (%(levelname)s:stackbot-%(component)s) %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False
        },
        'stackbot.importer': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        'stackbot.StackBotSQLiteDB': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        'stackbot.graph': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}

def setup_logging():
    """Initialize the logging subsystem."""
    # TODO: Add support for a logging configuration file to be passed in on the CLI
    logging.config.dictConfig(LOGGING_CONFIG)
