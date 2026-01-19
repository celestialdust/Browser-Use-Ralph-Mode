"""Pydantic models for browser agent structured outputs."""

from pydantic import BaseModel, Field


class BrowserToolOutput(BaseModel):
    """Structured output for all browser tool calls.

    This provides consistent, predictable output format that:
    1. Tells the agent what happened (action)
    2. Describes current state (observation)
    3. Suggests what to do next (next_step)
    4. Points to full output if needed (filepath)
    """

    action: str = Field(
        description="The action that was performed"
    )
    observation: str = Field(
        description="What was observed after the action"
    )
    next_step: str = Field(
        description="Suggested next step based on observation"
    )
    filepath: str = Field(
        description="Absolute path to file containing full command output"
    )

    def to_string(self) -> str:
        """Convert to human-readable string format."""
        return (
            f"Action: {self.action}\n"
            f"Observation: {self.observation}\n"
            f"Next Step: {self.next_step}\n"
            f"Full Output: {self.filepath}"
        )
