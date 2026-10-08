from __future__ import annotations

from pydantic import BaseModel

from src.health.domain.bo.dependency_check import DependencyCheck
from src.health.domain.bo.health_report import HealthReport
from src.health.domain.enums.health_status_enum import HealthStatusEnum


class DependencyCheckOutput(BaseModel):
    name: str
    status: str
    latency_ms: int
    error: str | None = None

    @staticmethod
    def from_bo(check: DependencyCheck) -> DependencyCheckOutput:
        return DependencyCheckOutput(
            name=check.name,
            status=check.status.value,
            latency_ms=check.latency_ms,
            error=check.error,
        )


class HealthOutput(BaseModel):
    status: str
    checks: list[DependencyCheckOutput]
    detail: str | None = None
    reason: str | None = None

    @staticmethod
    def from_bo(report: HealthReport) -> HealthOutput:
        is_healthy = report.status == HealthStatusEnum.HEALTHY
        return HealthOutput(
            status=report.status.value,
            checks=[DependencyCheckOutput.from_bo(check) for check in report.checks],
            detail=None if is_healthy else "One or more critical dependencies are unavailable.",
            reason=None if is_healthy else "healthCheckFailed",
        )
