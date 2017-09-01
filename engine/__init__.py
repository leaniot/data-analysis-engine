import logging
from logging.config import dictConfig

logging_config = dict(
    version=1,
    formatters={
        'f': {'format': '[%(levelname)s] %(asctime)s %(name)s [%(lineno)d] %(message)s'}
    },
    handlers={
        'h': {'class': 'logging.StreamHandler', 'formatter': 'f', 'level': logging.DEBUG}
    },
    root={'handlers': ['h'], 'level': logging.DEBUG}
)
dictConfig(logging_config)
logger = logging.getLogger('analysis')
