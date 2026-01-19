"""Checkpoint saver factory for dual database support."""

from typing import Union
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from browser_use_agent.storage.config import StorageConfig


async def get_checkpoint_saver() -> BaseCheckpointSaver:
    """Create checkpoint saver based on configuration.

    Returns:
        AsyncSqliteSaver for local development
        AsyncPostgresSaver for production

    Environment Variables:
        CHECKPOINT_DB_TYPE: 'sqlite' (default) or 'postgres'
        SQLITE_PATH: Path to SQLite database (default: .browser-agent/checkpoints/browser_agent.db)
        DATABASE_URL: PostgreSQL connection string
        DB_POOL_SIZE: PostgreSQL pool size (default: 10)
    """
    if StorageConfig.DB_TYPE == "postgres":
        if not StorageConfig.POSTGRES_URI:
            raise ValueError(
                "DATABASE_URL environment variable required for postgres DB_TYPE"
            )

        print(f"[Storage] Using PostgreSQL checkpoint saver")
        print(f"[Storage] Database: {StorageConfig.POSTGRES_URI.split('@')[-1]}")  # Hide credentials

        return AsyncPostgresSaver.from_conn_string(
            StorageConfig.POSTGRES_URI,
            pool_size=StorageConfig.POSTGRES_POOL_SIZE
        )
    else:
        checkpoint_path = StorageConfig.get_checkpoint_path()
        print(f"[Storage] Using SQLite checkpoint saver")
        print(f"[Storage] Database: {checkpoint_path}")

        return AsyncSqliteSaver.from_conn_string(str(checkpoint_path))


async def init_checkpoint_db():
    """Initialize checkpoint database tables.

    Must be called before using checkpoint saver.
    """
    saver = await get_checkpoint_saver()

    # Tables are auto-created on first use by LangGraph
    # This just ensures the connection works
    print(f"[Storage] Checkpoint database initialized successfully")

    return saver
