import logging
import os
from logging.handlers import RotatingFileHandler

from shimeji_nexus.core.paths import base_dir

LOG_PATH = os.path.join(base_dir(), "debug.log")

_configured = False


def get_logger(name):
    global _configured
    if not _configured:
        handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(name)s: %(message)s"))
        stream = logging.StreamHandler()
        stream.setFormatter(logging.Formatter("%(message)s"))
        logging.basicConfig(level=logging.WARNING, handlers=[handler, stream])
        _configured = True
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger
