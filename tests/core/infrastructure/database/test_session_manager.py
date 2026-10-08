import uuid

import pytest
from sqlalchemy import text

from src.core.infrastructure.database.sql import (
    session_manager as session_manager_module,
)
from src.core.infrastructure.database.sql.session_manager import (
    session_manager,
    with_transaction,
)


class _Boom(Exception):
    pass


@pytest.fixture
def scratch_table():
    table = f"test_session_manager_scratch_{uuid.uuid4().hex[:8]}"
    with session_manager() as session:
        session.execute(text(f"CREATE TABLE {table} (id SERIAL PRIMARY KEY, value TEXT)"))
        session.commit()
    yield table
    with session_manager() as session:
        session.execute(text(f"DROP TABLE IF EXISTS {table}"))
        session.commit()


def _row_count(table: str) -> int:
    with session_manager() as session:
        return session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def test_with_transaction_commits_on_success(scratch_table):
    @with_transaction
    def insert_row():
        with session_manager() as session:
            session.execute(text(f"INSERT INTO {scratch_table} (value) VALUES ('committed')"))

    insert_row()

    assert _row_count(scratch_table) == 1


def test_with_transaction_rolls_back_and_reraises_original_exception_on_failure(
    scratch_table,
):
    @with_transaction
    def insert_then_fail():
        with session_manager() as session:
            session.execute(text(f"INSERT INTO {scratch_table} (value) VALUES ('should_rollback')"))
        raise _Boom("boom")

    with pytest.raises(_Boom):
        insert_then_fail()

    assert _row_count(scratch_table) == 0


def test_nested_session_manager_reuses_the_outer_session():
    with session_manager() as outer, session_manager() as inner:
        assert inner is outer


def test_session_manager_raises_runtime_error_before_configuration(monkeypatch):
    monkeypatch.setattr(session_manager_module, "_session_factory", None)

    with pytest.raises(RuntimeError), session_manager_module.session_manager():
        pass
