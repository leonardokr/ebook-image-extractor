"""Logging helpers."""

from datetime import datetime, timezone
import json
import logging


class JsonLogFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Render one record as JSON.

        :param record: Input log record.
        :return: JSON line.
        """
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)


def configure_json_logger(logger: logging.Logger) -> None:
    """Replace logger handlers with JSON formatter.

    :param logger: Logger instance.
    """
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)
