"""Tests for browser agent creation and context loading."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_load_context_files_empty():
    """Test context loading when no context files exist."""
    from browser_use_agent.browser_agent import _load_context_files

    # Use a non-existent directory
    non_existent = Path("/tmp/non_existent_agent_dir_12345")

    result = _load_context_files(non_existent)
    assert result == ""


def test_load_context_files_with_agents_md(tmp_path):
    """Test context loading with AGENTS.md file."""
    from browser_use_agent.browser_agent import _load_context_files

    # Create memory directory and AGENTS.md
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    agents_md = memory_dir / "AGENTS.md"
    agents_md.write_text("# Browser Agent Memory\n\n" + "x" * 250)  # >200 chars to include

    result = _load_context_files(tmp_path)
    assert "<project_memory>" in result
    assert "Browser Agent Memory" in result


def test_load_context_files_with_skills(tmp_path):
    """Test context loading with skills metadata."""
    from browser_use_agent.browser_agent import _load_context_files

    # Create skills directory with a skill
    skills_dir = tmp_path / "skills"
    skill_folder = skills_dir / "google-search"
    skill_folder.mkdir(parents=True)

    skill_md = skill_folder / "SKILL.md"
    skill_md.write_text("""---
name: google-search
description: Perform Google searches
---

# Google Search Skill

Steps to search Google...
""")

    result = _load_context_files(tmp_path)
    assert "<skills>" in result
    assert "google-search" in result
    assert "Perform Google searches" in result


def test_load_context_files_truncates_long_agent_md(tmp_path):
    """Test that agent.md is truncated if too long."""
    from browser_use_agent.browser_agent import _load_context_files

    # Create agent.md with lots of content
    agent_md = tmp_path / "agent.md"
    agent_md.write_text("# Technical Reference\n\n" + "x" * 5000)

    result = _load_context_files(tmp_path)
    assert "<agent_memory>" in result
    assert "[...truncated for brevity...]" in result
