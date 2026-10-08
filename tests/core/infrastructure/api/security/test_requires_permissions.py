import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.core.infrastructure.api.security.requires_permissions import requires_permissions
from src.core.infrastructure.config.settings import Settings

PERMISSION = "pokemons:list"


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected")
    @requires_permissions([PERMISSION])
    async def protected(request: Request) -> dict:
        return {"ok": True}

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_build_app())


def test_allows_when_caller_holds_the_required_permission(client, mock_cognito_auth):
    token = mock_cognito_auth.generate_token(custom_claims={"custom:action": f'["{PERMISSION}"]'})

    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_forbidden_without_authorization_header(client):
    response = client.get("/protected")

    assert response.status_code == 403
    assert response.json() == {"detail": f"Required permissions: {PERMISSION}"}


def test_forbidden_with_token_lacking_the_required_permission(client, mock_cognito_auth):
    token = mock_cognito_auth.generate_token(custom_claims={"custom:action": '["other:permission"]'})

    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_forbidden_with_a_malformed_custom_action_claim(client, mock_cognito_auth):
    # `custom:action` is expected to be a JSON array; a non-JSON value must not be treated as a
    # grant and must not raise - it degrades to "no permissions granted".
    token = mock_cognito_auth.generate_token(custom_claims={"custom:action": "not-json"})

    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_decoration_rejects_a_sync_endpoint():
    with pytest.raises(TypeError):

        @requires_permissions([PERMISSION])
        def sync_endpoint(request: Request) -> dict:
            return {"ok": True}


def test_raises_when_the_endpoint_has_no_request_parameter():
    @requires_permissions([PERMISSION])
    async def no_request_endpoint() -> dict:
        return {"ok": True}

    with pytest.raises(RuntimeError):
        asyncio.run(no_request_endpoint())


def test_verifies_the_token_against_cognito_jwks_when_configured(client, mock_cognito_auth):
    # When Cognito is configured, the decorator must verify the token (signature/issuer/audience)
    # rather than trust an unverified decode - this is the branch `local`/`test` deliberately skip.
    token = mock_cognito_auth.generate_token(custom_claims={"custom:action": f'["{PERMISSION}"]'})
    configured_settings = Settings(
        database_url="postgresql+psycopg2://example:example@localhost:5432/example_api",
        cognito_region="eu-west-1",
        cognito_user_pool_id="eu-west-1_example",
        cognito_client_id="example-client-id",
    )
    fake_signing_key = MagicMock(key="irrelevant-signing-key")

    with (
        patch(
            "src.core.infrastructure.api.security.requires_permissions.Settings",
            return_value=configured_settings,
        ),
        patch("src.core.infrastructure.api.security.requires_permissions.PyJWKClient") as jwks_client_cls,
        patch(
            "src.core.infrastructure.api.security.requires_permissions.jwt.decode",
            return_value={"custom:action": f'["{PERMISSION}"]'},
        ) as decode,
    ):
        jwks_client_cls.return_value.get_signing_key_from_jwt.return_value = fake_signing_key

        response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    decode.assert_called_once()
    assert decode.call_args.kwargs["audience"] == "example-client-id"
