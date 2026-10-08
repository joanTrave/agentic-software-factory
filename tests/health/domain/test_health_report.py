from src.health.domain.bo.dependency_check import DependencyCheck
from src.health.domain.bo.health_report import HealthReport
from src.health.domain.enums.health_status_enum import (
    DependencyStatusEnum,
    HealthStatusEnum,
)


def _check(status: DependencyStatusEnum, name: str = "database") -> DependencyCheck:
    return DependencyCheck(name=name, status=status, latency_ms=1, error=None)


def test_health_report_is_healthy_when_all_checks_are_up():
    report = HealthReport(checks=[_check(DependencyStatusEnum.UP)])

    assert report.status == HealthStatusEnum.HEALTHY


def test_health_report_is_unhealthy_when_any_check_is_down():
    report = HealthReport(
        checks=[
            _check(DependencyStatusEnum.UP, name="cache"),
            _check(DependencyStatusEnum.DOWN, name="database"),
        ]
    )

    assert report.status == HealthStatusEnum.UNHEALTHY


def test_health_report_is_healthy_when_there_are_no_checks():
    report = HealthReport(checks=[])

    assert report.status == HealthStatusEnum.HEALTHY
