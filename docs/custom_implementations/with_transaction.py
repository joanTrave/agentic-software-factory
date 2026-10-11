"""Reference implementation of the `@with_transaction` decorator and its companion
`session_manager` context manager.

Backs best_practices.md Pattern 3 (Transaction Management): use cases that modify data wrap
their action method in `@with_transaction`, which commits on success and rolls back (then
re-raises) on any exception, instead of each use case managing its own session.
`session_manager()` is the same context manager best_practices.md Pattern 10's test factories
use directly (`with session_manager() as session: ...`) when a use case method isn't
involved.
"""

import functools
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

_session_factory: sessionmaker | None = None
_current_session: ContextVar[Session | None] = ContextVar("_current_session", default=None)


def configure_session_factory(factory: sessionmaker) -> None:
    """Call once at application startup with the project's configured `sessionmaker`."""
    global _session_factory
    _session_factory = factory


@contextmanager
def session_manager():
    """Yield the current session, opening one if none is already active.

    Reuses an already-open session from an enclosing `@with_transaction` call so nested calls
    share a single transaction, rather than silently opening a second one.
    """
    existing = _current_session.get()
    if existing is not None:
        yield existing
        return

    if _session_factory is None:
        raise RuntimeError("Call configure_session_factory() before using session_manager().")

    session = _session_factory()
    token = _current_session.set(session)
    try:
        yield session
    finally:
        _current_session.reset(token)
        session.close()


def get_read_session() -> Session:
    """Return the session a read-only repository should use, without owning its lifecycle.

    Inside an enclosing `@with_transaction`/`session_manager()` scope this is that scope's own
    session, so the read joins the caller's transaction and the scope releases the connection.
    Outside any scope it is a fresh *autocommit-mode* session (SQLAlchemy 1.4 legacy mode): it
    holds no connection between statements, checking one out only while a statement runs and
    returning it to the pool as soon as the result is consumed. Nothing therefore has to close
    it, which is what makes `IDatabaseRepositorySQL.db` safe to hand back from a property.
    Writes belong in a `@with_transaction` use case, not here.
    """
    existing = _current_session.get()
    if existing is not None:
        return existing

    if _session_factory is None:
        raise RuntimeError("Call configure_session_factory() before using get_read_session().")

    return _session_factory(autocommit=True)


def with_transaction(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for a use case's action method: run it inside one committed transaction.

    Commits on success. On any exception, rolls back and re-raises the original exception
    unchanged, so callers see the real failure rather than a transaction-management one.
    """

    @functools.wraps(method)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with session_manager() as session:
            try:
                result = method(*args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise

    return wrapper
