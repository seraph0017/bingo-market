"""Alembic environment configuration."""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool, engine_from_config
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our Base model and settings
from app.core.database import Base
from app.core.config import settings

# Import all models to ensure they're registered with Base
from app.models import (
    User,
    UserWallet,
    RechargeOrder,
    WalletTransaction,
    Topic,
    TopicReview,
    CreatorProfile,
    MarketPosition,
    MarketSettlement,
    UserSettlement,
    SettlementDispute,
    Product,
    ProductCategory,
    ExchangeOrder,
    UserProduct,
    SensitiveWord,
    ContentReview,
    Violation,
    UserRiskLevel,
    UserAppeal,
    CreatorCreditLevel,
    AuditLog,
    LoginDevice,
    UserTerms,
    UserNotification,
    SettlementAnnouncement,
    Announcement,
    SystemConfig,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Get database URL from settings, convert asyncpg to psycopg2 for Alembic
def get_sync_database_url() -> str:
    """Convert async database URL to sync for Alembic."""
    url = settings.database_url
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://")
    return url

# Set the SQLAlchemy URL in the config
config.set_main_option("sqlalchemy.url", get_sync_database_url())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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


def do_run_migrations(connection):
    """Run migrations with a given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
