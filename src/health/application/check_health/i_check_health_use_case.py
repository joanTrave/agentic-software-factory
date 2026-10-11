from abc import ABC, abstractmethod

from src.health.domain.bo.health_report import HealthReport


class ICheckHealthUseCase(ABC):
    @abstractmethod
    def execute(self) -> HealthReport:
        raise NotImplementedError
