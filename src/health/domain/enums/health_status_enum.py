from __future__ import annotations

from src.core.domain.enum import CustomEnum


class HealthStatusEnum(CustomEnum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class DependencyStatusEnum(CustomEnum):
    UP = "up"
    DOWN = "down"
