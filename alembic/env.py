from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import src.core.infrastructure.database.sql.metadata  # noqa: F401 - registers every module's models
from src.core.infrastructure.config.settings import Settings
from src.core.infrastructure.database.sql.base import Base

# this is the Alembic Config object, which provides access to the values within the .ini file
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The DSN comes from `Settings`, never from `alembic.ini` - so a database password is never
# committed and `alembic.ini` stays environment-independent.
settings = Settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# `target_metadata` must see every module's `*ModelSQL` for autogenerate - importing
# `src.core.infrastructure.database.sql.metadata` above is what wires that in.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode: no live DB connection, just a URL -- emits the SQL
    to a script instead of executing it against a database."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode: acquire a connection and apply them directly."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
