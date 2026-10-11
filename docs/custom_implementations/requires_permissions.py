"""Reference implementation of the `@requires_permissions` decorator.

Backs best_practices.md Pattern 5 (Permission Guards on Endpoints): every router endpoint
declares the permissions it requires via this decorator. It reads the caller's granted
permissions from the decoded JWT's `custom:action` claim — a JSON-encoded list of permission
strings, e.g. `'["pokemons:list"]'`, matching the Cognito custom-attribute convention the
`mock_cognito_auth` test fixture in best_practices.md Pattern 11 generates tokens with — and
raises HTTP 403 if the caller holds none of them.
"""

import functools
import inspect
import json
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, Request


def _extract_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Request:
    for value in (*args, *kwargs.values()):
        if isinstance(value, Request):
            return value
    raise RuntimeError("@requires_permissions requires the endpoint to accept a `Request` parameter.")


def _decode_granted_permissions(request: Request) -> set[str]:
    """Best-effort extraction of the caller's granted permissions from the bearer token.

    This reference implementation only reads the unverified `custom:action` claim — token
    verification (signature, issuer, audience, expiry) is assumed to already have happened
    upstream, e.g. in an auth dependency/middleware that ran before this decorator. Do not
    treat this as the project's only authentication check.
    """
    import jwt  # PyJWT

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return set()

    token = auth_header.split(" ", 1)[1]
    claims = jwt.decode(token, options={"verify_signature": False})
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
    `{"detail": "Required permissions: <perm1>, <perm2>"}` otherwise — matching the response
    body asserted by the `test_*_forbidden_wrong_permission` tests in best_practices.md
    Pattern 11.
    """

    def decorator(endpoint: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        if not inspect.iscoroutinefunction(endpoint):
            raise TypeError("@requires_permissions only supports async endpoint handlers.")

        @functools.wraps(endpoint)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _extract_request(args, kwargs)
            granted = _decode_granted_permissions(request)
            if not granted.intersection(required):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required permissions: {', '.join(required)}",
                )
            return await endpoint(*args, **kwargs)

        return wrapper

    return decorator
