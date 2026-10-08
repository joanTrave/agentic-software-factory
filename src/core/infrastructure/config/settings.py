from __future__ import annotations

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEPLOYED_ENVIRONMENTS = {"staging", "production"}


class Settings(BaseSettings):
    """Single source for every environment variable (python skill: "keep configuration
    outside source code"). Nothing else in the project calls `os.getenv` directly.

    `DATABASE_URL` is the only variable with no default — a missing/invalid configuration
    fails loudly at startup (`ValidationError`) rather than letting the service boot
    half-configured.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # -- Database -----------------------------------------------------------------------
    database_url: str
    test_database_url: str | None = None
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True
    healthcheck_db_timeout_seconds: int = 2

    # -- Application ----------------------------------------------------------------------
    app_env: str = "local"
    log_level: str = "INFO"
    port: int = 8000

    # -- Gunicorn ---------------------------------------------------------------------------
    gunicorn_workers: int | None = None
    gunicorn_timeout: int = 60

    # -- Auth (Cognito) ---------------------------------------------------------------------
    cognito_region: str | None = None
    cognito_user_pool_id: str | None = None
    cognito_client_id: str | None = None

    @model_validator(mode="after")
    def _derive_test_database_url(self) -> Settings:
        """Default `test_database_url` to `database_url` with `_test` appended to the
        database name, unless the caller set `TEST_DATABASE_URL` explicitly."""
        if self.test_database_url is None:
            prefix, _, database_name = self.database_url.rpartition("/")
            self.test_database_url = f"{prefix}/{database_name}_test"
        return self

    @model_validator(mode="after")
    def _require_cognito_settings_in_deployed_environments(self) -> Settings:
        """`local`/`test` tolerate unset Cognito settings (the mock auth fixture signs its
        own tokens); `staging`/`production` must not silently run with authentication
        effectively disabled."""
        if self.app_env in _DEPLOYED_ENVIRONMENTS:
            missing = [
                name
                for name, value in (
                    ("COGNITO_REGION", self.cognito_region),
                    ("COGNITO_USER_POOL_ID", self.cognito_user_pool_id),
                    ("COGNITO_CLIENT_ID", self.cognito_client_id),
                )
                if value is None
            ]
            if missing:
                raise ValueError(
                    f"Missing required Cognito settings for app_env={self.app_env!r}: {', '.join(missing)}"
                )
        return self
