"""Tests for system prompts."""

import pytest


def test_system_prompt_contains_required_sections():
    """Test that system prompt contains all required XML sections."""
    from browser_use_agent.prompts import BROWSER_AGENT_SYSTEM_PROMPT

    required_sections = [
        "<role>",
        "<task_management>",
        "<file_management>",
        "<browser_tools>",
        "<workflow>",
        "<constraints>",
    ]

    for section in required_sections:
        assert section in BROWSER_AGENT_SYSTEM_PROMPT, f"Missing section: {section}"


def test_workflow_section_has_planning_step():
    """Test that workflow section instructs agent to plan before acting."""
    from browser_use_agent.prompts import BROWSER_AGENT_SYSTEM_PROMPT

    # Workflow should instruct agent to plan before doing
    assert "plan" in BROWSER_AGENT_SYSTEM_PROMPT.lower()
    assert "write_todos" in BROWSER_AGENT_SYSTEM_PROMPT


def test_system_prompt_has_error_recovery():
    """Test that system prompt has error recovery section."""
    from browser_use_agent.prompts import BROWSER_AGENT_SYSTEM_PROMPT

    assert "<error_recovery>" in BROWSER_AGENT_SYSTEM_PROMPT
    assert "Element not found" in BROWSER_AGENT_SYSTEM_PROMPT or "element not found" in BROWSER_AGENT_SYSTEM_PROMPT.lower()


def test_system_prompt_mentions_browser_close():
    """Test that system prompt emphasizes closing browser."""
    from browser_use_agent.prompts import BROWSER_AGENT_SYSTEM_PROMPT

    assert "browser_close" in BROWSER_AGENT_SYSTEM_PROMPT


def test_system_prompt_has_subagent_guidance():
    """Test that system prompt has subagent delegation guidance."""
    from browser_use_agent.prompts import BROWSER_AGENT_SYSTEM_PROMPT

    assert "<subagents>" in BROWSER_AGENT_SYSTEM_PROMPT or "subagent" in BROWSER_AGENT_SYSTEM_PROMPT.lower()
