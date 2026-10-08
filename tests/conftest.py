import subprocess
from collections.abc import Callable
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from summer.inversion_of_control.constants import DEFAULT
from summer.inversion_of_control.dependencies import services_dict

from src.app import create_app
from src.core.infrastructure.bootstrap import bootstrap
from src.core.infrastructure.database.sql import session_manager as session_manager_module
from src.core.infrastructure.database.sql.session_manager import (
    configure_session_factory,
    session_manager,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MOCK_JWT_SIGNING_KEY = "test-signing-key"


@pytest.fixture(scope="session", autouse=True)
def _bootstrap():
    # The `test` compose service points DATABASE_URL at TEST_DATABASE_URL for this process
    # (docker-compose.yml), so bootstrap() here wires the app against the test database, not
    # the dev one. The suite runs against real migrations rather than `Base.metadata.create_all`
    # so a broken migration fails the build.
    bootstrap()
    subprocess.run(["alembic", "upgrade", "head"], cwd=_REPO_ROOT, check=True)


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def clean_database():
    yield
    with session_manager() as session:
        table_names = (
            session.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version'")
            )
            .scalars()
            .all()
        )
        if table_names:
            quoted_tables = ", ".join(f'"{name}"' for name in table_names)
            session.execute(text(f"TRUNCATE {quoted_tables} RESTART IDENTITY CASCADE"))
            session.commit()


@pytest.fixture
def override_service(monkeypatch: pytest.MonkeyPatch) -> Callable[[type, Callable[[], object]], None]:
    # summer's `@autowired` overwrites every annotated constructor argument with
    # `services_dict[context][interface]()`, even one passed explicitly, so a fake handed to a
    # use case constructor is silently replaced by the real service. Tests that need a fake must
    # therefore swap the registry entry; `monkeypatch.setitem` restores the original afterwards.
    def _override(interface: type, factory: Callable[[], object]) -> None:
        monkeypatch.setitem(services_dict[DEFAULT], interface, factory)

    return _override


@pytest.fixture
def small_pool_engine():
    # Same database the suite already runs against, but with a pool so small that any leaked
    # connection exhausts it within a few calls. `pool_timeout` is short so a leak surfaces as a
    # fast failure instead of stalling the test for the default 30s.
    original_factory = session_manager_module._session_factory
    engine = create_engine(
        original_factory.kw["bind"].url,
        pool_size=2,
        max_overflow=0,
        pool_timeout=1,
    )
    configure_session_factory(sessionmaker(bind=engine, autocommit=False, autoflush=False))
    yield engine
    configure_session_factory(original_factory)
    engine.dispose()


class _MockCognitoAuth:
    @staticmethod
    def generate_token(custom_claims: dict | None = None) -> str:
        claims = {"sub": "test-user", **(custom_claims or {})}
        return jwt.encode(claims, _MOCK_JWT_SIGNING_KEY, algorithm="HS256")


@pytest.fixture
def mock_cognito_auth() -> _MockCognitoAuth:
    return _MockCognitoAuth()
