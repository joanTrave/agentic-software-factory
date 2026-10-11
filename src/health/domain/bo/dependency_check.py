from pydantic import BaseModel

from src.health.domain.enums.health_status_enum import DependencyStatusEnum


class DependencyCheck(BaseModel):
    name: str
    status: DependencyStatusEnum
    latency_ms: int
    error: str | None = None
