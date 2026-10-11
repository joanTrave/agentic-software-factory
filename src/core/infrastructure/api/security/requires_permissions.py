"""`@requires_permissions` — wired from `docs/custom_implementations/requires_permissions.py`
(best_practices.md Pattern 5: Permission Guards on Endpoints).

Every router endpoint (except the unauthenticated health check — see `src/health/`, CF5 in
`.claude/tasks/constitution/plan/plan.md`) declares the permissions it requires via this
decorator, which reads the caller's granted permissions from the decoded JWT's `custom:action`
claim and raises HTTP 403 if the caller holds none of them.

Unlike the reference implementation, the token is verified (not just decoded) before its claims
are trusted: against Cognito's JWKS when Cognito is configured, which is enforced for
`staging`/`production` by `Settings` (see `src/core/infrastructure/config/settings.py`). In
`local`/`test`, where Cognito is deliberately unconfigured, the token is decoded without
signature verification so the `mock_cognito_auth` test fixture's locally-signed tokens keep
working — this project has no other identity provider to verify against in those environments.
"""

import functools
import inspect
import json
from collections.abc import Awaitable, Callable
from typing import Any

import jwt
from fastapi import HTTPException, Request
from jwt import PyJWKClient

from src.core.infrastructure.config.settings import Settings


def _extract_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Request:
    for value in (*args, *kwargs.values()):
        if isinstance(value, Request):
            return value
    raise RuntimeError("@requires_permissions requires the endpoint to accept a `Request` parameter.")


def _decode_claims(token: str, settings: Settings) -> dict[str, Any]:
    if not (settings.cognito_region and settings.cognito_user_pool_id and settings.cognito_client_id):
        # local/test: no Cognito configured — Settings already enforces this is never the
        # case in staging/production, so this branch cannot hide a real misconfiguration.
        return jwt.decode(token, options={"verify_signature": False})

    issuer = f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}"
    jwks_client = PyJWKClient(f"{issuer}/.well-known/jwks.json")
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=issuer,
        audience=settings.cognito_client_id,
    )


def _decode_granted_permissions(request: Request, settings: Settings) -> set[str]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return set()

    token = auth_header.split(" ", 1)[1]
    claims = _decode_claims(token, settings)
    raw = claims.get("custom:action", "[]")
    try:
        return set(json.loads(raw))
    except (TypeError, json.JSONDecodeError):
        return set()


def requires_permissions(
    required: list[str],
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Decorator factory: `@requires_permissions(["pokemons:list"])`.

    Grants access if the caller holds *any* of the listed permissions. Raises 403 with
    `{"detail": "Required permissions: <perm1>, <perm2>"}` otherwise.
    """

    def decorator(endpoint: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        if not inspect.iscoroutinefunction(endpoint):
            raise TypeError("@requires_permissions only supports async endpoint handlers.")

        @functools.wraps(endpoint)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _extract_request(args, kwargs)
            granted = _decode_granted_permissions(request, Settings())
            if not granted.intersection(required):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required permissions: {', '.join(required)}",
                )
            return await endpoint(*args, **kwargs)

        return wrapper

    return decorator
