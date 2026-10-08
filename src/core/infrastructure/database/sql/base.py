from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(UTC)


class BaseModelPgSQL:
    """Mixin every `*ModelSQL` inherits alongside `Base` (best_practices.md Pattern 2):

        class PokemonModelSQL(BaseModelPgSQL, Base):
            __tablename__ = "pokemons"
            ...

    Provides the columns every table needs: a UUID primary key and created/updated
    timestamps, so individual models only declare their own domain columns.
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
