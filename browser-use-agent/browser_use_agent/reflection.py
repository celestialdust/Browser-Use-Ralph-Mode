"""Reflection tools for session analysis and skill creation."""

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
from browser_use_agent.storage.config import StorageConfig


class SkillOpportunity(BaseModel):
    """Identified opportunity for skill extraction."""
    name: str = Field(description="Proposed skill name")
    description: str = Field(description="What the skill does")
    steps: List[str] = Field(description="Key steps in the workflow")


class ReflectionOutput(BaseModel):
    """Output from session reflection."""
    accomplishments: List[str] = Field(description="What was accomplished")
    challenges: List[str] = Field(description="Obstacles encountered")
    learnings: List[str] = Field(description="Key learnings")
    skill_opportunities: List[SkillOpportunity] = Field(
        default_factory=list,
        description="Potential skills to extract"
    )
    rules_to_add: List[str] = Field(
        default_factory=list,
        description="Rules to add to AGENTS.md"
    )


def _extract_section(content: str, section_name: str) -> List[str]:
    """Extract bullet points from a markdown section.

    Args:
        content: Markdown content to parse
        section_name: Name of section to extract (case-insensitive)

    Returns:
        List of bullet point items from that section
    """
    items = []
    in_section = False

    for line in content.split("\n"):
        lower_line = line.lower()
        if section_name.lower() in lower_line and "#" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("#"):
                break
            if line.strip().startswith("-"):
                items.append(line.strip()[1:].strip())

    return items


@tool
def reflect_on_session(thread_id: str) -> str:
    """Analyze the current session and extract learnings.

    Called after browser_close to capture insights from the session.
    Reads diary entries and identifies patterns worth saving.

    Args:
        thread_id: Thread identifier for the session

    Returns:
        Reflection summary with accomplishments, challenges, learnings
    """
    agent_dir = StorageConfig.get_agent_dir()
    diary_dir = agent_dir / "memory" / "diary"

    # Find diary entries for this thread (use first 8 chars of thread_id)
    diary_entries = []
    thread_prefix = thread_id[:8] if len(thread_id) >= 8 else thread_id

    if diary_dir.exists():
        for entry_file in diary_dir.glob(f"*{thread_prefix}*.md"):
            try:
                content = entry_file.read_text()
                diary_entries.append(content)
            except Exception:
                pass

        # Also check for recent entries (might not have thread_id in name)
        if not diary_entries:
            for entry_file in sorted(diary_dir.glob("*.md"), reverse=True)[:5]:
                try:
                    content = entry_file.read_text()
                    diary_entries.append(content)
                except Exception:
                    pass

    if not diary_entries:
        return (
            "No diary entries found for this session.\n"
            "To enable reflection, create diary entries during task execution:\n"
            "write_file(.browser-agent/memory/diary/YYYY-MM-DD-task-name.md, content)"
        )

    # Analyze diary entries (simple pattern extraction)
    combined = "\n".join(diary_entries)

    output = ReflectionOutput(
        accomplishments=_extract_section(combined, "accomplishments"),
        challenges=_extract_section(combined, "challenges"),
        learnings=_extract_section(combined, "learnings"),
        skill_opportunities=[],
        rules_to_add=[]
    )

    # Check for repeated patterns that could become skills
    combined_lower = combined.lower()

    if "login" in combined_lower and ("password" in combined_lower or "credential" in combined_lower):
        output.skill_opportunities.append(SkillOpportunity(
            name="login-workflow",
            description="Automated login flow for web services",
            steps=["Navigate to login page", "Fill credentials", "Submit form", "Verify success"]
        ))

    if "search" in combined_lower and "results" in combined_lower:
        output.skill_opportunities.append(SkillOpportunity(
            name="search-workflow",
            description="Perform searches and extract results",
            steps=["Navigate to search page", "Enter query", "Submit search", "Extract results"]
        ))

    if "form" in combined_lower and ("fill" in combined_lower or "submit" in combined_lower):
        output.skill_opportunities.append(SkillOpportunity(
            name="form-filling",
            description="Fill and submit web forms",
            steps=["Identify form fields", "Fill each field", "Validate inputs", "Submit form"]
        ))

    # Format output
    result = "## Session Reflection\n\n"
    result += "### Accomplishments\n"
    for item in output.accomplishments or ["No accomplishments recorded"]:
        result += f"- {item}\n"

    result += "\n### Challenges\n"
    for item in output.challenges or ["No challenges recorded"]:
        result += f"- {item}\n"

    result += "\n### Learnings\n"
    for item in output.learnings or ["No learnings recorded"]:
        result += f"- {item}\n"

    if output.skill_opportunities:
        result += "\n### Skill Opportunities\n"
        result += "Consider creating these reusable skills:\n"
        for skill in output.skill_opportunities:
            result += f"- **{skill.name}**: {skill.description}\n"
            result += f"  Steps: {', '.join(skill.steps)}\n"

    result += "\n### Next Steps\n"
    result += "- Review and add key learnings to .browser-agent/memory/AGENTS.md\n"
    result += "- Consider creating skills for repeated patterns\n"

    return result


# Export reflection tools
REFLECTION_TOOLS = [reflect_on_session]
