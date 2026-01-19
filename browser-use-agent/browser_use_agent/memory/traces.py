"""LangSmith trace collection for learning from agent executions."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    from langsmith import Client
except ImportError:
    print("Warning: langsmith not installed. Run: uv pip install langsmith")
    Client = None

from browser_use_agent.storage import StorageConfig


class LangSmithTraceFetcher:
    """Fetches and caches agent traces from LangSmith."""

    def __init__(self, project_name: str = "browser-agent"):
        """Initialize trace fetcher.

        Args:
            project_name: LangSmith project name
        """
        if Client is None:
            raise ImportError("langsmith package required. Run: uv pip install langsmith")

        self.client = Client()
        self.project_name = project_name
        self.cache_dir = StorageConfig.get_agent_dir() / "traces"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_recent_traces(
        self,
        hours: int = 24,
        filter_tags: Optional[List[str]] = None,
        min_feedback_score: float = 0.7
    ) -> List[Dict]:
        """Fetch successful traces from last N hours.

        Args:
            hours: Look back period
            filter_tags: Only fetch traces with these tags
            min_feedback_score: Minimum user feedback score (0-1)

        Returns:
            List of trace data dictionaries
        """
        end = datetime.now()
        start = end - timedelta(hours=hours)

        # Build filter query
        filter_query = f'and(eq(status, "success"), gt(feedback_score, {min_feedback_score}))'
        if filter_tags:
            tag_filters = " or ".join([f'eq(tags, "{tag}")' for tag in filter_tags])
            filter_query = f"and({filter_query}, or({tag_filters}))"

        print(f"[Traces] Fetching from LangSmith project: {self.project_name}")
        print(f"[Traces] Filter: {filter_query}")

        runs = self.client.list_runs(
            project_name=self.project_name,
            start_time=start,
            filter=filter_query
        )

        traces = []
        for run in runs:
            # Check cache first
            trace_path = self.cache_dir / f"{run.id}.json"
            if trace_path.exists():
                trace_data = json.loads(trace_path.read_text())
            else:
                # Extract and cache
                trace_data = self._extract_trace_data(run)
                trace_path.write_text(json.dumps(trace_data, indent=2))

            traces.append(trace_data)

        print(f"[Traces] Fetched {len(traces)} traces")
        return traces

    def _extract_trace_data(self, run) -> Dict:
        """Extract relevant data from LangSmith run."""
        return {
            "run_id": str(run.id),
            "task": run.inputs.get("task", ""),
            "steps": self._extract_steps(run),
            "success": run.status == "success",
            "feedback_score": run.feedback_stats.get("score", 0) if run.feedback_stats else 0,
            "duration_ms": run.total_tokens if hasattr(run, "total_tokens") else 0,
            "timestamp": run.start_time.isoformat() if run.start_time else "",
            "tags": run.tags or [],
            "metadata": run.extra or {},
        }

    def _extract_steps(self, run) -> List[Dict]:
        """Extract execution steps from run."""
        steps = []

        # Extract tool calls from run outputs
        if hasattr(run, "outputs") and run.outputs:
            messages = run.outputs.get("messages", [])
            for msg in messages:
                if hasattr(msg, "additional_kwargs"):
                    tool_calls = msg.additional_kwargs.get("tool_calls", [])
                    for tool_call in tool_calls:
                        steps.append({
                            "tool": tool_call.get("name", "unknown"),
                            "args": tool_call.get("args", {}),
                            "result": tool_call.get("result", ""),
                        })

        return steps

    def clear_cache(self, older_than_days: int = 30):
        """Remove cached traces older than N days.

        Args:
            older_than_days: Remove traces older than this many days
        """
        cutoff = datetime.now() - timedelta(days=older_than_days)
        removed = 0

        for trace_file in self.cache_dir.glob("*.json"):
            if trace_file.stat().st_mtime < cutoff.timestamp():
                trace_file.unlink()
                removed += 1

        print(f"[Traces] Removed {removed} cached traces older than {older_than_days} days")
