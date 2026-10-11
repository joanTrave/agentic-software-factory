"""Application bootstrap (`.claude/skills/dependency-injection/SKILL.md` "Application
bootstrap"): wires settings, logging, DI service discovery and the database session factory,
in that exact order, exactly once before any `@autowired` constructor or request is served.

Called by `src/app.py` (module import time, so `src.app:app` is ready for gunicorn) and by
`tests/conftest.py`'s session-scoped `_bootstrap` fixture — the test suite runs through the same
bootstrap path production does, rather than a parallel test-only setup.
"""

from summer.inversion_of_control.service_locator import (
    discover_services,
    get_executable_parent_path,
)

import src
from src.core.infrastructure.config.settings import Settings
from src.core.infrastructure.database.sql.engine import build_engine, build_session_factory
from src.core.infrastructure.database.sql.session_manager import configure_session_factory
from src.core.infrastructure.logging.logging_config import configure_logging

_bootstrapped = False


def bootstrap() -> Settings:
    """Idempotent: a second call (e.g. a test module re-importing `src.app`) is a no-op."""
    global _bootstrapped
    settings = Settings()
    if _bootstrapped:
        return settings

    configure_logging(settings.log_level)
    discover_services(get_executable_parent_path(src.__file__))

    engine = build_engine(settings)
    configure_session_factory(build_session_factory(engine))

    _bootstrapped = True
    return settings
