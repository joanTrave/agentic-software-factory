from __future__ import annotations

from contextvars import ContextVar

REQUEST_ID_HEADER = "x-request-id"

_request_id: ContextVar[str | None] = ContextVar("_request_id", default=None)


def get_request_id() -> str | None:
    """The id of the request currently being served, or `None` outside a request."""
    return _request_id.get()


def set_request_id(request_id: str | None) -> None:
    _request_id.set(request_id)
