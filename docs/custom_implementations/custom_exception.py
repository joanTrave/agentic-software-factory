"""Reference implementation of `CustomException`.

Backs best_practices.md Pattern 6 (Domain Exception Pattern): every domain/application
exception in this project inherits from `CustomException` instead of Python's built-in
`Exception`, and sets both `self.message` (human-readable, safe to show to a client) and
`self.reason` (a stable, machine-parsable code a client can switch on, e.g.
`"pokemonNotFound"`).
"""

from __future__ import annotations


class CustomException(Exception):
    """Base class for all domain/application exceptions.

    Subclasses set `self.message` and `self.reason` before calling
    `super().__init__(self.message, self.reason)` — see best_practices.md Pattern 6 for the
    canonical example (`PokemonNotFoundException`).
    """

    def __init__(self, message: str, reason: str) -> None:
        self.message = message
        self.reason = reason
        super().__init__(message, reason)

    def __str__(self) -> str:
        return self.message


class CustomNotFoundException(CustomException):
    """Convenience base for "entity not found" exceptions.

    Mirrors `PokemonNotFoundException` from best_practices.md Pattern 6 without repeating its
    boilerplate in every module — subclasses just pass the entity name and id:

        class PokemonNotFoundException(CustomNotFoundException):
            def __init__(self, pokemon_id: str) -> None:
                super().__init__("Pokemon", pokemon_id)
    """

    def __init__(self, entity_name: str, entity_id: str) -> None:
        message = f"{entity_name} with ID {entity_id} not found."
        reason = f"{entity_name[0].lower()}{entity_name[1:]}NotFound"
        super().__init__(message, reason)


# --- FastAPI wiring -----------------------------------------------------------------------
# Register once at app startup so any `CustomException` raised during a request turns into a
# structured JSON response instead of an unhandled 500:
#
#     app.add_exception_handler(CustomException, custom_exception_handler)

try:
    from fastapi import Request
    from fastapi.responses import JSONResponse

    async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
        status_code = 404 if exc.reason.endswith("NotFound") else 400
        return JSONResponse(
            status_code=status_code,
            content={"detail": exc.message, "reason": exc.reason},
        )
except ImportError:
    # fastapi is only needed for the exception handler, not for CustomException itself —
    # domain code that raises CustomException subclasses must not depend on a web framework
    # (best_practices.md Pattern 1).
    pass
