"""Storage configuration for browser agent."""

import os
from pathlib import Path
from typing import Optional


class StorageConfig:
    """Configuration for storage backends."""

    # Database type: 'sqlite' or 'postgres'
    DB_TYPE: str = os.getenv("CHECKPOINT_DB_TYPE", "sqlite")

    # SQLite configuration
    SQLITE_PATH: str = os.getenv(
        "SQLITE_PATH",
        ".browser-agent/checkpoints/browser_agent.db"
    )

    # PostgreSQL configuration
    POSTGRES_URI: str = os.getenv("DATABASE_URL", "")
    POSTGRES_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))

    # Supabase-specific (optional alternative to raw PostgreSQL)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Filesystem paths
    PROJECT_ROOT: Optional[Path] = None  # Auto-detected git root
    AGENT_DIR: str = ".browser-agent"

    @classmethod
    def get_agent_dir(cls) -> Path:
        """Get the .browser-agent directory path.

        Returns path relative to git root if detected, otherwise cwd.
        """
        if cls.PROJECT_ROOT is None:
            cls.PROJECT_ROOT = cls._detect_git_root()

        agent_dir = cls.PROJECT_ROOT / cls.AGENT_DIR
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

    @classmethod
    def _detect_git_root(cls) -> Path:
        """Detect git repository root, fallback to cwd."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            return Path.cwd()

    @classmethod
    def get_checkpoint_path(cls) -> Path:
        """Get full path to SQLite checkpoint file."""
        if cls.DB_TYPE != "sqlite":
            raise ValueError("get_checkpoint_path only valid for sqlite DB_TYPE")

        checkpoint_path = cls.get_agent_dir() / "checkpoints" / "browser_agent.db"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        return checkpoint_path
