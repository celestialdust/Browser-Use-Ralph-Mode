"""Session diary for recording agent experiences."""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from browser_use_agent.storage import StorageConfig


class SessionDiary:
    """Records session experiences for later reflection.

    The diary system stores structured markdown entries containing:
    - Accomplishments: What was achieved in the session
    - Challenges: Difficulties or obstacles encountered
    - Design decisions: Why certain approaches were chosen
    - User feedback: Direct feedback from the user
    - Tags: Automatically extracted for categorization

    Entries are stored in .browser-agent/memory/diary/ and can be
    marked as processed to avoid re-analysis by the reflection engine.
    """

    def __init__(self):
        """Initialize session diary."""
        self.diary_dir = StorageConfig.get_agent_dir() / "memory" / "diary"
        self.diary_dir.mkdir(parents=True, exist_ok=True)
        self.processed_log = self.diary_dir / "processed.log"

    async def create_entry(
        self,
        session_id: str,
        accomplishments: List[str],
        challenges: List[str],
        design_decisions: Dict[str, str],
        user_feedback: Optional[str] = None
    ) -> Path:
        """Create a diary entry from session experience.

        Called automatically on session end or via explicit command.

        Args:
            session_id: Unique session identifier
            accomplishments: List of what was accomplished
            challenges: List of challenges encountered
            design_decisions: Dict of design decisions and rationale
            user_feedback: Optional user feedback

        Returns:
            Path to created diary entry file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        entry_file = self.diary_dir / f"{session_id}_{timestamp}.md"

        content = f"""# Session Diary Entry

**Session ID**: {session_id}
**Date**: {datetime.now().isoformat()}

## Accomplishments
{self._format_list(accomplishments)}

## Challenges Encountered
{self._format_list(challenges)}

## Design Decisions
{self._format_dict(design_decisions)}

## User Feedback
{user_feedback or "None provided"}

## Tags
{self._extract_tags(accomplishments, challenges)}
"""

        entry_file.write_text(content)
        print(f"[Diary] Created entry: {entry_file}")
        return entry_file

    def get_unprocessed_entries(self) -> List[Path]:
        """Get diary entries that haven't been reflected upon.

        Returns:
            List of unprocessed diary entry paths
        """
        processed = set()
        if self.processed_log.exists():
            processed = set(self.processed_log.read_text().splitlines())

        all_entries = list(self.diary_dir.glob("*.md"))
        return [e for e in all_entries if str(e) not in processed]

    def mark_processed(self, entry_path: Path):
        """Mark entry as processed to avoid re-analysis.

        Args:
            entry_path: Path to diary entry
        """
        with self.processed_log.open("a") as f:
            f.write(f"{entry_path}\n")
        print(f"[Diary] Marked as processed: {entry_path.name}")

    def _format_list(self, items: List[str]) -> str:
        """Format list as markdown."""
        if not items:
            return "- (None)\n"
        return "\n".join([f"- {item}" for item in items])

    def _format_dict(self, items: Dict[str, str]) -> str:
        """Format dict as markdown."""
        if not items:
            return "- (None)\n"
        return "\n".join([f"- **{k}**: {v}" for k, v in items.items()])

    def _extract_tags(self, accomplishments: List[str], challenges: List[str]) -> str:
        """Extract tags from accomplishments and challenges.

        Automatically categorizes entries by:
        - Domain (google, linkedin, github, etc.)
        - Task type (authentication, form-filling, search, data-extraction)

        Args:
            accomplishments: List of accomplishments
            challenges: List of challenges

        Returns:
            Comma-separated tag string
        """
        tags = set()

        # Extract domain from accomplishments/challenges
        all_text = " ".join(accomplishments + challenges).lower()

        # Common domains
        domains = ["google", "linkedin", "github", "amazon", "facebook"]
        for domain in domains:
            if domain in all_text:
                tags.add(domain)

        # Common task types
        if any(word in all_text for word in ["login", "auth", "signin"]):
            tags.add("authentication")
        if any(word in all_text for word in ["form", "fill", "submit"]):
            tags.add("form-filling")
        if any(word in all_text for word in ["search", "query"]):
            tags.add("search")
        if any(word in all_text for word in ["scrape", "extract", "data"]):
            tags.add("data-extraction")

        return ", ".join(sorted(tags)) if tags else "general"
