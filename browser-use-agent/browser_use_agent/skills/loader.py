"""Skill loader with progressive disclosure.

Progressive disclosure pattern:
1. list_skills() - Metadata only (name, description, tags)
2. load_skill() - Full skill markdown content
3. load_skill_supporting_files() - Supporting files (code, configs, etc.)

This minimizes context usage by only loading what's needed at each step.
"""

from pathlib import Path
from typing import List, Dict, Optional

from browser_use_agent.storage import StorageConfig


class SkillLoader:
    """Loads skills with progressive disclosure pattern.

    Skills are stored in .browser-agent/skills/ directory with two formats:
    - skill_name.md - Flat file with YAML frontmatter
    - skill_name/SKILL.md - Subdirectory with SKILL.md inside (deepagents convention)

    Both formats support optional supporting files in a skill_name/ directory.

    Example skill structures:
        .browser-agent/skills/
            linkedin-login.md           # Flat format
            linkedin-login/             # Supporting files
                example.py
                config.json
            agent-browser/              # Subdirectory format
                SKILL.md
                scripts/
                    helper.py
    """

    def __init__(self):
        """Initialize skill loader."""
        self.skills_dir = StorageConfig.get_agent_dir() / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def _find_skill_file(self, skill_name: str) -> Optional[Path]:
        """Find the skill file for a given skill name.

        Supports two patterns:
        - skill_name.md (flat file)
        - skill_name/SKILL.md (subdirectory with SKILL.md)

        Args:
            skill_name: Name of skill to find

        Returns:
            Path to skill file or None if not found
        """
        # Try flat file first
        flat_file = self.skills_dir / f"{skill_name}.md"
        if flat_file.exists():
            return flat_file

        # Try subdirectory with SKILL.md
        subdir_file = self.skills_dir / skill_name / "SKILL.md"
        if subdir_file.exists():
            return subdir_file

        return None

    def list_skills(self) -> List[Dict]:
        """List all available skills (metadata only).

        Returns:
            List of skill metadata dicts with keys:
            - name: Skill name
            - description: Brief description
            - tags: Comma-separated tags
            - file: Filename or path
        """
        skills = []
        seen_names = set()

        # Find flat files (*.md in skills dir)
        for skill_file in sorted(self.skills_dir.glob("*.md")):
            metadata = self._extract_metadata(skill_file)
            if metadata:
                seen_names.add(metadata["name"])
                skills.append(metadata)

        # Find subdirectory skills (skill_name/SKILL.md)
        for skill_dir in sorted(self.skills_dir.iterdir()):
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    metadata = self._extract_metadata(skill_file)
                    if metadata and metadata["name"] not in seen_names:
                        # Use directory name as canonical name if different
                        metadata["dir"] = skill_dir.name
                        skills.append(metadata)

        return skills

    def load_skill(self, skill_name: str) -> Optional[str]:
        """Load full skill content.

        Args:
            skill_name: Name of skill to load (without .md extension)

        Returns:
            Full skill markdown content or None if not found
        """
        skill_file = self._find_skill_file(skill_name)
        if not skill_file:
            return None

        return skill_file.read_text()

    def load_skill_supporting_files(self, skill_name: str) -> Dict[str, str]:
        """Load supporting files for a skill.

        Args:
            skill_name: Name of skill

        Returns:
            Dict mapping relative file path to content
        """
        skill_dir = self.skills_dir / skill_name
        if not skill_dir.exists() or not skill_dir.is_dir():
            return {}

        files = {}
        for file_path in skill_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(skill_dir)
                try:
                    files[str(rel_path)] = file_path.read_text()
                except Exception as e:
                    print(f"[Skills] Warning: Could not read {rel_path}: {e}")
                    continue

        return files

    def _extract_metadata(self, skill_file: Path) -> Optional[Dict]:
        """Extract YAML frontmatter metadata from skill file.

        Expected format:
            ---
            name: skill-name
            description: Brief description
            tags: tag1, tag2
            ---

            # Skill Content...

        Args:
            skill_file: Path to skill markdown file

        Returns:
            Metadata dict or None if no valid frontmatter
        """
        try:
            content = skill_file.read_text()
        except Exception as e:
            print(f"[Skills] Warning: Could not read {skill_file.name}: {e}")
            return None

        # Extract YAML frontmatter
        if not content.startswith("---"):
            # No frontmatter - create basic metadata
            return {
                "name": skill_file.stem,
                "description": "No description",
                "tags": "",
                "file": skill_file.name,
            }

        try:
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            frontmatter = parts[1]
            metadata = {}

            for line in frontmatter.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

            # Ensure required fields
            metadata.setdefault("name", skill_file.stem)
            metadata.setdefault("description", "No description")
            metadata.setdefault("tags", "")
            metadata["file"] = skill_file.name

            return metadata
        except (ValueError, Exception) as e:
            print(f"[Skills] Warning: Could not parse frontmatter in {skill_file.name}: {e}")
            return None

    def save_skill(
        self,
        skill_name: str,
        content: str,
        supporting_files: Optional[Dict[str, str]] = None
    ) -> Path:
        """Save a skill to disk.

        Args:
            skill_name: Name of skill (will be used for filename)
            content: Skill markdown content with YAML frontmatter
            supporting_files: Optional dict mapping filenames to content

        Returns:
            Path to saved skill file
        """
        skill_file = self.skills_dir / f"{skill_name}.md"
        skill_file.write_text(content)

        # Save supporting files if provided
        if supporting_files:
            skill_dir = self.skills_dir / skill_name
            skill_dir.mkdir(exist_ok=True)

            for filename, file_content in supporting_files.items():
                file_path = skill_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_content)

        print(f"[Skills] Saved skill: {skill_name}")
        return skill_file

    def delete_skill(self, skill_name: str) -> bool:
        """Delete a skill and its supporting files.

        Args:
            skill_name: Name of skill to delete

        Returns:
            True if deleted, False if not found
        """
        skill_file = self.skills_dir / f"{skill_name}.md"
        skill_dir = self.skills_dir / skill_name

        deleted = False

        if skill_file.exists():
            skill_file.unlink()
            deleted = True

        if skill_dir.exists() and skill_dir.is_dir():
            import shutil
            shutil.rmtree(skill_dir)
            deleted = True

        if deleted:
            print(f"[Skills] Deleted skill: {skill_name}")

        return deleted
