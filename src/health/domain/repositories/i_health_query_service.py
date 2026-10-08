from __future__ import annotations

from abc import ABC, abstractmethod

from src.health.domain.bo.dependency_check import DependencyCheck


class IHealthQueryService(ABC):
    @abstractmethod
    def check_database_connection(self) -> DependencyCheck:
        raise NotImplementedError
