from __future__ import annotations

import re
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.core.infrastructure.logging.request_context import (
    REQUEST_ID_HEADER,
    get_request_id,
    set_request_id,
)

# An inbound id is echoed into logs and the response, so accept only a short, boring token.
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._\-]{1,128}$")


class RequestIdMiddleware:
    """Request-id propagation (plan §3 `logging_config.py`): reuses the inbound `X-Request-ID`
    (set by a load balancer / gateway) when it is well-formed, otherwise generates one, binds it
    to a contextvar so every log record emitted while serving the request carries it
    (`_JsonFormatter`), and echoes it on the response so a caller can correlate.

    Pure ASGI rather than `BaseHTTPMiddleware`, so the contextvar reliably reaches endpoints
    and cannot leak between requests.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        inbound = Headers(scope=scope).get(REQUEST_ID_HEADER)
        request_id = inbound if inbound and _VALID_REQUEST_ID.match(inbound) else uuid.uuid4().hex
        set_request_id(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = get_request_id() or request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            set_request_id(None)
