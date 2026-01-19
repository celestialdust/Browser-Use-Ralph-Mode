"""Tests for BrowserToolOutput model."""

import pytest
from browser_use_agent.models import BrowserToolOutput


def test_browser_tool_output_all_fields():
    """Test that BrowserToolOutput can be created with all fields."""
    output = BrowserToolOutput(
        action="Navigated to https://example.com",
        observation="Page loaded successfully with title 'Example Domain'",
        next_step="Take browser_snapshot to see available elements",
        filepath="/Users/test/.browser-agent/artifacts/tool_outputs/navigate_abc123_20260119_120000.txt"
    )
    assert output.action == "Navigated to https://example.com"
    assert output.observation == "Page loaded successfully with title 'Example Domain'"
    assert output.next_step == "Take browser_snapshot to see available elements"
    assert output.filepath.endswith(".txt")


def test_browser_tool_output_to_string():
    """Test that BrowserToolOutput converts to string correctly."""
    output = BrowserToolOutput(
        action="Clicked @e1",
        observation="Button was clicked, page state changed",
        next_step="Take snapshot to verify result",
        filepath="/path/to/output.txt"
    )
    result = output.to_string()
    assert "Action:" in result
    assert "Clicked @e1" in result
    assert "Observation:" in result
    assert "Button was clicked, page state changed" in result
    assert "Next Step:" in result
    assert "Take snapshot to verify result" in result
    assert "Full Output:" in result
    assert "/path/to/output.txt" in result


def test_browser_tool_output_model_validation():
    """Test that BrowserToolOutput validates required fields."""
    # Should raise validation error if required fields missing
    with pytest.raises(Exception):
        BrowserToolOutput()
