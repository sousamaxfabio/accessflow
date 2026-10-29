import json
import logging
from datetime import datetime

from app.logging_config import JsonFormatter


def make_log_record() -> logging.LogRecord:
    return logging.LogRecord(
        name="accessflow",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Request completed",
        args=(),
        exc_info=None,
    )


def test_json_formatter_creates_structured_request_log():
    record = make_log_record()
    record.event = "http_request_completed"
    record.request_id = "request-123"
    record.method = "POST"
    record.path = "/access-requests"
    record.status_code = 202
    record.duration_ms = 12.34

    result = json.loads(JsonFormatter().format(record))

    assert result["level"] == "INFO"
    assert result["logger"] == "accessflow"
    assert result["message"] == "Request completed"
    assert result["event"] == "http_request_completed"
    assert result["request_id"] == "request-123"
    assert result["method"] == "POST"
    assert result["path"] == "/access-requests"
    assert result["status_code"] == 202
    assert result["duration_ms"] == 12.34
    assert datetime.fromisoformat(result["timestamp"]).tzinfo is not None


def test_json_formatter_omits_context_that_was_not_supplied():
    result = json.loads(JsonFormatter().format(make_log_record()))

    assert "request_id" not in result
    assert "status_code" not in result
    assert "duration_ms" not in result