import json
import logging

from src.core.infrastructure.logging.logging_config import _JsonFormatter
from src.core.infrastructure.logging.request_context import set_request_id


def _record(message: str = "hello") -> logging.LogRecord:
    return logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0, msg=message, args=(), exc_info=None
    )


def test_json_formatter_includes_request_id_when_bound():
    set_request_id("rid-42")
    try:
        payload = json.loads(_JsonFormatter().format(_record()))
    finally:
        set_request_id(None)

    assert payload["request_id"] == "rid-42"
    assert payload["message"] == "hello"


def test_json_formatter_omits_request_id_outside_a_request():
    payload = json.loads(_JsonFormatter().format(_record()))

    assert "request_id" not in payload
