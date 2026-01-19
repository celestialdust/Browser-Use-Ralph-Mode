"""Tests for reflection tools."""

import pytest
from pathlib import Path


def test_reflect_on_session_no_diary(tmp_path):
    """Test reflect_on_session when no diary entries exist."""
    from browser_use_agent.reflection import reflect_on_session

    # Mock the storage config to use temp path
    with pytest.MonkeyPatch.context() as mp:
        from browser_use_agent.storage import config
        mp.setattr(config.StorageConfig, 'get_agent_dir', lambda: tmp_path)

        result = reflect_on_session.invoke({"thread_id": "test-thread"})

        assert "no diary entries" in result.lower() or "no diary" in result.lower()


def test_reflect_on_session_with_diary(tmp_path):
    """Test reflect_on_session with diary entries."""
    from browser_use_agent.reflection import reflect_on_session

    # Create diary directory with an entry
    diary_dir = tmp_path / "memory" / "diary"
    diary_dir.mkdir(parents=True)

    diary_entry = diary_dir / "2026-01-19-test-thre-task.md"
    diary_entry.write_text("""# Session Diary

## Accomplishments
- Completed task successfully
- Navigated to example.com

## Challenges
- Element took time to load

## Learnings
- Need to wait for dynamic content
""")

    with pytest.MonkeyPatch.context() as mp:
        from browser_use_agent.storage import config
        mp.setattr(config.StorageConfig, 'get_agent_dir', lambda: tmp_path)

        result = reflect_on_session.invoke({"thread_id": "test-thread"})

        assert "accomplishments" in result.lower()


def test_reflection_output_model():
    """Test ReflectionOutput model structure."""
    from browser_use_agent.reflection import ReflectionOutput, SkillOpportunity

    output = ReflectionOutput(
        accomplishments=["Task completed"],
        challenges=["Had to retry"],
        learnings=["Use fresh snapshots"],
        skill_opportunities=[
            SkillOpportunity(
                name="login-flow",
                description="Automated login",
                steps=["Navigate", "Fill form", "Submit"]
            )
        ],
        rules_to_add=["Always snapshot after nav"]
    )

    assert len(output.accomplishments) == 1
    assert len(output.skill_opportunities) == 1
    assert output.skill_opportunities[0].name == "login-flow"


def test_extract_section():
    """Test section extraction from markdown."""
    from browser_use_agent.reflection import _extract_section

    content = """# Test Doc

## Accomplishments
- Did thing 1
- Did thing 2

## Challenges
- Problem 1
"""

    accomplishments = _extract_section(content, "accomplishments")
    assert len(accomplishments) == 2
    assert "Did thing 1" in accomplishments[0]

    challenges = _extract_section(content, "challenges")
    assert len(challenges) == 1
