from __future__ import annotations

from sqlalchemy.orm import Session

from src.core.infrastructure.database.sql.session_manager import get_read_session


class IDatabaseRepositorySQL:
    """Mixed into every SQL repository alongside its domain interface (best_practices.md
    Pattern 8):

        class PokemonQueryServiceSQL(IPokemonQueryService, IDatabaseRepositorySQL):
            def get_by_id(self, pokemon_id): ...
                entity = self.db.query(PokemonModelSQL)...

    `self.db` resolves the session through `get_read_session()` rather than opening its own:
    inside an enclosing `@with_transaction`/`session_manager()` scope it is that scope's own
    session (one shared transaction, released by the scope); with no enclosing scope (e.g. a
    read-only query service called straight from a use case) it is an autocommit-mode session
    that returns its connection to the pool as soon as each statement's result is consumed, so
    repeated reads never leak connections. Anything that must run several statements on one
    connection (e.g. `SET LOCAL`) opens an explicit `with session_manager() as session:` block.
    """

    @property
    def db(self) -> Session:
        return get_read_session()
