from fastapi import Request
from fastapi.responses import JSONResponse

from src.core.domain.exceptions.custom_exception import CustomException


async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
    """Register once at app startup so a raised `CustomException` turns into a structured
    JSON response instead of an unhandled 500:

        app.add_exception_handler(CustomException, custom_exception_handler)

    Maps a `reason` ending in `NotFound` to 404; anything else to 400. The health module's
    503 response is a deliberate exception to this handler (see
    `src/health/infrastructure/api/v1/health_router.py`) — this handler can only express 404
    or 400, so an unreachable critical dependency returns its response directly rather than
    raising.
    """
    status_code = 404 if exc.reason.endswith("NotFound") else 400
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "reason": exc.reason},
    )
