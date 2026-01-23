"""Tool for presenting files to the user in the UI."""

import uuid
from datetime import datetime
from typing import Optional, Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from pydantic import BaseModel, Field


# File type mapping
FILE_TYPE_MAP = {
    ".pdf": "PDF",
    ".docx": "DOCX",
    ".doc": "DOC",
    ".pptx": "PPTX",
    ".ppt": "PPT",
    ".xlsx": "XLSX",
    ".xls": "XLS",
    ".md": "Markdown",
    ".txt": "Text",
    ".json": "JSON",
    ".csv": "CSV",
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".gif": "GIF",
    ".svg": "SVG",
    ".webp": "WEBP",
    ".html": "HTML",
}


class PresentFileInput(BaseModel):
    """Input for present_file tool."""
    file_path: str = Field(description="Path to the file to present (relative to .browser-agent)")
    display_name: str = Field(description="Name to display in the UI")
    description: Optional[str] = Field(default=None, description="Optional description of the file")


@tool("present_file", args_schema=PresentFileInput)
def present_file_tool(
    file_path: str,
    display_name: str,
    description: Optional[str] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = ""
) -> Command:
    """Present a file to the user in the chat UI.

    Use this after generating a file (PDF, DOCX, PPTX, Markdown, etc.) to make it
    visible and downloadable in the chat interface.

    The file will appear as a clickable card that opens a preview panel.

    Args:
        file_path: Path to the file relative to .browser-agent directory
        display_name: Human-readable name to show in the UI
        description: Optional description of what the file contains

    Returns:
        Command with state update to add file to presented_files list
    """
    from browser_use_agent.storage import StorageConfig

    agent_dir = StorageConfig.get_agent_dir()
    full_path = agent_dir / file_path

    if not full_path.exists():
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"Error: File not found at {file_path}",
                        tool_call_id=tool_call_id
                    )
                ]
            }
        )

    # Get file info
    file_size = full_path.stat().st_size
    file_ext = full_path.suffix.lower()
    file_type = FILE_TYPE_MAP.get(file_ext, "File")

    # Create presented file entry
    # Include tool_call_id so the frontend can associate this file
    # with the message that contains this tool call
    presented_file = {
        "id": str(uuid.uuid4()),
        "file_path": file_path,
        "display_name": display_name,
        "description": description,
        "file_type": file_type,
        "file_size": file_size,
        "presented_at": datetime.utcnow().isoformat() + "Z",
        "tool_call_id": tool_call_id,
    }

    result_message = f"Presented file '{display_name}' ({file_type}, {file_size} bytes) to user"

    # Return Command that updates both messages and presented_files
    return Command(
        update={
            "messages": [
                ToolMessage(content=result_message, tool_call_id=tool_call_id)
            ],
            "presented_files": [presented_file]
        }
    )
