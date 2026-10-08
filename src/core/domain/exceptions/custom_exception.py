from __future__ import annotations


class CustomException(Exception):
    """Base class for all domain/application exceptions (best_practices.md Pattern 6).

    Subclasses set `self.message` (human-readable, safe to show to a client) and
    `self.reason` (a stable, machine-parsable code a client can switch on) before calling
    `super().__init__(message, reason)`. Kept free of any framework import — the FastAPI
    wiring that turns a raised `CustomException` into an HTTP response lives in
    `src/core/infrastructure/api/exception_handlers.py`, not here, so this module stays
    importable from pure domain code (best_practices.md Pattern 1).
    """

    def __init__(self, message: str, reason: str) -> None:
        self.message = message
        self.reason = reason
        super().__init__(message, reason)

    def __str__(self) -> str:
        return self.message


class CustomNotFoundException(CustomException):
    """Convenience base for "entity not found" exceptions.

    Subclasses just pass the entity name and id, e.g.:

        class PokemonNotFoundException(CustomNotFoundException):
            def __init__(self, pokemon_id: str) -> None:
                super().__init__("Pokemon", pokemon_id)
    """

    def __init__(self, entity_name: str, entity_id: str) -> None:
        message = f"{entity_name} with ID {entity_id} not found."
        reason = f"{entity_name[0].lower()}{entity_name[1:]}NotFound"
        super().__init__(message, reason)
