import logging
import uvicorn
from pathlib import Path

from kcrud.domain.ports.logger import Logger, LogLevel
from kcrud.infrastructure.config import load_config
from infrastructure.api import create_api


_CONFIG_PATH = Path(__file__).parent / "config.yaml"


class _InterceptHandler(logging.Handler):
    def __init__(self, logger: Logger) -> None:
        super().__init__()
        self._logger = logger

    def emit(self, record: logging.LogRecord) -> None:
        level_map = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR,
            "CRITICAL": LogLevel.CRITICAL,
        }
        level = level_map.get(record.levelname, LogLevel.INFO)
        self._logger.log(level, record.getMessage())


def _setup_logging(logger: Logger) -> None:
    handler = _InterceptHandler(logger)
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.DEBUG)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "watchfiles"):
        log = logging.getLogger(name)
        log.handlers = [handler]
        log.propagate = False


_UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {},
    "loggers": {
        "uvicorn": {"handlers": [], "propagate": True},
        "uvicorn.access": {"handlers": [], "propagate": True},
        "uvicorn.error": {"handlers": [], "propagate": True},
    },
}

api, logger = create_api()
_setup_logging(logger)

if __name__ == "__main__":
    config = load_config(_CONFIG_PATH)
    uvicorn.run(
        "main_api:api",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
        log_config=_UVICORN_LOG_CONFIG,
    )
