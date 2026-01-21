"""Initialize .browser-agent directory structure."""

from pathlib import Path
from browser_use_agent.storage.config import StorageConfig


def init_agent_directories():
    """Create the standard .browser-agent directory structure.

    Creates:
        .browser-agent/
        ├── checkpoints/           # SQLite checkpoints (if local)
        ├── memory/                # Agent memory files
        │   ├── AGENTS.md
        │   └── USER_PREFERENCES.md
        ├── skills/                # Auto-generated and custom skills
        ├── artifacts/             # Session artifacts
        │   ├── screenshots/
        │   ├── file_outputs/
        │   └── tool_outputs/
        └── traces/                # Cached LangSmith traces
    """
    agent_dir = StorageConfig.get_agent_dir()

    # Create subdirectories
    subdirs = [
        "checkpoints",
        "memory",
        "skills",
        "artifacts/screenshots",
        "artifacts/file_outputs",
        "artifacts/tool_outputs",
        "traces",
    ]

    for subdir in subdirs:
        (agent_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Create initial memory files if they don't exist
    agents_md = agent_dir / "memory" / "AGENTS.md"
    if not agents_md.exists():
        agents_md.write_text("""# Browser Agent Memory

Last updated: (auto-updated on reflection)

## Learned Best Practices

(Auto-populated from reflection on LangSmith traces and diary entries)

## Domain-Specific Patterns

(Auto-populated with site-specific behaviors)

## Common Failure Patterns

(Auto-populated from error analysis)

## Skill Prerequisites

(Auto-populated when skills require credentials or data)
""")

    user_prefs_md = agent_dir / "memory" / "USER_PREFERENCES.md"
    if not user_prefs_md.exists():
        user_prefs_md.write_text("""# User Preferences

Max tokens: 2000 (enforced by UserPreferencesManager)

## UI Preferences

(User's preferred browser settings, viewport size, etc.)

## Workflow Preferences

(Common workflows and patterns)
""")

    # Create .gitignore in agent directory
    gitignore = agent_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("""# Ignore sensitive and generated files
traces/
checkpoints/*.db
checkpoints/*.db-*

# Keep directory structure
!.gitkeep
""")

    print(f"[Storage] Initialized directory structure at {agent_dir}")
    return agent_dir


def get_or_create_user_agent_dir() -> Path:
    """Get or create user-level ~/.browser-agent directory.

    Creates:
        ~/.browser-agent/
        ├── memory/
        │   ├── AGENTS.md
        │   └── USER_PREFERENCES.md
        └── skills/
    """
    user_dir = Path.home() / ".browser-agent"
    user_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (user_dir / "memory").mkdir(exist_ok=True)
    (user_dir / "skills").mkdir(exist_ok=True)

    # Create initial files
    agents_md = user_dir / "memory" / "AGENTS.md"
    if not agents_md.exists():
        agents_md.write_text("# User-Level Agent Memory\n\n")

    user_prefs = user_dir / "memory" / "USER_PREFERENCES.md"
    if not user_prefs.exists():
        user_prefs.write_text("# Global User Preferences\n\n")

    return user_dir
