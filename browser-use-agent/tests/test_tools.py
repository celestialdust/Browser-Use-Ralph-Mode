"""Tests for browser tools."""

import pytest
from unittest.mock import patch, MagicMock


def test_browser_scroll_down():
    """Test browser_scroll with down direction."""
    from browser_use_agent.tools import browser_scroll

    with patch('browser_use_agent.tools._run_browser_command') as mock_cmd:
        mock_cmd.return_value = {"success": True, "output": "Scrolled down 500px"}

        result = browser_scroll.invoke({
            "direction": "down",
            "amount": 500,
            "thread_id": "test-thread"
        })

        assert "Action:" in result
        assert "Scrolled down" in result
        mock_cmd.assert_called()


def test_browser_scroll_to_top():
    """Test browser_scroll with top direction."""
    from browser_use_agent.tools import browser_scroll

    with patch('browser_use_agent.tools._run_browser_command') as mock_cmd:
        mock_cmd.return_value = {"success": True, "output": "Scrolled to top"}

        result = browser_scroll.invoke({
            "direction": "top",
            "thread_id": "test-thread"
        })

        assert "top" in result.lower()


def test_browser_scroll_invalid_direction():
    """Test browser_scroll with invalid direction."""
    from browser_use_agent.tools import browser_scroll

    result = browser_scroll.invoke({
        "direction": "invalid",
        "thread_id": "test-thread"
    })

    assert "Invalid direction" in result


def test_browser_navigate_structured_output():
    """Test browser_navigate returns structured output."""
    from browser_use_agent.tools import browser_navigate

    with patch('browser_use_agent.tools._run_browser_command') as mock_cmd:
        with patch('browser_use_agent.tools.stream_manager') as mock_stream:
            with patch('browser_use_agent.tools._wait_for_stream_ready') as mock_wait:
                mock_cmd.return_value = {"success": True, "output": "Navigated"}
                mock_stream.get_stream_url.return_value = "ws://localhost:9223"
                mock_stream.get_port_for_thread.return_value = 9223
                mock_wait.return_value = True

                result = browser_navigate.invoke({
                    "url": "https://example.com",
                    "thread_id": "test-thread"
                })

                assert "Action:" in result
                assert "Navigated to https://example.com" in result
                assert "Observation:" in result
                assert "Next Step:" in result


def test_browser_snapshot_structured_output():
    """Test browser_snapshot returns structured output."""
    from browser_use_agent.tools import browser_snapshot
    import json

    with patch('browser_use_agent.tools._run_browser_command') as mock_cmd:
        mock_data = [{"ref": "@e1", "role": "button", "name": "Submit"}]
        mock_cmd.return_value = {"success": True, "output": json.dumps(mock_data)}

        result = browser_snapshot.invoke({
            "thread_id": "test-thread"
        })

        assert "Action:" in result
        assert "Observation:" in result
        assert "Next Step:" in result


def test_browser_click_structured_output():
    """Test browser_click returns structured output."""
    from browser_use_agent.tools import browser_click

    with patch('browser_use_agent.tools._run_browser_command') as mock_cmd:
        mock_cmd.return_value = {"success": True, "output": "Clicked"}

        result = browser_click.invoke({
            "ref": "@e1",
            "thread_id": "test-thread"
        })

        assert "Action:" in result
        assert "Clicked @e1" in result
        assert "Observation:" in result
        assert "Next Step:" in result
