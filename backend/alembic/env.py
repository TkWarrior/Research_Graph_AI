"""
Alembic env.py — runtime environment for migrations.

Reads DATABASE_URL from the app settings (.env) so the migration
uses the same connection string as the running application.
Supports both offline (SQL script) and online (direct DB connection) modes.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ── Make the app importable ────────────────────────────────────────────
# Add the backend directory to sys.path so we can import app modules.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.database import Base

# Import ALL models so Alembic autogenerate can detect them.
# Order matters: Workspace must be imported before models that FK into it.
import app.models  # noqa: F401 — registers Workspace, Document, GraphSnapshot, ChatSession, ChatMessage

# ── Alembic config object ─────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url with the value from our .env
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The MetaData object Alembic uses for autogenerate
target_metadata = Base.metadata


# ── Offline mode ──────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Emits SQL to stdout/a file without a live DB connection.
    Usage: alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online mode ───────────────────────────────────────────────────────
def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode with a live DB connection.
    Usage: alembic upgrade head
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,        # detect column type changes
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
