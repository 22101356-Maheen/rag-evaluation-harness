from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from backend.app.core.config import settings
from backend.app.db.postgres import Base
from backend.app.models.project import Project
from backend.app.models.experiment_run import ExperimentRun

# -----------------------------
# Alembic Configuration
# -----------------------------

config = context.config

# This tells Alembic to use our DATABASE_URL
# instead of a hard-coded database connection.
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# -----------------------------
# Model Metadata
# -----------------------------

# This gives Alembic access to our SQLAlchemy models.
# It uses this metadata to detect table changes.
target_metadata = Base.metadata


# -----------------------------
# Offline Migration
# -----------------------------

def run_migrations_offline() -> None:
    """
    Run migrations without opening a live database connection.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# -----------------------------
# Online Migration
# -----------------------------

def run_migrations_online() -> None:
    """
    Connect to PostgreSQL and apply migrations.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# -----------------------------
# Migration Mode
# -----------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()