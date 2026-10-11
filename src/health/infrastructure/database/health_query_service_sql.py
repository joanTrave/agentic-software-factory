import logging
import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from summer.inversion_of_control.dependencies import service

from src.core.infrastructure.config.settings import Settings
from src.core.infrastructure.database.sql.repositories.i_database_repository_sql import (
    IDatabaseRepositorySQL,
)
from src.core.infrastructure.database.sql.session_manager import session_manager
from src.health.domain.bo.dependency_check import DependencyCheck
from src.health.domain.enums.health_status_enum import DependencyStatusEnum
from src.health.domain.repositories.i_health_query_service import IHealthQueryService

_DEPENDENCY_NAME = "database"
_logger = logging.getLogger(__name__)


@service()
class HealthQueryServiceSQL(IHealthQueryService, IDatabaseRepositorySQL):
    """Probes the database through the application's own session factory (`session_manager()`),
    so the check exercises the real connection path — pooling, credentials, `pool_pre_ping` —
    rather than a second, differently-configured connection that could report healthy while the
    app's own pool is exhausted.

    It opens an explicit `session_manager()` block instead of using `self.db`: the statement
    timeout and the probe query must run on the *same* connection, and the block guarantees that
    connection goes back to the pool afterwards (`SET LOCAL` is transaction-scoped, so the
    timeout cannot leak onto the pooled connection either). Deliberately **not** wrapped in
    `@with_transaction`: the check is read-only, and on a dead connection the decorator's
    `session.rollback()` would itself raise, masking the original failure. The statement timeout
    bounds how long a hung database can delay the probe, so a stalled dependency still produces a
    fast `503` rather than outliving the orchestrator's own probe timeout.
    """

    def check_database_connection(self) -> DependencyCheck:
        started_at = time.perf_counter()
        timeout_ms = Settings().healthcheck_db_timeout_seconds * 1000
        try:
            with session_manager() as session:
                session.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
                session.execute(text("SELECT 1")).scalar()
            return DependencyCheck(
                name=_DEPENDENCY_NAME,
                status=DependencyStatusEnum.UP,
                latency_ms=_elapsed_ms(started_at),
                error=None,
            )
        except (SQLAlchemyError, RuntimeError) as exc:
            # Only the exception *class name* goes into the returned DependencyCheck: a
            # SQLAlchemy `OperationalError` message embeds the DSN, including the password,
            # and this endpoint is unauthenticated. The full exception is logged here instead.
            _logger.error("Health check database connection failed", exc_info=exc)
            return DependencyCheck(
                name=_DEPENDENCY_NAME,
                status=DependencyStatusEnum.DOWN,
                latency_ms=_elapsed_ms(started_at),
                error=type(exc).__name__,
            )


def _elapsed_ms(started_at: float) -> int:
    return round((time.perf_counter() - started_at) * 1000)
