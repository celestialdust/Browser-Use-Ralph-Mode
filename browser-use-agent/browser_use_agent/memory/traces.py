"""LangSmith trace collection using langsmith fetch CLI."""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from browser_use_agent.storage import StorageConfig


class LangSmithTraceFetcher:
    """Fetches and caches agent traces using langsmith fetch CLI.

    Requires:
        - langsmith-fetch CLI installed (uv pip install langsmith-fetch)
        - LANGSMITH_API_KEY environment variable
        - LANGSMITH_PROJECT environment variable
    """

    def __init__(self, project_name: str = "browser-agent"):
        """Initialize trace fetcher.

        Args:
            project_name: LangSmith project name (should match LANGSMITH_PROJECT env var)
        """
        self.project_name = project_name
        self.cache_dir = StorageConfig.get_agent_dir() / "traces"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_recent_traces(
        self,
        hours: int = 24,
        limit: int = 100,
        min_feedback_score: float = 0.7
    ) -> List[Dict]:
        """Fetch successful traces from last N hours using langsmith fetch CLI.

        The CLI command used:
            langsmith fetch traces <cache_dir> \\
                --limit <limit> \\
                --last-n-minutes <minutes> \\
                --include-metadata \\
                --include-feedback \\
                --format json

        Args:
            hours: Look back period in hours
            limit: Maximum number of traces to fetch
            min_feedback_score: Minimum user feedback score (0-1)

        Returns:
            List of trace data dictionaries filtered by feedback score
        """
        minutes = hours * 60

        print(f"[Traces] Fetching from LangSmith project: {self.project_name}")
        print(f"[Traces] Last {hours} hours, limit {limit}, min score {min_feedback_score}")

        # Run langsmith fetch CLI
        # The CLI will save JSON files to cache_dir
        cmd = [
            "langsmith", "fetch", "traces",
            str(self.cache_dir),
            "--limit", str(limit),
            "--last-n-minutes", str(minutes),
            "--include-metadata",
            "--include-feedback",
            "--format", "json"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60  # Prevent hanging
            )
            if result.stdout:
                print(f"[Traces] CLI output: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"[Traces] Error running langsmith fetch: {e.stderr}")
            print("[Traces] Check that LANGSMITH_API_KEY and LANGSMITH_PROJECT are set")
            return []
        except FileNotFoundError:
            print("[Traces] Error: langsmith CLI not found")
            print("[Traces] Install with: uv pip install langsmith-fetch")
            return []
        except subprocess.TimeoutExpired:
            print("[Traces] Error: langsmith fetch timed out after 60s")
            return []

        # Read all trace files from cache directory
        traces = []
        for trace_file in sorted(
            self.cache_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        ):
            try:
                trace_data = json.loads(trace_file.read_text())

                # Filter by feedback score
                feedback_score = self._get_feedback_score(trace_data)
                if feedback_score >= min_feedback_score:
                    traces.append(trace_data)

            except (json.JSONDecodeError, Exception) as e:
                print(f"[Traces] Error reading {trace_file.name}: {e}")
                continue

        print(f"[Traces] Fetched {len(traces)} traces with min score {min_feedback_score}")
        return traces

    def _get_feedback_score(self, trace_data: Dict) -> float:
        """Extract feedback score from trace data.

        The langsmith fetch CLI includes feedback in various formats.
        This method attempts to extract the score from common locations.

        Args:
            trace_data: Trace data from langsmith fetch

        Returns:
            Feedback score (0-1), defaults to 0 if not found
        """
        # Check for feedback array (most common format)
        if "feedback" in trace_data:
            feedback = trace_data["feedback"]
            if isinstance(feedback, list) and len(feedback) > 0:
                # Average all feedback scores
                scores = [f.get("score", 0) for f in feedback if "score" in f]
                return sum(scores) / len(scores) if scores else 0.0

        # Check metadata for feedback_score
        if "metadata" in trace_data:
            metadata = trace_data["metadata"]
            if "feedback_score" in metadata:
                return float(metadata["feedback_score"])

        # No feedback found
        return 0.0

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

        if removed > 0:
            print(f"[Traces] Removed {removed} cached traces older than {older_than_days} days")
