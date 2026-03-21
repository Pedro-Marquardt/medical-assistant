import logging

from api.infra.config import ConfigEnvs

LOG_LEVEL = getattr(logging, ConfigEnvs.LOG_LEVEL, logging.INFO)
LOG_FORMAT = (
    "%(asctime)-15s.%(msecs)d %(levelname)-5s --- [%(threadName)15s]"
    " %(name)-15s : %(lineno)d : %(message)s"
)
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
BASE_LOGGER_NAME = "ai-api"


class _Logger:
    def __init__(self):
        self.override_basic_config()

    def override_basic_config(self):
        """Configure logging without duplicates."""
        logger = logging.getLogger(BASE_LOGGER_NAME)

        # Clear existing handlers before adding new ones
        if logger.hasHandlers():
            logger.handlers.clear()

        logger.setLevel(LOG_LEVEL)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(console_handler)

        logger.propagate = False

        self.silence_third_party_loggers()

    def silence_third_party_loggers(self):
        """Reduce noise from third-party libraries."""
        logging.getLogger("chromadb").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("uvicorn").setLevel(logging.WARNING)

        # Suprimir logs verbosos do WebRTC/ICE
        logging.getLogger("aioice.ice").setLevel(logging.WARNING)
        logging.getLogger("aioice").setLevel(logging.WARNING)
        logging.getLogger("aiortc").setLevel(logging.WARNING)
        logging.getLogger("aiortc.rtcpeerconnection").setLevel(logging.WARNING)
        logging.getLogger("aiortc.rtcdtlstransport").setLevel(logging.WARNING)
        logging.getLogger("aiortc.rtcicetransport").setLevel(logging.WARNING)

    def get_configured_logger(self, name: str) -> logging.Logger:
        """Retrieve a configured logger instance."""
        return logging.getLogger(f"{BASE_LOGGER_NAME}.{name}")


log = _Logger().get_configured_logger("INFO")
