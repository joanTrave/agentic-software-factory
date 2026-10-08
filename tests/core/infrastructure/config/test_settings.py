import pytest
from pydantic import ValidationError

from src.core.infrastructure.config.settings import Settings


def _clear_cognito_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("COGNITO_REGION", "COGNITO_USER_POOL_ID", "COGNITO_CLIENT_ID"):
        monkeypatch.delenv(var, raising=False)


def test_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_loads_with_only_database_url_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://example:example@db:5432/example_api")
    monkeypatch.delenv("APP_ENV", raising=False)
    _clear_cognito_env(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+psycopg2://example:example@db:5432/example_api"
    assert settings.app_env == "local"
    assert settings.log_level == "INFO"
    assert settings.port == 8000


def test_settings_derives_test_database_url_by_appending_test_to_database_name(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://example:example@db:5432/example_api")
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    _clear_cognito_env(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.test_database_url == ("postgresql+psycopg2://example:example@db:5432/example_api_test")


def test_settings_honors_explicit_test_database_url_override(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://example:example@db:5432/example_api")
    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://example:example@db:5432/explicit_test_db",
    )
    _clear_cognito_env(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.test_database_url == ("postgresql+psycopg2://example:example@db:5432/explicit_test_db")


def test_settings_does_not_require_cognito_vars_in_local_env(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://example:example@db:5432/example_api")
    monkeypatch.setenv("APP_ENV", "local")
    _clear_cognito_env(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.app_env == "local"


def test_settings_requires_cognito_vars_in_production_env(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://example:example@db:5432/example_api")
    monkeypatch.setenv("APP_ENV", "production")
    _clear_cognito_env(monkeypatch)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_accepts_cognito_vars_in_production_env(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://example:example@db:5432/example_api")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("COGNITO_REGION", "eu-west-1")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", "pool-id")
    monkeypatch.setenv("COGNITO_CLIENT_ID", "client-id")

    settings = Settings(_env_file=None)

    assert settings.app_env == "production"
    assert settings.cognito_region == "eu-west-1"
