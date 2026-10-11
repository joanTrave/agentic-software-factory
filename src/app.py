"""The `src.app:app` gunicorn target (`gunicorn.conf.py`, `entrypoint.sh`).

Contains no business logic, no route definitions, no SQL — only app assembly: bootstrap, the
FastAPI instance, exception-handler registration, and an explicit router include list (not
filesystem autodiscovery, so an accidentally-unmounted router is a review-visible diff —
`.claude/skills/architecture/SKILL.md` "prefer explicit dependencies over service locators and
hidden globals").
"""

from fastapi import FastAPI

from src.core.domain.exceptions.custom_exception import CustomException
from src.core.infrastructure.api.exception_handlers import custom_exception_handler
from src.core.infrastructure.api.request_id_middleware import RequestIdMiddleware
from src.core.infrastructure.bootstrap import bootstrap
from src.health.infrastructure.api.v1.health_router import router as health_router

_API_V1_PREFIX = "/api/example-api/v1"


def create_app() -> FastAPI:
    settings = bootstrap()

    app = FastAPI(
        title="example-api",
        docs_url=None if settings.app_env == "production" else "/docs",
        openapi_url=None if settings.app_env == "production" else "/openapi.json",
    )
    app.add_exception_handler(CustomException, custom_exception_handler)
    app.add_middleware(RequestIdMiddleware)

    # Health first, before any auth-bearing router: `docs/constitution.md` requires it to
    # never depend on another router/middleware being correctly configured.
    app.include_router(health_router, prefix=_API_V1_PREFIX)
    # Future bounded contexts: app.include_router(<module>_router, prefix=_API_V1_PREFIX)

    return app


app = create_app()
