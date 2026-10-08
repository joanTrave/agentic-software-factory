import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.infrastructure.database.sql import (
    session_manager as session_manager_module,
)
from src.core.infrastructure.database.sql.session_manager import (
    configure_session_factory,
)
from src.health.domain.enums.health_status_enum import DependencyStatusEnum
from src.health.infrastructure.database.health_query_service_sql import (
    HealthQueryServiceSQL,
)

_UNREACHABLE_PASSWORD = "unreachable-secret-password"
_UNREACHABLE_HOST = "127.0.0.1"
_UNREACHABLE_DSN = f"postgresql+psycopg2://baduser:{_UNREACHABLE_PASSWORD}@{_UNREACHABLE_HOST}:1/baddb"


@pytest.fixture
def unreachable_database_factory():
    original_factory = session_manager_module._session_factory
    bad_engine = create_engine(_UNREACHABLE_DSN, pool_pre_ping=False)
    configure_session_factory(sessionmaker(bind=bad_engine))
    yield
    configure_session_factory(original_factory)
    bad_engine.dispose()


def test_check_database_connection_returns_up_with_non_negative_latency():
    service = HealthQueryServiceSQL()

    check = service.check_database_connection()

    assert check.name == "database"
    assert check.status == DependencyStatusEnum.UP
    assert check.latency_ms >= 0
    assert check.error is None


def test_check_database_connection_returns_down_without_raising_when_unreachable(
    unreachable_database_factory,
):
    service = HealthQueryServiceSQL()

    check = service.check_database_connection()

    assert check.name == "database"
    assert check.status == DependencyStatusEnum.DOWN
    assert check.error is not None


def test_check_database_connection_error_does_not_leak_connection_credentials(
    unreachable_database_factory,
):
    service = HealthQueryServiceSQL()

    check = service.check_database_connection()

    assert _UNREACHABLE_PASSWORD not in (check.error or "")
    assert _UNREACHABLE_HOST not in (check.error or "")
    assert "baduser" not in (check.error or "")


def test_check_database_connection_stays_up_when_called_more_times_than_the_pool_size(
    small_pool_engine,
):
    service = HealthQueryServiceSQL()
    call_count = small_pool_engine.pool.size() * 3

    statuses = [service.check_database_connection().status for _ in range(call_count)]

    assert statuses == [DependencyStatusEnum.UP] * call_count


def test_check_database_connection_returns_every_connection_to_the_pool(small_pool_engine):
    service = HealthQueryServiceSQL()

    for _ in range(small_pool_engine.pool.size() * 3):
        service.check_database_connection()

    assert small_pool_engine.pool.checkedout() == 0
