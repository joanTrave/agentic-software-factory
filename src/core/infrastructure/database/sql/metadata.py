"""Single place `alembic/env.py` imports to make `Base.metadata` complete for autogenerate.

Every module's `infrastructure/database/models/*.py` must be imported here (directly or via its
module's `models` package) so a new table shows up in `alembic revision --autogenerate`. The
health module owns no tables, so it contributes nothing here yet — the next bounded context adds
its import to this file.
"""

from __future__ import annotations

from src.core.infrastructure.database.sql.base import Base

__all__ = ["Base"]
