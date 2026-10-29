import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


CONTEXT_FIELDS = (
    "event",
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
)


class JsonFormatter(logging.Formatter):
    """Convert a Python log record into one JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field_name in CONTEXT_FIELDS:
            field_value = getattr(record, field_name, None)
            if field_value is not None:
                payload[field_name] = field_value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure and return the logger used by AccessFlow."""

    logger = logging.getLogger("accessflow")
    logger.setLevel(log_level.upper())
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)
    logger.propagate = False

    return logger