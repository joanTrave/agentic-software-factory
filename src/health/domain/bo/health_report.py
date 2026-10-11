from pydantic import BaseModel

from src.health.domain.bo.dependency_check import DependencyCheck
from src.health.domain.enums.health_status_enum import DependencyStatusEnum, HealthStatusEnum


class HealthReport(BaseModel):
    """The module's only domain logic: a report is `UNHEALTHY` if any dependency check is
    `DOWN`, `HEALTHY` otherwise — including when there are no checks at all (an empty report
    documents the boundary deliberately rather than leaving it to accident)."""

    checks: list[DependencyCheck]

    @property
    def status(self) -> HealthStatusEnum:
        if any(check.status == DependencyStatusEnum.DOWN for check in self.checks):
            return HealthStatusEnum.UNHEALTHY
        return HealthStatusEnum.HEALTHY
