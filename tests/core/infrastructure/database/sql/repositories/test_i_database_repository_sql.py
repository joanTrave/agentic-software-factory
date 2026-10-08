from sqlalchemy import text

from src.core.infrastructure.database.sql.repositories.i_database_repository_sql import (
    IDatabaseRepositorySQL,
)
from src.core.infrastructure.database.sql.session_manager import (
    session_manager,
    with_transaction,
)


class _ReadOnlyRepository(IDatabaseRepositorySQL):
    def select_one(self) -> int:
        return self.db.execute(text("SELECT 1")).scalar()


def test_repeated_reads_outside_a_transaction_do_not_exhaust_the_connection_pool(small_pool_engine):
    repository = _ReadOnlyRepository()

    results = [repository.select_one() for _ in range(small_pool_engine.pool.size() * 3)]

    assert results == [1] * len(results)


def test_repeated_reads_outside_a_transaction_return_every_connection_to_the_pool(small_pool_engine):
    repository = _ReadOnlyRepository()

    for _ in range(small_pool_engine.pool.size() * 3):
        repository.select_one()

    assert small_pool_engine.pool.checkedout() == 0


def test_db_inside_a_transaction_is_the_transactions_own_session():
    repository = _ReadOnlyRepository()

    @with_transaction
    def read_session_identities():
        with session_manager() as transaction_session:
            return repository.db, transaction_session

    repository_session, transaction_session = read_session_identities()

    assert repository_session is transaction_session
