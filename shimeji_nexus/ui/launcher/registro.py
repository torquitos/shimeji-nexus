from shimeji_nexus.core.logging_setup import get_logger

_logger = get_logger("launcher")


def debug_log(msg):
    _logger.debug(msg)
