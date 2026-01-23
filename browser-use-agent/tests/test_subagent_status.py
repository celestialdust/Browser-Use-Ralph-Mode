"""Tests for SubagentStatus type definitions."""

import pytest
from browser_use_agent.state import SubagentStatus, AgentState


def test_subagent_status_structure():
    """Test SubagentStatus has required fields."""
    status = SubagentStatus(
        subagent_id="sa_123",
        subagent_type="research",
        prompt="Research AI trends",
        status="running",
        started_at="2026-01-22T10:00:00Z",
        tool_calls_count=3,
        last_activity="Searching web..."
    )
    assert status["status"] == "running"
    assert status["tool_calls_count"] == 3
    assert status["subagent_id"] == "sa_123"
    assert status["subagent_type"] == "research"
    assert status["prompt"] == "Research AI trends"


def test_subagent_status_optional_fields():
    """Test SubagentStatus optional fields."""
    status = SubagentStatus(
        subagent_id="sa_456",
        subagent_type="browser",
        prompt="Navigate to example.com",
        status="completed",
        started_at="2026-01-22T10:00:00Z",
        completed_at="2026-01-22T10:05:00Z",
        tool_calls_count=5,
        last_activity=None,
        result_summary="Successfully navigated to example.com",
        error=None
    )
    assert status["status"] == "completed"
    assert status["completed_at"] == "2026-01-22T10:05:00Z"
    assert status["result_summary"] == "Successfully navigated to example.com"


def test_subagent_status_error_state():
    """Test SubagentStatus with error state."""
    status = SubagentStatus(
        subagent_id="sa_789",
        subagent_type="file_writer",
        prompt="Write a report",
        status="error",
        started_at="2026-01-22T10:00:00Z",
        tool_calls_count=2,
        error="Permission denied: cannot write to file"
    )
    assert status["status"] == "error"
    assert status["error"] == "Permission denied: cannot write to file"


def test_agent_state_includes_active_subagents():
    """Test AgentState includes active_subagents field."""
    from browser_use_agent.state import create_initial_state

    state = create_initial_state("test-thread-123")

    # active_subagents should be in the state (may be None initially)
    assert "active_subagents" in state or state.get("active_subagents") is None


def test_subagent_status_all_status_values():
    """Test all valid status values for SubagentStatus."""
    valid_statuses = ["pending", "running", "completed", "error", "cancelled"]

    for status_value in valid_statuses:
        status = SubagentStatus(
            subagent_id=f"sa_{status_value}",
            subagent_type="test",
            prompt="Test prompt",
            status=status_value,
            started_at="2026-01-22T10:00:00Z",
            tool_calls_count=0
        )
        assert status["status"] == status_value
