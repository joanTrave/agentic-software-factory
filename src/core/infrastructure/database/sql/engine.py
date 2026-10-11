from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from src.core.infrastructure.config.settings import Settings


def build_engine(settings: Settings, database_url: str | None = None) -> Engine:
    """Build the SQLAlchemy 1.4 engine (`## Stack`: SQLAlchemy 1.4 + Alembic) used by both
    the application and, via `bootstrap()`, Alembic's `env.py`."""
    return create_engine(
        database_url or settings.database_url,
        pool_pre_ping=settings.db_pool_pre_ping,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        future=False,
    )


def build_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=False)
