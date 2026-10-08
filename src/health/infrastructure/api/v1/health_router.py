from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# Importing the concrete `HealthQueryServiceSQL` registers it with the DI container
# (`@service()` runs at import time) even along the path FastAPI's module import follows,
# independent of `discover_services()`'s own filesystem scan at bootstrap.
import src.health.infrastructure.database.health_query_service_sql  # noqa: F401
from src.health.application.check_health.check_health_use_case import CheckHealthUseCase
from src.health.application.check_health.serializers.health_output import HealthOutput
from src.health.domain.enums.health_status_enum import HealthStatusEnum

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthOutput,
    responses={503: {"model": HealthOutput}},
)
async def check_health(request: Request) -> JSONResponse:
    """The orchestrator's liveness **and** readiness probe. Deliberately **not** decorated
    with `@requires_permissions` and takes no auth dependency — the one documented exception
    to best_practices.md Pattern 5, because the endpoint must never depend on authentication,
    another service, or anything the service cannot verify on its own (`docs/constitution.md`
    `## Conventions`). `request` is accepted only for signature consistency with every other
    router in the project, not because this handler reads it.

    Returns a `JSONResponse` directly rather than raising a `CustomException`: the shared
    `custom_exception_handler` can only express 404/400, and a 503 means something different to
    a load balancer than either of those.
    """
    use_case = CheckHealthUseCase()
    report = use_case.execute()
    output = HealthOutput.from_bo(report)
    status_code = 200 if report.status == HealthStatusEnum.HEALTHY else 503
    return JSONResponse(status_code=status_code, content=output.model_dump(mode="json", exclude_none=True))


__all__ = ["router"]
