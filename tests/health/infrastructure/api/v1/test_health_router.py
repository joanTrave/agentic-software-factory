import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.infrastructure.database.sql import (
    session_manager as session_manager_module,
)
from src.core.infrastructure.database.sql.session_manager import (
    configure_session_factory,
)

ENDPOINT = "/api/example-api/v1/health"

_UNREACHABLE_PASSWORD = "unreachable-secret-password"
_UNREACHABLE_HOST = "127.0.0.1"
_UNREACHABLE_DSN = f"postgresql+psycopg2://baduser:{_UNREACHABLE_PASSWORD}@{_UNREACHABLE_HOST}:1/baddb"


@pytest.fixture
def unreachable_database():
    original_factory = session_manager_module._session_factory
    bad_engine = create_engine(_UNREACHABLE_DSN, pool_pre_ping=False)
    configure_session_factory(sessionmaker(bind=bad_engine))
    yield
    configure_session_factory(original_factory)
    bad_engine.dispose()


def _resolve_schema_properties(schema: dict, document: dict) -> set:
    if "$ref" in schema:
        node = document
        for part in schema["$ref"].removeprefix("#/").split("/"):
            node = node[part]
        return _resolve_schema_properties(node, document)
    if "allOf" in schema:
        properties: set = set()
        for sub_schema in schema["allOf"]:
            properties |= _resolve_schema_properties(sub_schema, document)
        return properties
    return set(schema.get("properties", {}).keys())


def test_health_returns_200_when_database_is_reachable(api_client: TestClient):
    response = api_client.get(ENDPOINT)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    database_check = next(check for check in body["checks"] if check["name"] == "database")
    assert database_check["status"] == "up"


def test_health_returns_503_when_database_is_unreachable(api_client: TestClient, unreachable_database):
    response = api_client.get(ENDPOINT)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
    assert body["reason"] == "healthCheckFailed"
    database_check = next(check for check in body["checks"] if check["name"] == "database")
    assert database_check["status"] == "down"


def test_health_requires_no_authentication(api_client: TestClient):
    response = api_client.get(ENDPOINT)

    assert response.status_code != 401
    assert response.status_code != 403
    assert response.status_code == 200


def test_health_does_not_leak_connection_details(api_client: TestClient, unreachable_database):
    response = api_client.get(ENDPOINT)

    assert _UNREACHABLE_PASSWORD not in response.text
    assert _UNREACHABLE_HOST not in response.text
    assert "baduser" not in response.text


def test_health_response_matches_openapi_schema(api_client: TestClient, unreachable_database):
    response = api_client.get(ENDPOINT)
    assert response.status_code == 503

    openapi_schema = api_client.get("/openapi.json").json()
    health_responses = openapi_schema["paths"][ENDPOINT]["get"]["responses"]
    assert "503" in health_responses

    schema = health_responses["503"]["content"]["application/json"]["schema"]
    declared_properties = _resolve_schema_properties(schema, openapi_schema)

    body = response.json()
    assert set(body.keys()).issubset(declared_properties)
