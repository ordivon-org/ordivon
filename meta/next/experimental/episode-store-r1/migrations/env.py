from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, event, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _database_url() -> str:
    explicit = os.environ.get("ORDIVON_EXPERIMENTAL_SQLALCHEMY_URL")
    if explicit:
        return explicit
    dsn = os.environ.get("ORDIVON_EXPERIMENTAL_DSN")
    if not dsn:
        raise RuntimeError(
            "set ORDIVON_EXPERIMENTAL_DSN or ORDIVON_EXPERIMENTAL_SQLALCHEMY_URL"
        )
    if dsn.startswith("postgresql://"):
        return "postgresql+psycopg://" + dsn.removeprefix("postgresql://")
    return dsn


def _role() -> str | None:
    value = os.environ.get("ORDIVON_EXPERIMENTAL_DB_ROLE")
    if value is None:
        return None
    if not value.replace("_", "").isalnum():
        raise RuntimeError("ORDIVON_EXPERIMENTAL_DB_ROLE must be a simple identifier")
    return value


def run_migrations_offline() -> None:
    context.configure(url=_database_url(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url(), poolclass=pool.NullPool)
    role = _role()
    if role is not None:

        @event.listens_for(engine, "connect")
        def _set_role(dbapi_connection: object, _: object) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            try:
                cursor.execute(f'SET ROLE "{role}"')
            finally:
                cursor.close()

    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
