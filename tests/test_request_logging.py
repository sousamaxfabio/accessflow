import json
import logging
from io import StringIO

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.logging_config import JsonFormatter
from app.request_logging import RequestLoggingMiddleware


def create_test_client(log_output: StringIO) -> TestClient:
    logger = logging.getLogger("accessflow.test.request_logging")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    handler = logging.StreamHandler(log_output)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    app = FastAPI()
    app.add_middleware(
        RequestLoggingMiddleware,
        logger=logger,
    )

    @app.get("/example")
    def example() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/failure")
    def failure() -> None:
        raise RuntimeError("Simulated failure")

    return TestClient(
        app,
        raise_server_exceptions=False,
    )


def test_middleware_adds_request_id_and_structured_log():
    log_output = StringIO()

    with create_test_client(log_output) as client:
        response = client.get("/example")

    log_entry = json.loads(log_output.getvalue())

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == log_entry["request_id"]
    assert log_entry["event"] == "http_request_completed"
    assert log_entry["method"] == "GET"
    assert log_entry["path"] == "/example"
    assert log_entry["status_code"] == 200
    assert log_entry["duration_ms"] >= 0


def test_middleware_preserves_incoming_request_id():
    log_output = StringIO()

    with create_test_client(log_output) as client:
        response = client.get(
            "/example",
            headers={"X-Request-ID": "upstream-request-456"},
        )

    log_entry = json.loads(log_output.getvalue())

    assert response.headers["X-Request-ID"] == "upstream-request-456"
    assert log_entry["request_id"] == "upstream-request-456"


def test_middleware_logs_unexpected_failure():
    log_output = StringIO()

    with create_test_client(log_output) as client:
        response = client.get("/failure")

    log_entry = json.loads(log_output.getvalue())

    assert response.status_code == 500
    assert log_entry["event"] == "http_request_failed"
    assert log_entry["path"] == "/failure"
    assert log_entry["status_code"] == 500
    assert "RuntimeError: Simulated failure" in log_entry["exception"]
