"""Tests for present_file tool."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from langgraph.types import Command


def test_present_file_tool_exists():
    """Test that present_file tool is available."""
    from browser_use_agent.present_file import present_file_tool

    assert present_file_tool is not None
    assert present_file_tool.name == "present_file"


def test_present_file_requires_path():
    """Test that present_file requires file_path."""
    from browser_use_agent.present_file import present_file_tool

    schema = present_file_tool.args_schema.model_json_schema()
    assert "file_path" in schema["required"]


def test_present_file_requires_display_name():
    """Test that present_file requires display_name."""
    from browser_use_agent.present_file import present_file_tool

    schema = present_file_tool.args_schema.model_json_schema()
    assert "display_name" in schema["required"]


def test_present_file_description_optional():
    """Test that description is optional."""
    from browser_use_agent.present_file import present_file_tool

    schema = present_file_tool.args_schema.model_json_schema()
    # description should NOT be in required
    assert "description" not in schema.get("required", [])


def _invoke_tool_with_call_id(tool, args, tool_call_id="test-call-id"):
    """Helper to invoke tool with proper ToolCall format."""
    tool_call = {
        "name": tool.name,
        "args": args,
        "type": "tool_call",
        "id": tool_call_id,
    }
    return tool.invoke(tool_call)


def test_present_file_with_existing_file():
    """Test present_file with an existing file."""
    from browser_use_agent.present_file import present_file_tool

    # Create a temporary directory and file
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create artifacts directory structure
        artifacts_dir = Path(tmpdir) / "artifacts"
        artifacts_dir.mkdir(parents=True)

        # Create a test file
        test_file = artifacts_dir / "test_report.pdf"
        test_file.write_bytes(b"fake pdf content for testing")

        # Mock StorageConfig at the storage module level
        with patch('browser_use_agent.storage.StorageConfig') as mock_config:
            mock_config.get_agent_dir.return_value = Path(tmpdir)

            result = _invoke_tool_with_call_id(present_file_tool, {
                "file_path": "artifacts/test_report.pdf",
                "display_name": "Test Report",
                "description": "A test PDF report"
            })

            # Result is now a Command object
            assert isinstance(result, Command)
            assert "messages" in result.update
            assert "presented_files" in result.update

            # Check the message content
            message = result.update["messages"][0]
            assert "Presented file" in message.content
            assert "Test Report" in message.content
            assert "PDF" in message.content

            # Check the presented file entry
            presented_file = result.update["presented_files"][0]
            assert presented_file["display_name"] == "Test Report"
            assert presented_file["file_type"] == "PDF"
            assert presented_file["description"] == "A test PDF report"


def test_present_file_nonexistent_file():
    """Test present_file with a non-existent file."""
    from browser_use_agent.present_file import present_file_tool

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('browser_use_agent.storage.StorageConfig') as mock_config:
            mock_config.get_agent_dir.return_value = Path(tmpdir)

            result = _invoke_tool_with_call_id(present_file_tool, {
                "file_path": "artifacts/nonexistent.pdf",
                "display_name": "Missing File"
            })

            # Result is a Command with error message
            assert isinstance(result, Command)
            assert "messages" in result.update

            message = result.update["messages"][0]
            assert "Error" in message.content
            assert "not found" in message.content

            # No presented_files for error case
            assert "presented_files" not in result.update


def test_present_file_different_file_types():
    """Test present_file with different file types."""
    from browser_use_agent.present_file import present_file_tool

    test_cases = [
        (".pdf", "PDF"),
        (".docx", "DOCX"),
        (".pptx", "PPTX"),
        (".xlsx", "XLSX"),
        (".md", "Markdown"),
        (".txt", "Text"),
        (".json", "JSON"),
        (".csv", "CSV"),
        (".png", "PNG"),
        (".html", "HTML"),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        artifacts_dir = Path(tmpdir) / "artifacts"
        artifacts_dir.mkdir(parents=True)

        with patch('browser_use_agent.storage.StorageConfig') as mock_config:
            mock_config.get_agent_dir.return_value = Path(tmpdir)

            for ext, expected_type in test_cases:
                test_file = artifacts_dir / f"test{ext}"
                test_file.write_bytes(b"test content")

                result = _invoke_tool_with_call_id(present_file_tool, {
                    "file_path": f"artifacts/test{ext}",
                    "display_name": f"Test {ext} file"
                }, tool_call_id=f"call-{ext}")

                assert isinstance(result, Command)
                presented_file = result.update["presented_files"][0]
                assert presented_file["file_type"] == expected_type, \
                    f"Expected '{expected_type}' for {ext}, got: {presented_file['file_type']}"


def test_present_file_returns_file_size():
    """Test that present_file returns file size information."""
    from browser_use_agent.present_file import present_file_tool

    with tempfile.TemporaryDirectory() as tmpdir:
        artifacts_dir = Path(tmpdir) / "artifacts"
        artifacts_dir.mkdir(parents=True)

        # Create a file with known size
        test_file = artifacts_dir / "test.txt"
        content = b"x" * 100
        test_file.write_bytes(content)

        with patch('browser_use_agent.storage.StorageConfig') as mock_config:
            mock_config.get_agent_dir.return_value = Path(tmpdir)

            result = _invoke_tool_with_call_id(present_file_tool, {
                "file_path": "artifacts/test.txt",
                "display_name": "Test File"
            })

            assert isinstance(result, Command)

            # Check message content includes size
            message = result.update["messages"][0]
            assert "100 bytes" in message.content

            # Check presented file entry has correct size
            presented_file = result.update["presented_files"][0]
            assert presented_file["file_size"] == 100


def test_present_file_includes_timestamp():
    """Test that presented file includes timestamp."""
    from browser_use_agent.present_file import present_file_tool

    with tempfile.TemporaryDirectory() as tmpdir:
        artifacts_dir = Path(tmpdir) / "artifacts"
        artifacts_dir.mkdir(parents=True)

        test_file = artifacts_dir / "test.txt"
        test_file.write_text("test content")

        with patch('browser_use_agent.storage.StorageConfig') as mock_config:
            mock_config.get_agent_dir.return_value = Path(tmpdir)

            result = _invoke_tool_with_call_id(present_file_tool, {
                "file_path": "artifacts/test.txt",
                "display_name": "Test File"
            })

            presented_file = result.update["presented_files"][0]
            assert "presented_at" in presented_file
            assert presented_file["presented_at"].endswith("Z")  # ISO format with Z


def test_present_file_generates_unique_id():
    """Test that each presented file gets a unique ID."""
    from browser_use_agent.present_file import present_file_tool

    with tempfile.TemporaryDirectory() as tmpdir:
        artifacts_dir = Path(tmpdir) / "artifacts"
        artifacts_dir.mkdir(parents=True)

        test_file = artifacts_dir / "test.txt"
        test_file.write_text("test content")

        with patch('browser_use_agent.storage.StorageConfig') as mock_config:
            mock_config.get_agent_dir.return_value = Path(tmpdir)

            # Call twice and check IDs are different
            result1 = _invoke_tool_with_call_id(present_file_tool, {
                "file_path": "artifacts/test.txt",
                "display_name": "Test File 1"
            }, tool_call_id="call-1")
            result2 = _invoke_tool_with_call_id(present_file_tool, {
                "file_path": "artifacts/test.txt",
                "display_name": "Test File 2"
            }, tool_call_id="call-2")

            id1 = result1.update["presented_files"][0]["id"]
            id2 = result2.update["presented_files"][0]["id"]
            assert id1 != id2


def test_present_file_tool_call_id_in_message():
    """Test that ToolMessage has correct tool_call_id."""
    from browser_use_agent.present_file import present_file_tool

    with tempfile.TemporaryDirectory() as tmpdir:
        artifacts_dir = Path(tmpdir) / "artifacts"
        artifacts_dir.mkdir(parents=True)

        test_file = artifacts_dir / "test.txt"
        test_file.write_text("test content")

        with patch('browser_use_agent.storage.StorageConfig') as mock_config:
            mock_config.get_agent_dir.return_value = Path(tmpdir)

            result = _invoke_tool_with_call_id(present_file_tool, {
                "file_path": "artifacts/test.txt",
                "display_name": "Test File"
            }, tool_call_id="my-unique-call-id")

            message = result.update["messages"][0]
            assert message.tool_call_id == "my-unique-call-id"
