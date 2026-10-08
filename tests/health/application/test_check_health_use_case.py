from src.health.application.check_health.check_health_use_case import (
    CheckHealthUseCase,
)
from src.health.domain.bo.dependency_check import DependencyCheck
from src.health.domain.enums.health_status_enum import (
    DependencyStatusEnum,
    HealthStatusEnum,
)
from src.health.domain.repositories.i_health_query_service import (
    IHealthQueryService,
)


class _FakeUnhealthyQueryService(IHealthQueryService):
    def check_database_connection(self) -> DependencyCheck:
        return DependencyCheck(
            name="database",
            status=DependencyStatusEnum.DOWN,
            latency_ms=2012,
            error="OperationalError",
        )


_FAKE_LATENCY_MS = 987654


class _FakeHealthyQueryService(IHealthQueryService):
    def __init__(self):
        self.calls = 0

    def check_database_connection(self) -> DependencyCheck:
        self.calls += 1
        return DependencyCheck(name="database", status=DependencyStatusEnum.UP, latency_ms=_FAKE_LATENCY_MS, error=None)


def test_check_health_use_case_builds_healthy_report_from_fake_dependency(override_service):
    fake = _FakeHealthyQueryService()
    override_service(IHealthQueryService, lambda: fake)

    report = CheckHealthUseCase().execute()

    assert report.status == HealthStatusEnum.HEALTHY
    assert len(report.checks) == 1
    assert report.checks[0].name == "database"
    assert report.checks[0].status == DependencyStatusEnum.UP
    assert report.checks[0].latency_ms == _FAKE_LATENCY_MS
    assert fake.calls == 1


def test_check_health_use_case_builds_unhealthy_report_from_fake_dependency(override_service):
    override_service(IHealthQueryService, _FakeUnhealthyQueryService)

    report = CheckHealthUseCase().execute()

    assert report.status == HealthStatusEnum.UNHEALTHY
    assert report.checks[0].status == DependencyStatusEnum.DOWN
    assert report.checks[0].error == "OperationalError"


def test_override_service_restores_the_real_service_after_the_test():
    report = CheckHealthUseCase().execute()

    assert report.checks[0].latency_ms != _FAKE_LATENCY_MS
    assert report.checks[0].error is None
