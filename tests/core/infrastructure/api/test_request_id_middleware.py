import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.infrastructure.api.request_id_middleware import RequestIdMiddleware
from src.core.infrastructure.logging.request_context import get_request_id

_PATH = "/probe"


def _build_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get(_PATH)
    def probe() -> dict:
        return {"request_id": get_request_id()}

    return TestClient(app)


def test_middleware_generates_a_request_id_and_echoes_it_on_the_response():
    response = _build_client().get(_PATH)

    request_id = response.json()["request_id"]
    assert request_id
    assert response.headers["x-request-id"] == request_id


def test_middleware_reuses_a_well_formed_inbound_request_id():
    response = _build_client().get(_PATH, headers={"x-request-id": "abc-123"})

    assert response.json()["request_id"] == "abc-123"
    assert response.headers["x-request-id"] == "abc-123"


def test_middleware_replaces_a_malformed_inbound_request_id():
    response = _build_client().get(_PATH, headers={"x-request-id": "bad id with spaces"})

    assert response.json()["request_id"] != "bad id with spaces"


def test_middleware_clears_the_request_id_after_the_request():
    _build_client().get(_PATH)

    assert get_request_id() is None


def test_each_request_gets_its_own_request_id():
    client = _build_client()

    first = client.get(_PATH).json()["request_id"]
    second = client.get(_PATH).json()["request_id"]

    assert first != second


def test_log_records_emitted_during_a_request_carry_the_request_id(caplog):
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    logger = logging.getLogger("request-id-test")

    @app.get(_PATH)
    def probe() -> dict:
        logger.warning("inside request")
        return {}

    with caplog.at_level(logging.WARNING, logger="request-id-test"):
        response = TestClient(app).get(_PATH, headers={"x-request-id": "rid-1"})

    assert response.headers["x-request-id"] == "rid-1"
    assert [record.message for record in caplog.records] == ["inside request"]
