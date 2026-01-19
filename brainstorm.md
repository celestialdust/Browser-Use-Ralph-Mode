# Production-Grade Browser-Use Agent Architecture Design

**Date:** 2026-01-19

**Goal:** Transform the current browser-use agent into a production-grade system by applying deepagents CLI architecture patterns, adding middleware, backends, memory/learning systems, skills, and enhanced UI.

---

## Architecture Overview

**Layered Architecture (Bottom-Up):**

1. **Backend & Storage Layer** - Database (SQLite/PostgreSQL) + Filesystem (deepagents library)
2. **Memory & Learning Layer** - LangSmith traces, domain knowledge, adaptive learning
3. **Middleware Stack** - Core deepagents + browser-specific + production middleware
4. **Tool Layer** - Built-in browser tools + Bash tool for advanced commands
5. **Skills System** - Auto-generation from traces with sandbox testing
6. **Agent & UI Layer** - ChatOpenAI with reasoning, enhanced web UI

---

## Layer 1: Tool Layer

**Design Principle:** Use the most common agent-browser commands as built-in tools, with Bash tool for specialized/advanced commands.

### Built-in Browser Tools (20 core commands)

**Navigation (5 tools):**
- `browser_open(url, thread_id)` - Navigate to URL
- `browser_back(thread_id)` - Go back
- `browser_forward(thread_id)` - Go forward
- `browser_reload(thread_id)` - Reload page
- `browser_close(thread_id)` - Close browser

**Interaction (8 tools):**
- `browser_click(ref, thread_id)` - Click element (@ref or selector)
- `browser_type(ref, text, thread_id)` - Type into element
- `browser_fill(ref, text, thread_id)` - Clear and fill element
- `browser_press(key, thread_id)` - Press key (Enter, Tab, Control+a)
- `browser_hover(ref, thread_id)` - Hover element
- `browser_check(ref, thread_id)` - Check checkbox
- `browser_uncheck(ref, thread_id)` - Uncheck checkbox
- `browser_select(ref, value, thread_id)` - Select dropdown option

**Observation (5 tools):**
- `browser_snapshot(thread_id, interactive_only)` - Get accessibility tree with @refs (CRITICAL for AI)
- `browser_get(info_type, thread_id, ref)` - Get info (text, html, value, attr, title, url, count)
- `browser_is_visible(ref, thread_id)` - Check if visible
- `browser_is_enabled(ref, thread_id)` - Check if enabled
- `browser_is_checked(ref, thread_id)` - Check if checked
- `browser_screenshot(thread_id, filename)` - Take screenshot
- `browser_wait(thread_id, condition, value)` - Wait for element or time

**Session & Settings (2 tools):**
- `browser_cookies(action, thread_id, data)` - Manage cookies (get, set, clear)
- `browser_set_viewport(width, height, thread_id)` - Set viewport size
- `browser_set_headers(headers_json, thread_id)` - Set HTTP headers
- `browser_set_device(device_name, thread_id)` - Set device emulation
- `browser_set_geo(lat, lng, thread_id)` - Set geolocation
- `browser_set_credentials(username, password, thread_id)` - Set HTTP auth credentials

**Bash Tool (for advanced/specialized commands):**
- Executes any agent-browser command not in built-in tools
- Examples: `drag`, `upload`, `find`, `pdf`, `eval`, `mouse`, `network`, `trace`, `console`, `storage`, `tab`
- Learns new command patterns from skills
- Has access to full `agent-browser --help` in context
- Sandboxed execution with timeout

**Tool Changes from Current Implementation:**
- ADD: Navigation controls (back, forward, reload)
- ADD: Checkbox operations (check, uncheck)
- ADD: Dropdown selection (select)
- ADD: Device/geo/credentials settings
- KEEP: Individual `is_visible`, `is_enabled`, `is_checked` (no unified `is` command)
- KEEP: Individual viewport/headers settings (no unified `set` command)
- CONSOLIDATE: `browser_get` for all info retrieval

---

## Layer 2: Backend & Storage Layer

**Design Principle:** Dual database support (SQLite for dev, PostgreSQL for production) + deepagents filesystem backend for file operations.

### Database Storage (Checkpoints)

**SQLite (Local Development):**
- File: `.browser-agent/checkpoints/browser_agent.db`
- Uses: `AsyncSqliteSaver` from LangGraph
- Benefits: Zero setup, portable, perfect for local dev/demos

**PostgreSQL (Production):**
- Cloud services: Supabase, AWS RDS, Google Cloud SQL
- Uses: `AsyncPostgresSaver` from LangGraph
- Connection: `DATABASE_URL` environment variable
- Benefits: Multi-instance shared state, production durability, backups

**Configuration:**
```python
class StorageConfig:
    DB_TYPE: str = os.getenv("CHECKPOINT_DB_TYPE", "sqlite")
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "./checkpoints/browser_agent.db")
    POSTGRES_URI: str = os.getenv("DATABASE_URL", "")
    POSTGRES_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))

    # Supabase-specific
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
```

**Factory Pattern:**
```python
async def get_checkpoint_saver() -> BaseCheckpointSaver:
    """Factory to create SQLite or PostgreSQL checkpoint saver."""
    if StorageConfig.DB_TYPE == "postgres":
        return AsyncPostgresSaver.from_conn_string(
            StorageConfig.POSTGRES_URI,
            pool_size=StorageConfig.POSTGRES_POOL_SIZE
        )
    else:
        return AsyncSqliteSaver.from_conn_string(StorageConfig.SQLITE_PATH)
```

### Filesystem Storage

**Implementation:** Use deepagents library's `FilesystemBackend` and `FilesystemMiddleware` (DO NOT reimplement).

**Directory Structure:**
```
<project_root>/.browser-agent/          # Project-specific (git root detected)
├── checkpoints/
│   └── browser_agent.db                # SQLite checkpoints (if local)
├── memory/
│   ├── AGENTS.md                       # Project-level agent memory
│   ├── USER_PREFERENCES.md             # User preferences (max 2000 tokens)
│   └── domains/                        # Per-domain learned knowledge
│       ├── google.com.md               # "Google often triggers CAPTCHA, use viewport 1920x1080"
│       ├── linkedin.com.md             # "LinkedIn requires human-like delays (1500ms)"
│       └── github.com.md
├── skills/                             # Auto-generated and custom skills
│   ├── google_search.md
│   ├── linkedin_login.md               # Skill with prerequisite: credential
│   └── form_filling.md
├── settings/
│   ├── config.json                     # Agent configuration
│   └── credentials.json                # Encrypted credentials vault
├── artifacts/
│   ├── screenshots/                    # Session screenshots
│   │   └── <thread_id>/
│   └── sessions/                       # Browser session data
│       └── <thread_id>/
│           ├── cookies.json
│           ├── localstorage.json
│           └── metadata.json
└── traces/                             # Cached LangSmith traces
    └── <date>/
        └── <trace_id>.json

~/.browser-agent/                       # User-level storage
├── memory/
│   ├── AGENTS.md                       # User-level agent memory
│   └── USER_PREFERENCES.md             # Global user preferences
├── skills/                             # User's personal skills
└── settings/
    └── global_config.json              # User preferences
```

**User Preferences Management:**
```python
class UserPreferencesManager:
    """Manages user preferences with token limits."""
    MAX_TOKENS = 2000  # Prevent context bloat

    async def load_preferences(self) -> str:
        """Load and merge user + project preferences, truncate to limit."""
        # Loaded into system prompt at session start
        # Contains: UI preferences, default browser settings, common workflows
```

**Backend Modes:**
- **Local mode:** Uses deepagents `FilesystemBackend` with local execution
- **Sandbox mode (future):** Uses `RemoteSandboxBackend` (Daytona/Modal/Runloop style)
- Both implement `SandboxBackendProtocol` for command execution

**Backend Protocol:**
```python
class BackendProtocol(Protocol):
    @property
    def id(self) -> str: ...

class SandboxBackendProtocol(BackendProtocol, Protocol):
    async def execute(self, command: str) -> ExecuteResponse: ...
```

---

## Summary of Decisions

**Tool Layer:**
- 20 built-in browser tools based on `agent-browser --help` most common commands
- Bash tool for advanced/specialized commands
- Keep individual `is_*` and `set_*` tools (no unified commands)

**Backend & Storage:**
- Dual database: SQLite (dev) + PostgreSQL (production) via environment variable
- Use deepagents `FilesystemBackend` (don't reimplement)
- Project-aware directory structure with git root detection
- User preferences loaded into prompt (max 2000 tokens)
- Support for future sandbox backends (Daytona-style)

---

---

## Layer 3: Memory & Learning Layer

**Design Principle:** Two-tier memory system (episodic + procedural) inspired by Claude Diary pattern, with LangSmith-powered skill discovery and domain-specific learning.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Memory & Learning Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Episodic Memory          Procedural Memory                 │
│  (Raw Sessions)           (Distilled Rules)                 │
│                                                              │
│  ┌────────────────┐      ┌────────────────────────┐        │
│  │ Session Logs   │      │ AGENTS.md              │        │
│  │ LangSmith      │─────▶│ USER_PREFERENCES.md    │        │
│  │ Traces         │      │ domains/*.md           │        │
│  │ Diary Entries  │      │ skills/*.md            │        │
│  └────────────────┘      └────────────────────────┘        │
│         │                          ▲                        │
│         │                          │                        │
│         ▼                          │                        │
│  ┌────────────────────────────────────────────┐            │
│  │      Reflection & Analysis Engine          │            │
│  │  - Trajectory Analyzer                     │            │
│  │  - Pattern Extractor                       │            │
│  │  - Skill Generator                         │            │
│  │  - Rule Synthesizer                        │            │
│  └────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Part 1: Episodic Memory (Raw Experience Capture)

**1.1 LangSmith Trace Collection**

```python
class LangSmithTraceFetcher:
    """Fetches and caches agent traces from LangSmith."""

    def __init__(self, project_name: str = "browser-agent"):
        self.client = Client()  # LangSmith client
        self.project_name = project_name
        self.cache_dir = Path(".browser-agent/traces")

    async def fetch_recent_traces(
        self,
        hours: int = 24,
        filter_tags: list[str] = None,
        min_feedback_score: float = 0.7
    ) -> list[dict]:
        """Fetch successful traces from last N hours.

        Args:
            hours: Look back period
            filter_tags: Only fetch traces with these tags
            min_feedback_score: Minimum user feedback score (0-1)
        """
        end = datetime.now()
        start = end - timedelta(hours=hours)

        runs = self.client.list_runs(
            project_name=self.project_name,
            start_time=start,
            filter='and(eq(status, "success"), gt(feedback_score, 0.7))'
        )

        traces = []
        for run in runs:
            # Cache locally to avoid repeated API calls
            trace_path = self.cache_dir / f"{run.id}.json"
            if not trace_path.exists():
                trace_data = self._extract_trace_data(run)
                trace_path.write_text(json.dumps(trace_data, indent=2))
            else:
                trace_data = json.loads(trace_path.read_text())
            traces.append(trace_data)

        return traces

    def _extract_trace_data(self, run) -> dict:
        """Extract relevant data from LangSmith run."""
        return {
            "run_id": str(run.id),
            "task": run.inputs.get("task", ""),
            "steps": self._extract_steps(run),
            "success": run.status == "success",
            "feedback_score": run.feedback_stats.get("score", 0),
            "duration_ms": run.execution_order,
            "timestamp": run.start_time.isoformat(),
            "tags": run.tags or [],
        }
```

**1.2 Session Diary Entries**

Similar to Claude Code's `/diary` command, capture session experiences:

```python
class SessionDiary:
    """Records session experiences for later reflection."""

    def __init__(self, diary_dir: Path = Path(".browser-agent/memory/diary")):
        self.diary_dir = diary_dir
        self.diary_dir.mkdir(parents=True, exist_ok=True)
        self.processed_log = diary_dir / "processed.log"

    async def create_entry(
        self,
        session_id: str,
        accomplishments: list[str],
        challenges: list[str],
        design_decisions: dict,
        user_feedback: str = None
    ):
        """Create a diary entry from session experience.

        Called automatically on session end or via explicit /diary command.
        """
        entry_file = self.diary_dir / f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        content = f"""# Session Diary Entry

**Session ID**: {session_id}
**Date**: {datetime.now().isoformat()}

## Accomplishments
{self._format_list(accomplishments)}

## Challenges Encountered
{self._format_list(challenges)}

## Design Decisions
{self._format_dict(design_decisions)}

## User Feedback
{user_feedback or "None provided"}

## Tags
{self._extract_tags(accomplishments, challenges)}
"""
        entry_file.write_text(content)
        return entry_file

    def get_unprocessed_entries(self) -> list[Path]:
        """Get diary entries that haven't been reflected upon."""
        processed = set()
        if self.processed_log.exists():
            processed = set(self.processed_log.read_text().splitlines())

        all_entries = list(self.diary_dir.glob("*.md"))
        return [e for e in all_entries if str(e) not in processed]

    def mark_processed(self, entry_path: Path):
        """Mark entry as processed to avoid re-analysis."""
        with self.processed_log.open("a") as f:
            f.write(f"{entry_path}\n")
```

### Part 2: Procedural Memory (Distilled Knowledge)

**2.1 AGENTS.md Memory File**

Project-level and user-level memory following Claude diary pattern:

```markdown
# Browser Agent Memory

Last updated: 2026-01-19

## Learned Best Practices

### Anti-Bot Strategies
- Save cookies after successful login, reuse in subsequent sessions to avoid re-triggering CAPTCHA
- For CAPTCHAs: Use multi-layered approach (DOM → Visual → Human)

### Domain-Specific Patterns

#### google.com
- CAPTCHA trigger: Missing cookies or suspicious activity
- Success pattern: Restore cookies → navigate
- Cookie lifetime: 7 days

#### linkedin.com
- Session cookies expire after 24h
- May require CAPTCHA solving on suspicious activity

#### github.com
- No special anti-bot measures needed
- Standard navigation works reliably

## Common Failure Patterns

### Element Not Found
- **Cause**: Navigated without waiting for page load or element not visible
- **Fix**: Use `browser_wait` with appropriate conditions (element, text, or load state)

### Stale Element Reference
- **Cause**: Used @ref after DOM change
- **Fix**: Re-snapshot after any navigation or significant interaction

## Skill Prerequisites

### LinkedIn Login (linkedin_login.md)
- Requires: credentials (username, password)
- Credential source: .browser-agent/settings/credentials.json

### Payment Form Filling (payment_form.md)
- Requires: payment info (card number, CVV, expiry)
- Warning: Request human approval before filling payment fields
```

**2.2 User Preferences (Token-Limited)**

```python
class UserPreferencesManager:
    """Manages user preferences with strict token limits."""

    MAX_TOKENS = 2000  # Prevent context bloat

    def __init__(self):
        self.user_prefs_path = Path("~/.browser-agent/memory/USER_PREFERENCES.md").expanduser()
        self.project_prefs_path = Path(".browser-agent/memory/USER_PREFERENCES.md")

    async def load_preferences(self) -> str:
        """Load and merge user + project preferences.

        Returns truncated content if exceeds MAX_TOKENS.
        This is loaded into system prompt at session start.
        """
        user_prefs = self._load_file(self.user_prefs_path)
        project_prefs = self._load_file(self.project_prefs_path)

        merged = f"{user_prefs}\n\n{project_prefs}"

        # Token limit enforcement
        token_count = self._count_tokens(merged)
        if token_count > self.MAX_TOKENS:
            # Prioritize project > user, truncate oldest entries
            merged = self._truncate_to_limit(merged, self.MAX_TOKENS)

        return merged

    def _count_tokens(self, text: str) -> int:
        """Approximate token count (4 chars ≈ 1 token)."""
        return len(text) // 4
```

**2.3 Domain Knowledge Base**

Per-domain learned patterns stored as individual files:

```
.browser-agent/memory/domains/
├── google.com.md
├── linkedin.com.md
├── github.com.md
└── amazon.com.md
```

Each domain file contains:
- Anti-bot configurations
- Success patterns
- Common failure modes
- Timing requirements
- Cookie management strategies

### Part 3: Reflection & Analysis Engine

**3.1 Trajectory Analyzer**

```python
class TrajectoryAnalyzer:
    """Analyzes agent trajectories to extract learnings."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-5", temperature=0)  # or o4-mini

    async def analyze_trace(self, trace: dict) -> TrajectoryAnalysis:
        """Analyze a single trace for learnings.

        Identifies:
        - Successful patterns to replicate
        - Failure patterns to avoid
        - Domain-specific behaviors
        - Skill candidates
        """
        prompt = f"""Analyze this browser automation trace:

Task: {trace['task']}
Steps: {json.dumps(trace['steps'], indent=2)}
Success: {trace['success']}
Feedback Score: {trace['feedback_score']}

Extract:
1. **Success Patterns**: What worked well? Why?
2. **Failure Patterns**: What failed? Root cause?
3. **Domain Insights**: Site-specific behaviors (anti-bot, timing, etc.)
4. **Skill Candidate**: Is this repeatable? Can it be a skill?
5. **Rule Updates**: Suggested updates to AGENTS.md

Format as JSON:
{{
  "success_patterns": ["pattern1", "pattern2"],
  "failure_patterns": [{{ "issue": "...", "fix": "..." }}],
  "domain_insights": {{ "domain": "...", "insights": ["..."] }},
  "skill_candidate": {{ "name": "...", "description": "...", "commands": ["..."] }},
  "rule_updates": ["rule1", "rule2"]
}}
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        analysis = json.loads(response.content)

        return TrajectoryAnalysis(**analysis)
```

**3.2 Reflection Command (like Claude's /reflect)**

```python
class ReflectionEngine:
    """Reflects on diary entries and updates procedural memory."""

    def __init__(self):
        self.diary = SessionDiary()
        self.analyzer = TrajectoryAnalyzer()
        self.agents_md_path = Path(".browser-agent/memory/AGENTS.md")
        self.reflection_dir = Path(".browser-agent/memory/reflections")

    async def reflect(self, force: bool = False):
        """Analyze unprocessed diary entries and update AGENTS.md.

        Similar to Claude Code's /reflect command:
        1. Load unprocessed diary entries
        2. Analyze each entry against existing rules
        3. Identify violations, patterns, new learnings
        4. Update AGENTS.md with synthesized rules
        5. Mark entries as processed
        """
        entries = self.diary.get_unprocessed_entries()
        if not entries and not force:
            return "No unprocessed diary entries"

        current_rules = self.agents_md_path.read_text() if self.agents_md_path.exists() else ""

        all_insights = []
        for entry_path in entries:
            entry_content = entry_path.read_text()

            # Analyze entry
            analysis = await self._analyze_entry(entry_content, current_rules)
            all_insights.append(analysis)

            # Save individual reflection
            reflection_path = self.reflection_dir / f"{entry_path.stem}_reflection.md"
            reflection_path.write_text(self._format_reflection(analysis))

            # Mark processed
            self.diary.mark_processed(entry_path)

        # Synthesize all insights into rule updates
        updated_rules = await self._synthesize_rules(current_rules, all_insights)

        # Update AGENTS.md
        self.agents_md_path.write_text(updated_rules)

        return f"Reflected on {len(entries)} entries, updated AGENTS.md"

    async def _analyze_entry(self, entry: str, current_rules: str) -> dict:
        """Analyze diary entry against existing rules."""
        prompt = f"""Analyze this session diary entry against existing agent rules:

CURRENT RULES:
{current_rules}

DIARY ENTRY:
{entry}

Identify:
1. **Rule Violations**: Did the session violate any existing rules?
2. **Weak Guidelines**: Are any rules too vague or not enforced?
3. **New Patterns**: Any recurring patterns not captured in rules?
4. **Domain Knowledge**: Site-specific learnings to document?
5. **Skill Opportunities**: Repeatable workflows to extract as skills?

Return JSON with analysis.
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return json.loads(response.content)

    async def _synthesize_rules(self, current_rules: str, insights: list[dict]) -> str:
        """Synthesize insights into updated AGENTS.md content."""
        prompt = f"""Update agent memory rules based on reflection insights:

CURRENT RULES:
{current_rules}

INSIGHTS FROM SESSIONS:
{json.dumps(insights, indent=2)}

Generate updated AGENTS.md that:
1. Strengthens weak guidelines
2. Adds new patterns discovered
3. Documents domain-specific knowledge
4. Removes outdated rules
5. Maintains clear, actionable format

Keep token count under 5000.
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content
```

### Part 4: Skill Discovery & Auto-Generation

**4.1 Skill Generator from Successful Traces**

```python
class SkillGenerator:
    """Auto-generates skills from successful LangSmith traces."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-5", temperature=0)  # or o4-mini
        self.skills_dir = Path(".browser-agent/skills")
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    async def generate_skill_from_trace(
        self,
        trace: dict,
        trajectory_analysis: TrajectoryAnalysis
    ) -> Optional[Path]:
        """Generate skill from successful trace.

        Creates skill markdown file with:
        - YAML frontmatter (name, description, triggers, prerequisites)
        - Step-by-step commands
        - Example usage
        - Error handling patterns
        """
        if not trajectory_analysis.skill_candidate:
            return None

        skill_name = trajectory_analysis.skill_candidate["name"]

        # Check if skill already exists
        skill_path = self.skills_dir / f"{skill_name}.md"
        if skill_path.exists():
            return None  # Skip duplicates

        # Generate skill content
        skill_content = await self._generate_skill_content(
            trace,
            trajectory_analysis
        )

        # Save skill file
        skill_path.write_text(skill_content)

        # Queue for human review
        await self._queue_for_review(skill_path, trace)

        return skill_path

    async def _generate_skill_content(
        self,
        trace: dict,
        analysis: TrajectoryAnalysis
    ) -> str:
        """Generate skill markdown content from trace."""
        prompt = f"""Generate a skill file for browser automation:

TASK: {trace['task']}
STEPS: {json.dumps(trace['steps'], indent=2)}
ANALYSIS: {json.dumps(analysis.dict(), indent=2)}

Generate a skill markdown file following this template:

---
name: skill-name
description: What this skill does
triggers: When to use this skill
prerequisites: Required credentials or data
---

# Skill Name

## Purpose
[Brief description]

## Prerequisites
[List required credentials, data, or setup]

## Steps
[Step-by-step commands with agent-browser]

## Error Handling
[Common failures and recovery strategies]

## Example Usage
[Concrete example]

---

Return ONLY the markdown content.
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    async def _queue_for_review(self, skill_path: Path, trace: dict):
        """Queue skill for human review before activation."""
        review_queue = Path(".browser-agent/skills/pending_review.json")

        queue_data = []
        if review_queue.exists():
            queue_data = json.loads(review_queue.read_text())

        queue_data.append({
            "skill_path": str(skill_path),
            "trace_id": trace["run_id"],
            "created_at": datetime.now().isoformat(),
            "status": "pending_review"
        })

        review_queue.write_text(json.dumps(queue_data, indent=2))
```

### Part 5: Credential Management

**5.1 Encrypted Credential Vault**

```python
class CredentialVault:
    """Encrypted storage for credentials with human-in-the-loop access."""

    def __init__(self):
        self.vault_path = Path(".browser-agent/settings/credentials.json")
        self.encryption_key = self._get_or_create_key()

    def store_credential(
        self,
        service: str,
        username: str,
        password: str,
        metadata: dict = None
    ):
        """Store encrypted credential."""
        vault = self._load_vault()

        vault[service] = {
            "username": self._encrypt(username),
            "password": self._encrypt(password),
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }

        self._save_vault(vault)

    async def request_credential(
        self,
        service: str,
        reason: str
    ) -> Optional[dict]:
        """Request credential with human approval.

        Triggers HumanInTheLoop middleware for approval.
        """
        vault = self._load_vault()

        if service not in vault:
            # Trigger human request for new credential
            return await self._request_new_credential(service, reason)

        # Decrypt and return
        cred = vault[service]
        return {
            "username": self._decrypt(cred["username"]),
            "password": self._decrypt(cred["password"])
        }
```

### Part 6: Memory Loading into System Prompt

```python
class MemoryLoader:
    """Loads memory into system prompt at session start."""

    async def load_session_memory(self, thread_id: str) -> str:
        """Load relevant memory for session.

        Includes:
        1. User preferences (max 2000 tokens)
        2. Recent AGENTS.md rules
        3. Domain knowledge for expected sites
        4. Active skills
        """
        prefs_manager = UserPreferencesManager()
        agents_md = Path(".browser-agent/memory/AGENTS.md")

        memory_sections = []

        # User preferences
        prefs = await prefs_manager.load_preferences()
        memory_sections.append(f"## User Preferences\n{prefs}")

        # Agent memory
        if agents_md.exists():
            agents_content = agents_md.read_text()
            memory_sections.append(f"## Learned Patterns\n{agents_content}")

        # Combine and return
        full_memory = "\n\n".join(memory_sections)

        # Final token check
        token_count = len(full_memory) // 4
        if token_count > 8000:  # Reserve 8k tokens max for memory
            # Truncate oldest sections
            full_memory = self._truncate_memory(full_memory, 8000)

        return full_memory
```

---

## Summary of Memory & Learning Layer

**Episodic Memory:**
- LangSmith traces (cached locally)
- Session diary entries (manual or auto-generated)
- Raw experience logs

**Procedural Memory:**
- AGENTS.md (project + user level)
- USER_PREFERENCES.md (token-limited, loaded into prompt)
- Domain knowledge files (per-site patterns)
- Skills library (auto-generated + manual)

**Learning Mechanisms:**
1. **Trajectory Analysis**: Extract patterns from LangSmith traces
2. **Reflection**: Synthesize diary entries into rules (like Claude /reflect)
3. **Skill Discovery**: Auto-generate skills from successful traces
4. **Rule Evolution**: Continuously update AGENTS.md based on experiences

**Integration Points:**
- Memory loaded into system prompt at session start
- Reflection triggered on PreCompact hook (long sessions)
- Skills auto-generated from high-feedback traces (score > 0.7)
- Domain knowledge consulted before navigation

---

---

## Layer 4: Middleware Stack

**Design Principle:** Composable middleware layers that wrap the agent's execution flow, providing cross-cutting concerns like memory, approval workflows, logging, and browser-specific behaviors.

### Middleware Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Execution Flow                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Core DeepAgents Middleware                 │    │
│  │  - TodoListMiddleware                              │    │
│  │  - FilesystemMiddleware                            │    │
│  │  - SummarizationMiddleware                         │    │
│  │  - AnthropicPromptCachingMiddleware                │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │      Browser-Specific Middleware                   │    │
│  │  - BrowserSessionMiddleware                        │    │
│  │  - BrowserMemoryMiddleware                         │    │
│  │  - DomainAdapterMiddleware                         │    │
│  │  - AntiDetectionMiddleware                         │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │       Production Middleware                        │    │
│  │  - HumanApprovalMiddleware                         │    │
│  │  - HumanInTheLoopMiddleware                        │    │
│  │  - CredentialMiddleware                            │    │
│  │  - TrajectoryLoggingMiddleware                     │    │
│  │  - SkillDiscoveryMiddleware                        │    │
│  │  - ErrorRecoveryMiddleware                         │    │
│  │  - PerformanceMonitoringMiddleware                 │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│                  Agent Core (Model + Tools)                  │
└─────────────────────────────────────────────────────────────┘
```

### Middleware Lifecycle Hooks

Each middleware can implement these hooks:

```python
class AgentMiddleware:
    """Base class for all middleware."""

    # Execution start/end
    async def before_agent(self, state: AgentState, runtime: Runtime) -> dict | Command:
        """Called once at agent start. Setup, validation."""

    async def after_agent(self, state: AgentState, runtime: Runtime) -> dict | Command:
        """Called once at agent end. Cleanup, logging."""

    # Model call wrapping
    async def before_model(self, state: AgentState, runtime: Runtime) -> dict | Command:
        """Before each LLM call. Context preparation."""

    async def wrap_model_call(
        self,
        state: AgentState,
        runtime: Runtime,
        call_next: Callable
    ) -> ModelResponse:
        """Wraps LLM invocation. Modify request/response."""

    async def after_model(self, state: AgentState, runtime: Runtime) -> dict | Command:
        """After each LLM call. Post-processing."""

    # Tool call wrapping
    async def wrap_tool_call(
        self,
        state: AgentState,
        runtime: Runtime,
        tool_call: ToolCall,
        call_next: Callable
    ) -> ToolMessage:
        """Wraps tool execution. Approval, logging, error handling."""
```

### Part 1: Core DeepAgents Middleware (Use Existing)

These are provided by the deepagents library and should be used as-is:

**1.1 TodoListMiddleware**

```python
from langchain.agents.middleware import TodoListMiddleware

# Adds write_todos tool for task planning
todo_middleware = TodoListMiddleware()

# Agent automatically gets planning capabilities:
# - write_todos(todos: list[dict]) tool
# - System prompt with planning instructions
# - TodoItem state tracking
```

**1.2 FilesystemMiddleware**

```python
from deepagents.agent.middleware import FilesystemMiddleware
from deepagents.backend.filesystem import FilesystemBackend

# Adds filesystem tools: ls, read_file, write_file, edit_file
filesystem_backend = FilesystemBackend()
filesystem_middleware = FilesystemMiddleware(backend=filesystem_backend)

# Agent can offload context to files:
# - ls(path) - list directory contents
# - read_file(path) - read file contents
# - write_file(path, content) - write to file
# - edit_file(path, old_string, new_string) - edit file
```

**1.3 SummarizationMiddleware**

```python
from langchain.agents.middleware import SummarizationMiddleware

# Automatically summarizes conversation when token limit approached
summarization_middleware = SummarizationMiddleware(
    trigger={"tokens": 50000},  # Trigger at 50k tokens
    keep=10  # Keep last 10 messages
)

# Benefits:
# - Prevents context overflow
# - Maintains conversational continuity
# - Preserves AI/Tool message pairs
```

**1.4 AnthropicPromptCachingMiddleware**

```python
from langchain.agents.middleware import AnthropicPromptCachingMiddleware

# Optimizes Anthropic API usage by caching prompts
caching_middleware = AnthropicPromptCachingMiddleware()

# Benefits:
# - Reduces API costs
# - Speeds up repeated interactions
# - Automatic cache management
```

### Part 2: Browser-Specific Middleware (Custom)

**2.1 BrowserSessionMiddleware**

```python
class BrowserSessionMiddleware(AgentMiddleware):
    """Manages browser session lifecycle per thread."""

    def __init__(self):
        self.active_sessions: dict[str, BrowserSession] = {}
        self.session_timeout = 3600  # 1 hour

    async def before_agent(self, state: AgentState, runtime: Runtime) -> dict:
        """Initialize browser session for thread if needed."""
        thread_id = state.get("thread_id")

        if thread_id not in self.active_sessions:
            # Create new session
            session = await self._create_session(thread_id)
            self.active_sessions[thread_id] = session

            return {
                "browser_session": {
                    "sessionId": thread_id,
                    "streamUrl": session.stream_url,
                    "isActive": True
                }
            }

        return {}

    async def after_agent(self, state: AgentState, runtime: Runtime) -> dict:
        """Cleanup old sessions on timeout."""
        await self._cleanup_stale_sessions()
        return {}

    async def wrap_tool_call(
        self,
        state: AgentState,
        runtime: Runtime,
        tool_call: ToolCall,
        call_next: Callable
    ) -> ToolMessage:
        """Inject thread_id into browser tool calls."""
        if tool_call.name.startswith("browser_"):
            # Auto-inject thread_id if missing
            if "thread_id" not in tool_call.args:
                tool_call.args["thread_id"] = state["thread_id"]

        return await call_next(tool_call)
```

**2.2 BrowserMemoryMiddleware**

```python
class BrowserMemoryMiddleware(AgentMiddleware):
    """Loads browser-specific memory into context."""

    def __init__(self):
        self.memory_loader = MemoryLoader()

    async def before_agent(self, state: AgentState, runtime: Runtime) -> dict:
        """Load memory into system message."""
        thread_id = state["thread_id"]

        # Load user preferences, AGENTS.md, domain knowledge
        memory_content = await self.memory_loader.load_session_memory(thread_id)

        # Inject into system message
        messages = state.get("messages", [])
        if messages and messages[0].type == "system":
            # Append to existing system message
            messages[0].content += f"\n\n# Agent Memory\n{memory_content}"
        else:
            # Insert new system message
            messages.insert(0, SystemMessage(content=f"# Agent Memory\n{memory_content}"))

        return {"messages": messages}
```

**2.3 DomainAdapterMiddleware**

```python
class DomainAdapterMiddleware(AgentMiddleware):
    """Adapts agent behavior based on target domain."""

    def __init__(self):
        self.domains_dir = Path(".browser-agent/memory/domains")

    async def before_model(self, state: AgentState, runtime: Runtime) -> dict:
        """Inject domain-specific instructions before model call."""
        messages = state["messages"]

        # Extract target domain from recent messages
        target_domain = self._extract_target_domain(messages)

        if target_domain:
            domain_file = self.domains_dir / f"{target_domain}.md"
            if domain_file.exists():
                domain_knowledge = domain_file.read_text()

                # Inject as system message
                domain_msg = SystemMessage(
                    content=f"# Domain-Specific Knowledge: {target_domain}\n{domain_knowledge}"
                )
                messages.insert(-1, domain_msg)  # Before last user message

                return {"messages": messages}

        return {}

    def _extract_target_domain(self, messages: list[BaseMessage]) -> Optional[str]:
        """Extract domain from navigation commands in recent messages."""
        # Look for browser_navigate commands in tool calls
        # Extract domain from URLs
        # Return domain like "google.com", "linkedin.com"
        pass
```

**2.4 AntiDetectionMiddleware**

```python
class AntiDetectionMiddleware(AgentMiddleware):
    """Automatically applies anti-bot measures and handles CAPTCHA with multi-layered approach."""

    PROBLEMATIC_DOMAINS = ["google.com", "linkedin.com", "facebook.com"]

    def __init__(self):
        self.llm_with_vision = ChatOpenAI(
            model="gpt-5",  # Multimodal model (or o4-mini)
            temperature=0
        )

    async def wrap_tool_call(
        self,
        state: AgentState,
        runtime: Runtime,
        tool_call: ToolCall,
        call_next: Callable
    ) -> ToolMessage:
        """Inject anti-bot setup before navigation and handle CAPTCHA detection."""

        if tool_call.name == "browser_navigate":
            url = tool_call.args.get("url", "")
            domain = self._extract_domain(url)

            if domain in self.PROBLEMATIC_DOMAINS:
                thread_id = tool_call.args.get("thread_id")

                # Pre-configure anti-bot measures
                await self._apply_anti_bot_setup(thread_id)

        # Execute tool call
        result = await call_next(tool_call)

        # After execution, check for CAPTCHA
        if tool_call.name in ["browser_navigate", "browser_click", "browser_fill"]:
            captcha_detected = await self._detect_captcha(state)

            if captcha_detected:
                # Multi-layered CAPTCHA handling
                solved = await self._handle_captcha_multilayer(state)

                if not solved:
                    # Fall back to human help
                    raise NodeInterrupt(
                        "CAPTCHA detected and could not be solved automatically. Human assistance needed.",
                        captcha_help_requested=True
                    )

        return result

    async def _apply_anti_bot_setup(self, thread_id: str):
        """Apply anti-bot measures before navigation."""
        # Restore saved cookies if available
        await self._restore_domain_cookies(thread_id)

    async def _detect_captcha(self, state: AgentState) -> bool:
        """Detect CAPTCHA presence on page."""
        thread_id = state["thread_id"]

        # Check DOM for common CAPTCHA indicators
        captcha_selectors = [
            "iframe[src*='recaptcha']",
            "iframe[src*='hcaptcha']",
            ".g-recaptcha",
            "#captcha",
            "[class*='captcha']"
        ]

        for selector in captcha_selectors:
            result = await browser_get_info("count", thread_id, selector=selector)
            if result and int(result) > 0:
                return True

        return False

    async def _handle_captcha_multilayer(self, state: AgentState) -> bool:
        """Multi-layered CAPTCHA solving approach.

        1. Try DOM approach (accessibility tree analysis)
        2. Try visual approach (screenshot + vision model)
        3. If both fail, return False (triggers human help)
        """
        thread_id = state["thread_id"]

        # Layer 1: DOM approach
        dom_solved = await self._solve_captcha_dom(thread_id)
        if dom_solved:
            logger.info("CAPTCHA solved via DOM approach")
            return True

        # Layer 2: Visual approach (multimodal LLM)
        visual_solved = await self._solve_captcha_visual(state)
        if visual_solved:
            logger.info("CAPTCHA solved via visual approach")
            return True

        # Layer 3: Human help (handled by caller)
        logger.warning("CAPTCHA could not be solved automatically")
        return False

    async def _solve_captcha_dom(self, thread_id: str) -> bool:
        """Attempt to solve CAPTCHA using DOM approach.

        Works for:
        - Simple text CAPTCHAs
        - Checkbox CAPTCHAs ("I'm not a robot")
        - Audio CAPTCHAs with accessible controls
        """
        try:
            # Get snapshot to find CAPTCHA elements
            snapshot = await browser_snapshot(thread_id, interactive_only=True)

            # Look for checkbox-style CAPTCHAs
            checkbox_found = self._find_element_by_text(snapshot, "I'm not a robot")
            if checkbox_found:
                await browser_click(checkbox_found, thread_id)
                await browser_wait_time(2000, thread_id)
                return True

            # Look for audio CAPTCHA alternatives
            audio_button = self._find_element_by_text(snapshot, "Audio challenge")
            if audio_button:
                # Click audio challenge
                await browser_click(audio_button, thread_id)
                # Note: Audio solving would require speech-to-text
                # For now, just return False to try visual approach
                return False

            return False

        except Exception as e:
            logger.debug(f"DOM CAPTCHA solving failed: {e}")
            return False

    async def _solve_captcha_visual(self, state: AgentState) -> bool:
        """Attempt to solve CAPTCHA using visual approach with multimodal LLM.

        Takes screenshot of browser and sends to vision model for analysis.
        Works for:
        - Image-based CAPTCHAs (select all traffic lights, etc.)
        - Text CAPTCHAs rendered as images
        - Complex visual puzzles
        """
        thread_id = state["thread_id"]

        try:
            # Take screenshot of current page
            screenshot_path = f".browser-agent/temp/captcha_{thread_id}_{int(time.time())}.png"
            await browser_screenshot(thread_id, filename=screenshot_path)

            # Read screenshot as base64
            with open(screenshot_path, "rb") as f:
                screenshot_base64 = base64.b64encode(f.read()).decode()

            # Send to vision model for analysis
            response = await self.llm_with_vision.ainvoke([
                HumanMessage(
                    content=[
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this screenshot for CAPTCHA challenges.

If there is a CAPTCHA:
1. Identify the type (image selection, text entry, puzzle, etc.)
2. Provide step-by-step instructions to solve it using browser automation
3. Include specific @refs or selectors to click

Return JSON:
{
  "captcha_found": true/false,
  "captcha_type": "image_selection" | "text_entry" | "puzzle" | "none",
  "solution_steps": ["step 1", "step 2", ...],
  "elements_to_click": ["@e1", "@e2", ...],
  "text_to_enter": "answer if applicable"
}
"""
                        }
                    ]
                )
            ])

            analysis = json.loads(response.content)

            if not analysis["captcha_found"]:
                return False

            # Execute solution steps
            for step_desc in analysis["solution_steps"]:
                # Click elements
                for element_ref in analysis.get("elements_to_click", []):
                    await browser_click(element_ref, thread_id)
                    await browser_wait_time(500, thread_id)

                # Enter text if needed
                if analysis.get("text_to_enter"):
                    # Find input field (assume first input in snapshot)
                    snapshot = await browser_snapshot(thread_id, interactive_only=True)
                    input_ref = self._find_first_input(snapshot)
                    if input_ref:
                        await browser_fill(input_ref, analysis["text_to_enter"], thread_id)

            # Verify if CAPTCHA was solved (no longer present)
            await browser_wait_time(2000, thread_id)
            still_present = await self._detect_captcha(state)

            return not still_present

        except Exception as e:
            logger.debug(f"Visual CAPTCHA solving failed: {e}")
            return False
```

**CAPTCHA Handling Strategy:**

1. **Prevention First**: Restore saved cookies before navigation (cookie reuse from successful sessions)
2. **Detection**: Check DOM for common CAPTCHA indicators after navigation/interaction
3. **Multi-Layered Solving**:
   - **Layer 1 - DOM Approach**: Use accessibility tree to find and interact with CAPTCHA elements
     - Checkbox CAPTCHAs ("I'm not a robot")
     - Text-based CAPTCHAs accessible via DOM
   - **Layer 2 - Visual Approach**: Use multimodal LLM (GPT-5 or o4-mini) to analyze screenshot
     - Image selection CAPTCHAs (traffic lights, crosswalks, etc.)
     - Text CAPTCHAs rendered as images
     - Complex visual puzzles
   - **Layer 3 - Human Help**: If both automated approaches fail, trigger `HumanInTheLoopMiddleware`
4. **Learning**: Successful CAPTCHA solutions logged to LangSmith for future skill generation

### Part 3: Production Middleware (Custom)

**3.1 HumanApprovalMiddleware**

```python
class HumanApprovalMiddleware(AgentMiddleware):
    """Requests human approval for action tools."""

    APPROVAL_REQUIRED = [
        "browser_navigate", "browser_click", "browser_fill",
        "browser_type", "browser_press_key", "browser_eval"
    ]

    async def wrap_tool_call(
        self,
        state: AgentState,
        runtime: Runtime,
        tool_call: ToolCall,
        call_next: Callable
    ) -> ToolMessage:
        """Request approval before executing action tools."""

        if tool_call.name in self.APPROVAL_REQUIRED:
            # Create approval request
            approval_request = {
                "id": str(uuid.uuid4()),
                "command": tool_call.name,
                "args": tool_call.args,
                "requiresApproval": True
            }

            # Add to approval queue
            approval_queue = state.get("approval_queue", [])
            approval_queue.append(approval_request)

            # Trigger interrupt for user approval
            raise NodeInterrupt(
                f"Approval required for {tool_call.name}",
                approval_queue=approval_queue
            )

        return await call_next(tool_call)
```

**3.2 HumanInTheLoopMiddleware**

```python
class HumanInTheLoopMiddleware(AgentMiddleware):
    """Requests human intervention when agent is stuck."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_counts: dict[str, int] = {}

    async def after_model(self, state: AgentState, runtime: Runtime) -> dict | Command:
        """Detect stuck patterns and request human help."""
        messages = state["messages"]

        # Detect if agent is stuck (repeated errors, no progress)
        if self._is_stuck(messages):
            thread_id = state["thread_id"]
            self.retry_counts[thread_id] = self.retry_counts.get(thread_id, 0) + 1

            if self.retry_counts[thread_id] >= self.max_retries:
                # Request human intervention
                raise NodeInterrupt(
                    f"Agent stuck after {self.max_retries} retries. Human guidance needed.",
                    human_input_requested=True
                )
        else:
            # Reset retry count on success
            self.retry_counts.pop(state["thread_id"], None)

        return {}

    def _is_stuck(self, messages: list[BaseMessage]) -> bool:
        """Detect if agent is repeating same errors or actions."""
        # Check last 3 tool calls
        # If same tool failing repeatedly → stuck
        # If element not found repeatedly → stuck
        pass
```

**3.3 CredentialMiddleware**

```python
class CredentialMiddleware(AgentMiddleware):
    """Manages credential requests with human approval."""

    def __init__(self):
        self.credential_vault = CredentialVault()

    async def wrap_tool_call(
        self,
        state: AgentState,
        runtime: Runtime,
        tool_call: ToolCall,
        call_next: Callable
    ) -> ToolMessage:
        """Intercept credential requests."""

        # Check if tool call mentions "login", "password", "credentials"
        if self._requires_credentials(tool_call):
            # Extract service from context
            service = self._extract_service_from_context(state)

            # Request credential from vault (triggers human approval if not found)
            credential = await self.credential_vault.request_credential(
                service=service,
                reason=f"Needed for {tool_call.name}"
            )

            if credential:
                # Inject credential into tool args
                tool_call.args["username"] = credential["username"]
                tool_call.args["password"] = credential["password"]

        return await call_next(tool_call)
```

**3.4 TrajectoryLoggingMiddleware**

```python
class TrajectoryLoggingMiddleware(AgentMiddleware):
    """Logs agent trajectories to LangSmith for learning."""

    def __init__(self):
        self.langsmith_client = Client()
        self.current_trajectory: dict = {}

    async def before_agent(self, state: AgentState, runtime: Runtime) -> dict:
        """Initialize trajectory recording."""
        self.current_trajectory = {
            "thread_id": state["thread_id"],
            "task": self._extract_task(state),
            "steps": [],
            "start_time": datetime.now().isoformat()
        }
        return {}

    async def wrap_tool_call(
        self,
        state: AgentState,
        runtime: Runtime,
        tool_call: ToolCall,
        call_next: Callable
    ) -> ToolMessage:
        """Record each tool call in trajectory."""
        step_start = datetime.now()

        try:
            result = await call_next(tool_call)
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            # Record step
            self.current_trajectory["steps"].append({
                "tool": tool_call.name,
                "args": tool_call.args,
                "success": success,
                "error": error,
                "duration_ms": (datetime.now() - step_start).total_seconds() * 1000
            })

        return result

    async def after_agent(self, state: AgentState, runtime: Runtime) -> dict:
        """Save trajectory to LangSmith."""
        self.current_trajectory["end_time"] = datetime.now().isoformat()
        self.current_trajectory["success"] = self._determine_success(state)

        # Log to LangSmith
        await self._log_trajectory(self.current_trajectory)

        return {}
```

**3.5 SkillDiscoveryMiddleware**

```python
class SkillDiscoveryMiddleware(AgentMiddleware):
    """Automatically discovers skill candidates from successful trajectories."""

    def __init__(self):
        self.skill_generator = SkillGenerator()
        self.trajectory_analyzer = TrajectoryAnalyzer()

    async def after_agent(self, state: AgentState, runtime: Runtime) -> dict:
        """Analyze trajectory and generate skills if candidate found."""

        # Get trajectory from TrajectoryLoggingMiddleware
        trajectory = self._get_current_trajectory(state)

        # Check if trajectory was successful
        if trajectory.get("success") and len(trajectory["steps"]) >= 3:
            # Analyze for skill potential
            analysis = await self.trajectory_analyzer.analyze_trace(trajectory)

            if analysis.skill_candidate:
                # Generate skill (queued for human review)
                skill_path = await self.skill_generator.generate_skill_from_trace(
                    trajectory,
                    analysis
                )

                if skill_path:
                    logger.info(f"New skill candidate generated: {skill_path}")

        return {}
```

**3.6 ErrorRecoveryMiddleware**

```python
class ErrorRecoveryMiddleware(AgentMiddleware):
    """Provides automatic error recovery strategies."""

    async def wrap_tool_call(
        self,
        state: AgentState,
        runtime: Runtime,
        tool_call: ToolCall,
        call_next: Callable
    ) -> ToolMessage:
        """Wrap tool calls with error recovery."""

        max_retries = 3
        retry_delay = 1.0  # seconds

        for attempt in range(max_retries):
            try:
                result = await call_next(tool_call)
                return result

            except ElementNotFoundException as e:
                if attempt < max_retries - 1:
                    # Recovery: Re-snapshot and retry
                    logger.info(f"Element not found, re-snapshotting (attempt {attempt+1})")
                    await self._recovery_snapshot(state)
                    await asyncio.sleep(retry_delay)
                else:
                    raise

            except TimeoutException as e:
                if attempt < max_retries - 1:
                    # Recovery: Wait longer
                    logger.info(f"Timeout, extending wait (attempt {attempt+1})")
                    await asyncio.sleep(retry_delay * 2)
                else:
                    raise

    async def _recovery_snapshot(self, state: AgentState):
        """Take fresh snapshot for recovery."""
        thread_id = state["thread_id"]
        await browser_snapshot(thread_id, interactive_only=True)
```

**3.7 PerformanceMonitoringMiddleware**

```python
class PerformanceMonitoringMiddleware(AgentMiddleware):
    """Monitors agent performance metrics."""

    async def before_agent(self, state: AgentState, runtime: Runtime) -> dict:
        """Start performance tracking."""
        return {
            "perf_start_time": datetime.now().isoformat(),
            "perf_metrics": {
                "tool_calls": 0,
                "model_calls": 0,
                "errors": 0,
                "total_tokens": 0
            }
        }

    async def wrap_model_call(
        self,
        state: AgentState,
        runtime: Runtime,
        call_next: Callable
    ) -> ModelResponse:
        """Track model call metrics."""
        response = await call_next()

        # Update metrics
        metrics = state.get("perf_metrics", {})
        metrics["model_calls"] += 1
        metrics["total_tokens"] += response.usage.total_tokens

        return response

    async def wrap_tool_call(
        self,
        state: AgentState,
        runtime: Runtime,
        tool_call: ToolCall,
        call_next: Callable
    ) -> ToolMessage:
        """Track tool call metrics."""
        metrics = state.get("perf_metrics", {})
        metrics["tool_calls"] += 1

        try:
            return await call_next(tool_call)
        except Exception:
            metrics["errors"] += 1
            raise

    async def after_agent(self, state: AgentState, runtime: Runtime) -> dict:
        """Log performance metrics."""
        metrics = state.get("perf_metrics", {})
        duration = (
            datetime.fromisoformat(state.get("perf_start_time")) -
            datetime.now()
        ).total_seconds()

        logger.info(f"Performance: {metrics} in {duration:.2f}s")
        return {}
```

### Part 4: Middleware Composition

```python
def create_browser_agent_with_middleware(
    model: BaseChatModel,
    system_prompt: str,
    tools: list[BaseTool]
) -> CompiledStateGraph:
    """Create browser agent with full middleware stack."""

    # Initialize backends
    filesystem_backend = FilesystemBackend()

    # Core middleware (order matters for composition)
    middleware = [
        # 1. Core deepagents middleware
        TodoListMiddleware(),
        FilesystemMiddleware(backend=filesystem_backend),
        SummarizationMiddleware(trigger={"tokens": 50000}, keep=10),
        AnthropicPromptCachingMiddleware(),

        # 2. Browser-specific middleware
        BrowserSessionMiddleware(),
        BrowserMemoryMiddleware(),
        DomainAdapterMiddleware(),
        AntiDetectionMiddleware(),

        # 3. Production middleware
        PerformanceMonitoringMiddleware(),
        TrajectoryLoggingMiddleware(),
        CredentialMiddleware(),
        HumanApprovalMiddleware(),
        HumanInTheLoopMiddleware(max_retries=3),
        ErrorRecoveryMiddleware(),
        SkillDiscoveryMiddleware(),
    ]

    # Create agent with middleware
    agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools,
        middleware=middleware
    )

    return agent
```

---

## Summary of Middleware Stack

**Core DeepAgents Middleware (Use Existing):**
- TodoListMiddleware: Task planning with write_todos tool
- FilesystemMiddleware: File operations (ls, read, write, edit)
- SummarizationMiddleware: Automatic conversation summarization
- AnthropicPromptCachingMiddleware: Prompt caching optimization

**Browser-Specific Middleware (Custom):**
- BrowserSessionMiddleware: Session lifecycle per thread
- BrowserMemoryMiddleware: Load AGENTS.md, preferences into context
- DomainAdapterMiddleware: Inject domain knowledge before navigation
- AntiDetectionMiddleware: Auto-apply anti-bot measures

**Production Middleware (Custom):**
- HumanApprovalMiddleware: Approval workflow for action tools
- HumanInTheLoopMiddleware: Request help when stuck
- CredentialMiddleware: Manage credentials with human approval
- TrajectoryLoggingMiddleware: Log to LangSmith for learning
- SkillDiscoveryMiddleware: Auto-generate skills from success patterns
- ErrorRecoveryMiddleware: Automatic retry with recovery strategies
- PerformanceMonitoringMiddleware: Track metrics (calls, tokens, errors)

**Key Patterns:**
1. Middleware wraps agent execution with cross-cutting concerns
2. Hooks: before_agent, before_model, wrap_model_call, wrap_tool_call, after_agent
3. Can modify state, interrupt execution, or control flow
4. Composes naturally (outer middleware wraps inner)
5. Separation of concerns: session management, memory, approval, logging, recovery

**Multimodal Support Requirements:**

For CAPTCHA visual analysis and general multimodal capabilities:

1. **ChatOpenAI Configuration**: Support image inputs alongside text
   ```python
   llm = ChatOpenAI(
       model="gpt-5",  # Vision-capable model (or o4-mini)
       temperature=0
   )

   # Message format with images
   message = HumanMessage(
       content=[
           {
               "type": "image_url",
               "image_url": {"url": "data:image/png;base64,..."}
           },
           {
               "type": "text",
               "text": "Analyze this image"
           }
       ]
   )
   ```

2. **UI Image Upload**: Chat interface should support image attachments
   - Drag-and-drop image upload like Anthropic Claude UI
   - Paste images from clipboard
   - Camera capture on mobile devices
   - Image preview before sending
   - Support formats: PNG, JPEG, WebP, GIF
   - Max file size: 10MB per image
   - Display uploaded images in chat history

3. **State Management**: Add image support to AgentState
   ```python
   class AgentState(TypedDict):
       messages: List[BaseMessage]  # Can contain image content
       uploaded_images: Dict[str, str]  # image_id -> base64
       # ... other fields
   ```

4. **Use Cases**:
   - User uploads screenshot: "What's wrong with this page?"
   - Agent takes screenshot for CAPTCHA analysis
   - Agent sends browser viewport to user for feedback
   - User provides annotated images with instructions
   - Agent analyzes visual design for UI testing

---

---

## Layer 5: Skills System

**Design Principle:** Simple, open format for giving agents browser automation expertise. Skills are directories with SKILL.md files that load progressively into agent context. Based on Anthropic's agentskills pattern.

### Skills Architecture Overview - Progressive Disclosure

```
┌─────────────────────────────────────────────────────────────┐
│                 Progressive Disclosure Model                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Level 1: Session Start (System Prompt)                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │   Skill Metadata (name + description)              │    │
│  │   - All skills/*.md frontmatter                    │    │
│  │   - Lightweight: ~50-100 tokens per skill          │    │
│  │   - Agent knows WHAT skills exist                  │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│  Level 2: On-Demand (When Relevant)                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │   Full SKILL.md Content                            │    │
│  │   - Agent uses read_file tool                      │    │
│  │   - Loads when task matches skill description      │    │
│  │   - Contains: instructions, steps, examples        │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│  Level 3: As-Needed (Supporting Files)                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │   Referenced Resources                             │    │
│  │   - Agent uses read_file for specific files       │    │
│  │   - Examples: forms.md, reference.md, scripts/     │    │
│  │   - Only loads what's needed for current task     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Skill Auto-Generation                    │    │
│  │  - Extract from successful LangSmith traces        │    │
│  │  - SkillGenerator creates SKILL.md files           │    │
│  │  - Human reviews and activates                     │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Part 1: Skill File Structure

**1.1 Skill Directory Structure**

```
.browser-agent/skills/
├── google-search/
│   ├── SKILL.md                    # Main skill file (required)
│   ├── examples.md                 # Optional: usage examples
│   └── reference.md                # Optional: detailed reference
├── linkedin-login/
│   ├── SKILL.md
│   └── forms.md                    # Optional: form field reference
└── form-filling/
    └── SKILL.md
```

**1.2 SKILL.md Format (Simple, Anthropic Pattern)**

```markdown
---
name: google-search
description: Perform a Google search and extract top results. Use when user wants to search Google for information.
---

# Google Search Skill

Use this skill when the user wants to search Google for information.

## When to Use

- User asks to "search google for X"
- User says "google X" or "look up X on google"
- User wants current search results from Google

## How It Works

### Step 1: Restore Cookies (If Available)

Check for saved Google cookies to avoid CAPTCHA:
```bash
# Check if cookies exist for google.com
read_file(".browser-agent/memory/domains/google.com.md")
# If cookies saved, restore them
browser_cookies_set(saved_cookies, thread_id)
```

### Step 2: Navigate to Google

```bash
browser_navigate("https://www.google.com", thread_id)
browser_wait("element", thread_id, selector="textarea[name='q']")
```

### Step 3: Enter Search Query

```bash
browser_snapshot(thread_id, interactive_only=True)
# The search input is usually the first element (@e1)
browser_fill(@e1, query, thread_id)
browser_press("Enter", thread_id)
```

### Step 4: Wait for Results

```bash
browser_wait("load", thread_id, state="networkidle")
browser_snapshot(thread_id, interactive_only=True)
```

### Step 5: Extract Results

```bash
# Get titles (h3 elements)
titles = browser_get_info("text", thread_id, selector="h3")

# Get URLs (links)
urls = browser_get_info("attr", thread_id, selector="a", attr="href")

# Filter out non-result links (ads, navigation)
# Keep only URLs starting with "https://" that aren't google.com
```

### Step 6: Save Cookies for Future Use

```bash
cookies = browser_cookies_get(thread_id)
# Store in domain knowledge for next session
write_file(".browser-agent/memory/domains/google.com.md", cookie_data)
```

## Common Issues

### CAPTCHA Appears

If you see reCAPTCHA or "unusual traffic" message:
1. Check if CAPTCHA iframe exists: `browser_get_info("count", thread_id, selector="iframe[src*='recaptcha']")`
2. If CAPTCHA present, AntiDetectionMiddleware will handle automatically (DOM → Visual → Human fallback)
3. After solving, cookies are saved automatically

### Element Not Found

If search input (@e1) not found:
1. Take another snapshot: `browser_snapshot(thread_id, interactive_only=True)`
2. Wait 1 second: `browser_wait(1000, thread_id)`
3. Retry up to 3 times before requesting human help

### Rate Limiting

If Google shows "unusual traffic" message:
1. Save current cookies for future use
2. Wait 30 seconds
3. Try again with saved cookies
4. If persists, inform user Google has rate-limited the session

## Example Conversation

**User**: "Search Google for LangChain tutorials"

**Agent Thinking**: This matches the google-search skill. Let me use read_file to load the full skill instructions.

**Agent Actions**:
1. Read `.browser-agent/skills/google-search/SKILL.md`
2. Follow the steps in the skill
3. Extract search results
4. Return formatted results to user

**Agent Response**: "I found these LangChain tutorials from Google:
1. [Title] - [URL]
2. [Title] - [URL]
..."
```

### Part 2: Skill Loading at Session Start

**2.1 Progressive Disclosure - Level 1 (System Prompt)**

At session start, load all skill metadata into system prompt:

```python
class SkillLoader:
    """Loads skill metadata into system prompt at session start."""

    def __init__(self):
        self.skills_dir = Path(".browser-agent/skills")

    async def load_skill_metadata(self) -> str:
        """Load all SKILL.md frontmatter for system prompt.

        Returns lightweight description of available skills (~50-100 tokens each).
        Agent knows WHAT skills exist without loading full content.
        """
        skill_metadata = []

        # Scan all skills directories
        for skill_dir in self.skills_dir.glob("*/"):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            # Parse YAML frontmatter
            content = skill_file.read_text()
            if content.startswith("---"):
                frontmatter_end = content.find("---", 3)
                frontmatter = content[3:frontmatter_end].strip()

                # Extract name and description
                name = self._extract_yaml_field(frontmatter, "name")
                description = self._extract_yaml_field(frontmatter, "description")

                if name and description:
                    skill_metadata.append(f"- **{name}**: {description}")

        # Format for system prompt
        skills_section = "\n".join(skill_metadata)
        return f"""

## Available Skills

You have access to the following browser automation skills. When a task matches a skill's description, use the read_file tool to load the full skill instructions from `.browser-agent/skills/<skill-name>/SKILL.md`.

{skills_section}

To use a skill:
1. Recognize when user's request matches a skill description
2. Use read_file(".browser-agent/skills/<skill-name>/SKILL.md") to load full instructions
3. Follow the skill's step-by-step guidance
4. Load supporting files (examples.md, reference.md) as needed using read_file
"""
```

**2.2 System Prompt Integration**

```python
class BrowserMemoryMiddleware(AgentMiddleware):
    """Loads memory AND skill metadata into context at session start."""

    def __init__(self):
        self.memory_loader = MemoryLoader()
        self.skill_loader = SkillLoader()  # Add skill loader

    async def before_agent(self, state: AgentState, runtime: Runtime) -> dict:
        """Load memory + skill metadata into system message."""
        thread_id = state["thread_id"]

        # Load user preferences, AGENTS.md, domain knowledge
        memory_content = await self.memory_loader.load_session_memory(thread_id)

        # Load skill metadata (Level 1 - Progressive Disclosure)
        skills_metadata = await self.skill_loader.load_skill_metadata()

        # Inject into system message
        messages = state.get("messages", [])
        if messages and messages[0].type == "system":
            messages[0].content += f"\n\n# Agent Memory\n{memory_content}"
            messages[0].content += f"\n\n{skills_metadata}"  # Add skills
        else:
            system_content = f"# Agent Memory\n{memory_content}\n\n{skills_metadata}"
            messages.insert(0, SystemMessage(content=system_content))

        return {"messages": messages}
```

**2.3 On-Demand Loading (Level 2 - Agent Exercises Judgment)**

Agent automatically loads full SKILL.md when relevant:

```markdown
**User**: "Search Google for LangChain tutorials"

**Agent Internal Reasoning**: 
This matches the `google-search` skill description. Let me load the full instructions.

**Agent Tool Call**:
read_file(".browser-agent/skills/google-search/SKILL.md")

**Agent Internal State**:
Now I have the full skill instructions. I'll follow the steps:
1. Restore cookies if available
2. Navigate to Google
3. Enter search query
4. Extract results
5. Save cookies

**Agent Executes Skill Steps**:
[Follows SKILL.md instructions using browser tools]
```

Agent may also load supporting files as needed:

```python
# If skill references examples.md, agent loads it
read_file(".browser-agent/skills/google-search/examples.md")

# If skill references forms.md for field mappings
read_file(".browser-agent/skills/linkedin-login/forms.md")
```

### Part 3: Skill Auto-Generation (from LangSmith Traces)

**3.1 Simplified SkillGenerator**

```python
class SkillGenerator:
    """Auto-generates SKILL.md files from successful traces."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-5", temperature=0)  # or o4-mini
        self.skills_dir = Path(".browser-agent/skills")

    async def generate_skill_from_trace(
        self,
        trace: dict,
        analysis: TrajectoryAnalysis
    ) -> Optional[Path]:
        """Generate SKILL.md from successful trace.

        Simple workflow:
        1. LLM analyzes trace and creates SKILL.md content
        2. Save to skills/<skill-name>/SKILL.md
        3. Human reviews and activates (moves from draft/ to main skills/)
        """
        if not analysis.skill_candidate:
            return None

        skill_name = analysis.skill_candidate["name"]
        skill_dir = self.skills_dir / "drafts" / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Generate SKILL.md content using LLM
        skill_content = await self._generate_skill_content(trace, analysis)

        # Save to draft
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(skill_content)

        logger.info(f"Generated skill draft: {skill_path}")
        return skill_path

    async def _generate_skill_content(
        self,
        trace: dict,
        analysis: TrajectoryAnalysis
    ) -> str:
        """Use LLM to generate SKILL.md from trace."""
        prompt = f"""Generate a SKILL.md file for this browser automation workflow:

TASK: {trace['task']}
STEPS TAKEN: {json.dumps(trace['steps'], indent=2)}
SUCCESS: {trace['success']}

Create a SKILL.md file following this format:

---
name: skill-name (kebab-case)
description: Brief description (one sentence). Use when [trigger condition].
---

# Skill Name

Use this skill when [describe when to use].

## When to Use

- Bullet point triggers
- When user asks for X
- When task involves Y

## How It Works

### Step 1: [Step Name]

Description of what this step does.

```bash
# Browser commands
browser_command(args, thread_id)
```

### Step 2: [Next Step]

... (continue for all steps)

## Common Issues

### Issue Name

Description and solution.

## Example Conversation

Show how agent would use this skill.

---

Generate ONLY the SKILL.md content, following the format exactly.
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content
```

**3.2 Human Review & Activation**

Simple workflow:
1. Skills generated to `.browser-agent/skills/drafts/`
2. Human reviews SKILL.md file
3. If approved: `mv drafts/<skill-name> .browser-agent/skills/<skill-name>`
4. Skill now loads automatically at next session start

Optional CLI command:
```bash
# List draft skills
ls .browser-agent/skills/drafts/

# Review a skill
cat .browser-agent/skills/drafts/google-search/SKILL.md

# Activate a skill
mv .browser-agent/skills/drafts/google-search .browser-agent/skills/

# Or reject a skill
rm -rf .browser-agent/skills/drafts/google-search
```

---

## Summary of Skills System (Simplified)

**Progressive Disclosure Architecture:**
- **Level 1 (Session Start)**: Load skill metadata (name + description) into system prompt (~50-100 tokens/skill)
- **Level 2 (On-Demand)**: Agent loads full SKILL.md when task matches description via read_file tool
- **Level 3 (As-Needed)**: Agent loads supporting files (examples.md, reference.md) via read_file as needed

**Skill File Structure:**
- Simple YAML frontmatter: `name`, `description` (required)
- Markdown content: When to Use, How It Works (steps), Common Issues, Example Conversation
- Optional supporting files: examples.md, reference.md, forms.md, scripts/

**Skill Auto-Generation:**
- SkillDiscoveryMiddleware triggers after successful runs (feedback score > 0.7)
- SkillGenerator uses LLM (GPT-5/o4-mini) to create SKILL.md from trace
- Saves to `.browser-agent/skills/drafts/`
- Human reviews and activates (simple file move)

**No Complex Features (Deferred):**
- ❌ Sandbox testing framework (too advanced for this round)
- ❌ Version management system (too advanced for this round)
- ❌ Automated activation workflows (manual review sufficient)
- ✅ Simple file-based skills that load into filesystem and prompts
- ✅ Agent exercises judgment on when to load which skills

**Integration:**
- Skills loaded via BrowserMemoryMiddleware at session start (Level 1)
- Agent uses FilesystemMiddleware tools (read_file) to load full skills (Level 2+)
- SkillDiscoveryMiddleware generates new skills from successful traces
- Skills work seamlessly with Memory Layer (domain knowledge) and Tool Layer (browser commands)

---

## Layer 6: Agent & UI Layer

### Part 1: ChatOpenAI Configuration with Reasoning Display

**1.1 Backend: ChatOpenAI Setup (replacing AzureChatOpenAI)**

Update `browser_use_agent/configuration.py`:

```python
"""Configuration for browser automation agent."""

import os
from typing import Optional, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

class Config:
    """Configuration settings for browser automation agent."""

    # LLM Configuration
    MODEL_NAME: str = os.getenv("DEPLOYMENT_NAME", "gpt-5")  # gpt-5 or o4-mini
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "1.0"))

    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")

    # Reasoning Configuration
    REASONING_EFFORT: Literal["low", "medium", "high"] = "medium"
    REASONING_SUMMARY: Literal["auto", "brief", "detailed"] = "detailed"

    # Stream Configuration
    STREAM_ENABLED: bool = True
    BASE_STREAM_PORT: int = 9223
    MAX_PORT_OFFSET: int = 100

    # Tool Approval Configuration
    AUTO_APPROVED_TOOLS: list[str] = [
        "browser_snapshot",
        "browser_screenshot",
        "browser_get_info",
        "browser_is_visible",
        "browser_is_enabled",
        "browser_get_url",
        "browser_get_title",
        "browser_cookies_get",
        "browser_wait_time",
        "browser_console_messages",
    ]

    APPROVAL_REQUIRED_TOOLS: list[str] = [
        "browser_open",
        "browser_click",
        "browser_fill",
        "browser_type",
        "browser_press_key",
        "browser_eval",
        "browser_hover",
        "browser_drag",
        "browser_select_option",
        "browser_file_upload",
        "browser_cookies_set",
        "browser_set_headers",
    ]

def create_llm(
    stream: bool = True,
    enable_reasoning: bool = True,
    reasoning_effort: Literal["low", "medium", "high"] = "medium",
    temperature: float = 1.0,
) -> ChatOpenAI:
    """Create ChatOpenAI instance with reasoning support.

    Args:
        stream: Enable streaming responses
        enable_reasoning: Enable reasoning display (extended thinking)
        reasoning_effort: Reasoning effort level (low/medium/high)
        temperature: Sampling temperature

    Returns:
        ChatOpenAI: Configured LLM instance
    """
    # Construct v1 API endpoint for Azure
    base_url = f"{Config.AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1/"

    llm_config = {
        "model": Config.MODEL_NAME,
        "api_key": Config.AZURE_OPENAI_API_KEY,
        "base_url": base_url,
        "default_headers": {"api-key": Config.AZURE_OPENAI_API_KEY},
        "temperature": temperature,
        "streaming": stream,
    }

    # Enable reasoning (extended thinking) if requested
    if enable_reasoning:
        llm_config["use_responses_api"] = True
        llm_config["reasoning"] = {
            "effort": reasoning_effort,
            "summary": Config.REASONING_SUMMARY,
        }
        llm_config["include"] = ["reasoning.encrypted_content"]

    return ChatOpenAI(**llm_config)
```

**1.2 Agent Integration**

Update `browser_use_agent/browser_agent.py` to use new LLM:

```python
from browser_use_agent.configuration import create_llm
from deepagents import create_deep_agent

def create_browser_agent(
    tools: list,
    system_prompt: str,
    enable_reasoning: bool = True,
    reasoning_effort: str = "medium",
):
    """Create browser automation agent with reasoning support.

    Args:
        tools: List of tools for the agent
        system_prompt: System prompt for the agent
        enable_reasoning: Enable reasoning display
        reasoning_effort: Reasoning effort level (low/medium/high)

    Returns:
        Deep agent with reasoning capabilities
    """
    llm = create_llm(
        stream=True,
        enable_reasoning=enable_reasoning,
        reasoning_effort=reasoning_effort,
    )

    return create_deep_agent(
        llm=llm,
        tools=tools,
        system_message=system_prompt,
        # Middleware added via deepagents patterns (documented in Layer 4)
    )
```

**1.3 State Schema Enhancement**

Update `browser_use_agent/state.py` to include reasoning content:

```python
from typing import TypedDict, List, Dict, Optional, Any
from langchain_core.messages import BaseMessage

class ReasoningContent(TypedDict, total=False):
    """Reasoning content from ChatOpenAI."""
    summary: str  # Summary of reasoning process
    encrypted_content: str  # Encrypted full reasoning (for audit/debugging)
    timestamp: int
    isComplete: bool

class AgentState(TypedDict, total=False):
    """State for the browser automation agent."""
    messages: List[BaseMessage]
    todos: List[TodoItem]
    files: Dict[str, str]
    browser_session: Optional[BrowserSession]
    approval_queue: List[BrowserCommand]
    current_thought: Optional[ThoughtProcess]  # Keep for backward compat
    current_reasoning: Optional[ReasoningContent]  # New: reasoning from ChatOpenAI
    thread_id: str
    uploaded_images: List[Dict[str, Any]]  # New: multimodal support
```

**1.4 Streaming Reasoning to Frontend**

Update agent streaming logic to extract reasoning chunks:

```python
async def stream_agent_response(
    agent,
    state: AgentState,
    config: dict,
):
    """Stream agent response with reasoning content.

    Yields state updates including:
    - reasoning chunks (current_reasoning)
    - message chunks
    - tool calls
    - todos updates
    """
    async for chunk in agent.astream(state, config, stream_mode="values"):
        # Extract reasoning from chunk if available
        if "messages" in chunk and len(chunk["messages"]) > 0:
            last_message = chunk["messages"][-1]

            # Check for reasoning in additional_kwargs
            if hasattr(last_message, "additional_kwargs") and "reasoning" in last_message.additional_kwargs:
                reasoning_data = last_message.additional_kwargs["reasoning"]

                # Extract summary (may be list of content blocks in 2026 SDKs)
                summary = reasoning_data.get("summary", "")
                if isinstance(summary, list) and len(summary) > 0:
                    summary = summary[0].get("text", "")

                # Update current_reasoning in state
                chunk["current_reasoning"] = {
                    "summary": summary,
                    "encrypted_content": reasoning_data.get("encrypted_content", ""),
                    "timestamp": int(time.time() * 1000),
                    "isComplete": False,
                }

        yield chunk
```

### Part 2: Frontend - Reasoning Display

**2.1 Types Enhancement**

Update `deep-agents-ui/src/app/types/types.ts`:

```typescript
export interface ReasoningContent {
  summary: string;
  encrypted_content?: string;
  timestamp: number;
  isComplete: boolean;
}

export interface AgentState {
  messages: Message[];
  todos: TodoItem[];
  files: Record<string, string>;
  browser_session?: BrowserSession;
  approval_queue?: BrowserCommand[];
  current_thought?: ThoughtProcess;
  current_reasoning?: ReasoningContent;  // New
  thread_id: string;
  uploaded_images?: ImageUpload[];  // New
}

export interface ImageUpload {
  id: string;
  data: string;  // base64 data URL
  mimeType: string;
  name: string;
  size: number;
  uploadedAt: number;
}
```

**2.2 ReasoningDisplay Component**

Create `deep-agents-ui/src/app/components/ReasoningDisplay.tsx`:

```typescript
"use client";

import React, { useState, useEffect, useCallback } from "react";
import { ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ReasoningContent } from "@/app/types/types";

interface ReasoningDisplayProps {
  reasoning: ReasoningContent;
  isStreaming?: boolean;
  isExpanded?: boolean;
}

function BlinkingCursor() {
  return (
    <span className="inline-block w-1.5 h-4 bg-primary/60 ml-0.5 animate-pulse" />
  );
}

function streamText(
  text: string,
  setter: (value: string) => void,
  onComplete?: () => void
) {
  let index = 0;
  const interval = setInterval(() => {
    if (index < text.length) {
      setter(text.slice(0, index + 1));
      index++;
    } else {
      clearInterval(interval);
      onComplete?.();
    }
  }, 10); // 10ms per character

  return () => clearInterval(interval);
}

function generatePreview(summary: string, maxLength: number = 80): string {
  if (!summary || summary.trim() === "") {
    return "Thinking...";
  }

  const cleaned = summary.trim();
  if (cleaned.length <= maxLength) {
    return cleaned;
  }

  return cleaned.slice(0, maxLength - 3) + "...";
}

export function ReasoningDisplay({
  reasoning,
  isStreaming = false,
  isExpanded = false,
}: ReasoningDisplayProps) {
  const [expanded, setExpanded] = useState(isExpanded);
  const [displayedSummary, setDisplayedSummary] = useState("");
  const [streamComplete, setStreamComplete] = useState(!isStreaming);
  const [preview, setPreview] = useState("");

  useEffect(() => {
    if (isStreaming && reasoning.summary) {
      const cleanup = streamText(
        reasoning.summary,
        (text) => {
          setDisplayedSummary(text);
          setPreview(generatePreview(text));
        },
        () => setStreamComplete(true)
      );
      return cleanup;
    } else {
      setDisplayedSummary(reasoning.summary);
      setStreamComplete(true);
      setPreview(generatePreview(reasoning.summary));
    }
  }, [reasoning.summary, isStreaming]);

  const toggleExpanded = useCallback(() => {
    setExpanded((prev) => !prev);
  }, []);

  if (!reasoning.summary) {
    return null;
  }

  return (
    <div
      className={cn(
        "w-full overflow-hidden rounded-lg border border-primary/20 transition-all duration-200",
        expanded ? "bg-primary/5" : "hover:bg-primary/5"
      )}
    >
      <Button
        variant="ghost"
        size="sm"
        onClick={toggleExpanded}
        className={cn(
          "flex w-full items-center justify-between gap-2 px-3 py-2.5 text-left",
          "border-none shadow-none outline-none focus-visible:ring-0",
          "cursor-pointer"
        )}
      >
        <div className="flex w-full items-center gap-2 min-w-0">
          <div className="flex items-center gap-2 flex-shrink-0">
            <Sparkles size={14} className="text-primary" />
            <span className="text-[15px] font-medium tracking-[-0.6px] text-foreground">
              Reasoning
            </span>
          </div>
          {!expanded && preview && (
            <span className="text-sm text-muted-foreground truncate flex-1 min-w-0 italic">
              {preview}
            </span>
          )}
          <div className="flex-shrink-0 ml-auto">
            {expanded ? (
              <ChevronUp size={14} className="text-muted-foreground" />
            ) : (
              <ChevronDown size={14} className="text-muted-foreground" />
            )}
          </div>
        </div>
      </Button>

      {expanded && (
        <div className="px-4 pb-4 pt-1">
          <div className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {displayedSummary}
            {isStreaming && !streamComplete && <BlinkingCursor />}
          </div>
        </div>
      )}
    </div>
  );
}
```

**2.3 ChatMessage Integration**

Update `deep-agents-ui/src/app/components/ChatMessage.tsx` to display reasoning:

```typescript
import { ReasoningDisplay } from "@/app/components/ReasoningDisplay";

export function ChatMessage({ message, reasoning }: ChatMessageProps) {
  return (
    <div className="space-y-3">
      {/* Show reasoning if available (before message content) */}
      {reasoning && (
        <ReasoningDisplay
          reasoning={reasoning}
          isStreaming={!reasoning.isComplete}
          isExpanded={false}
        />
      )}

      {/* Message content */}
      <div className="prose prose-sm max-w-none">
        {message.content}
      </div>

      {/* Tool calls, etc. */}
    </div>
  );
}
```

### Part 3: Enhanced Browser Preview Session Management

**3.1 Session Visibility Logic**

Update `deep-agents-ui/src/app/components/BrowserPanel.tsx`:

```typescript
"use client";

import { useEffect, useState } from "react";
import { BrowserPreview } from "@/app/components/BrowserPreview";
import { useChatContext } from "@/providers/ChatProvider";
import { Monitor, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function BrowserPanel() {
  const { browserSession, messages } = useChatContext();
  const [isVisible, setIsVisible] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  // Auto-show logic: Show panel when browser session becomes active
  useEffect(() => {
    if (browserSession?.isActive && browserSession?.streamUrl) {
      setIsVisible(true);
      setIsMinimized(false);
    }
  }, [browserSession?.isActive, browserSession?.streamUrl]);

  // Auto-hide logic: Hide panel when browser session closes
  useEffect(() => {
    if (!browserSession?.isActive && isVisible) {
      // Delay hiding to allow user to see final state
      const timer = setTimeout(() => {
        setIsVisible(false);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [browserSession?.isActive, isVisible]);

  // Don't render if no session exists
  if (!browserSession?.streamUrl) {
    return null;
  }

  return (
    <div
      className={cn(
        "fixed right-0 top-0 h-full transition-all duration-300 ease-in-out",
        "bg-background border-l border-border shadow-lg z-50",
        isVisible ? "w-[400px]" : "w-0 overflow-hidden",
        isMinimized && "w-12"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-muted/30">
        <div className="flex items-center gap-2">
          <Monitor size={16} className="text-muted-foreground" />
          <span className="text-sm font-medium">Browser Preview</span>
          {browserSession.isActive && (
            <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setIsMinimized(!isMinimized)}
          >
            {isMinimized ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setIsVisible(false)}
          >
            <X size={14} />
          </Button>
        </div>
      </div>

      {/* Browser viewport */}
      {!isMinimized && (
        <div className="h-[calc(100%-48px)] overflow-hidden">
          <BrowserPreview
            streamUrl={browserSession.streamUrl}
            sessionId={browserSession.sessionId}
          />
        </div>
      )}
    </div>
  );
}
```

**3.2 Session Management Rules**

Browser preview visibility logic:

1. **Show panel when**:
   - Browser session becomes active (first `browser_open` command)
   - User manually opens preview from toolbar

2. **Keep panel visible when**:
   - Browser session is active
   - Agent is performing browser interactions
   - User has manually opened the panel

3. **Hide panel when**:
   - Browser session closes (`browser_close` command)
   - User manually closes preview
   - Session remains inactive for > 30 seconds

4. **Auto-minimize when**:
   - Browser session is active but agent is not performing browser actions for > 10 seconds
   - User switches to another thread (keep session alive but minimize)

### Part 4: Image Upload Support (Multimodal)

**4.1 ImageUpload Component**

Create `deep-agents-ui/src/app/components/ImageUpload.tsx`:

```typescript
"use client";

import React, { useState, useRef, useCallback } from "react";
import { Upload, X, Image as ImageIcon, Camera } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ImageUpload } from "@/app/types/types";

interface ImageUploadProps {
  images: ImageUpload[];
  onImagesChange: (images: ImageUpload[]) => void;
  maxImages?: number;
  maxSizeMB?: number;
}

export function ImageUploadComponent({
  images,
  onImagesChange,
  maxImages = 5,
  maxSizeMB = 10,
}: ImageUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const processFiles = useCallback(
    async (files: FileList | File[]) => {
      const fileArray = Array.from(files);
      const maxSize = maxSizeMB * 1024 * 1024;

      const newImages: ImageUpload[] = [];

      for (const file of fileArray) {
        // Check file type
        if (!file.type.startsWith("image/")) {
          alert(`${file.name} is not an image file`);
          continue;
        }

        // Check file size
        if (file.size > maxSize) {
          alert(`${file.name} exceeds ${maxSizeMB}MB limit`);
          continue;
        }

        // Check total count
        if (images.length + newImages.length >= maxImages) {
          alert(`Maximum ${maxImages} images allowed`);
          break;
        }

        // Convert to base64
        const reader = new FileReader();
        const dataUrl = await new Promise<string>((resolve) => {
          reader.onload = (e) => resolve(e.target?.result as string);
          reader.readAsDataURL(file);
        });

        newImages.push({
          id: `${Date.now()}-${Math.random()}`,
          data: dataUrl,
          mimeType: file.type,
          name: file.name,
          size: file.size,
          uploadedAt: Date.now(),
        });
      }

      if (newImages.length > 0) {
        onImagesChange([...images, ...newImages]);
      }
    },
    [images, maxImages, maxSizeMB, onImagesChange]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        processFiles(e.target.files);
        e.target.value = ""; // Reset input
      }
    },
    [processFiles]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        processFiles(e.dataTransfer.files);
      }
    },
    [processFiles]
  );

  const handlePaste = useCallback(
    (e: ClipboardEvent) => {
      if (e.clipboardData?.files && e.clipboardData.files.length > 0) {
        processFiles(e.clipboardData.files);
      }
    },
    [processFiles]
  );

  const removeImage = useCallback(
    (id: string) => {
      onImagesChange(images.filter((img) => img.id !== id));
    },
    [images, onImagesChange]
  );

  // Add paste listener
  useEffect(() => {
    document.addEventListener("paste", handlePaste);
    return () => document.removeEventListener("paste", handlePaste);
  }, [handlePaste]);

  return (
    <div className="space-y-2">
      {/* Image thumbnails */}
      {images.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {images.map((image) => (
            <div
              key={image.id}
              className="relative w-20 h-20 rounded-md overflow-hidden border border-border group"
            >
              <img
                src={image.data}
                alt={image.name}
                className="w-full h-full object-cover"
              />
              <button
                onClick={() => removeImage(image.id)}
                className="absolute top-1 right-1 bg-destructive/90 text-destructive-foreground rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Upload area */}
      {images.length < maxImages && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "border-2 border-dashed rounded-lg p-4 transition-colors",
            isDragging
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/50"
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              className="gap-2"
            >
              <ImageIcon size={16} />
              Choose files
            </Button>
            <span className="text-xs text-muted-foreground">
              or drag & drop, or paste
            </span>
          </div>
          <p className="text-xs text-center text-muted-foreground mt-2">
            Up to {maxImages} images, {maxSizeMB}MB each
          </p>
        </div>
      )}
    </div>
  );
}
```

**4.2 ChatInterface Integration**

Update `deep-agents-ui/src/app/components/ChatInterface.tsx`:

```typescript
import { ImageUploadComponent } from "@/app/components/ImageUpload";
import type { ImageUpload } from "@/app/types/types";

export function ChatInterface({ assistant }: ChatInterfaceProps) {
  const [uploadedImages, setUploadedImages] = useState<ImageUpload[]>([]);

  // ... existing code ...

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      if (!input.trim() && uploadedImages.length === 0) return;

      // Send message with images
      await sendMessage(input, uploadedImages);

      // Clear input and images
      setInput("");
      setUploadedImages([]);
    },
    [input, uploadedImages, sendMessage]
  );

  return (
    <div className="flex flex-col h-full">
      {/* ... messages ... */}

      {/* Input area */}
      <div className="border-t border-border p-4">
        <form onSubmit={handleSubmit} className="space-y-3">
          {/* Image upload */}
          <ImageUploadComponent
            images={uploadedImages}
            onImagesChange={setUploadedImages}
            maxImages={5}
            maxSizeMB={10}
          />

          {/* Text input */}
          <div className="flex gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 resize-none rounded-md border border-border bg-background px-3 py-2"
              rows={1}
            />
            <Button
              type="submit"
              disabled={submitDisabled || (!input.trim() && uploadedImages.length === 0)}
            >
              <ArrowUp size={16} />
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

**4.3 Backend: Multimodal Message Processing**

Update backend to handle image content in messages:

```python
from langchain_core.messages import HumanMessage
from typing import List, Dict, Any

def create_multimodal_message(
    text: str,
    images: List[Dict[str, Any]]
) -> HumanMessage:
    """Create multimodal message with text and images.

    Args:
        text: Text content
        images: List of image uploads with data URLs

    Returns:
        HumanMessage with multimodal content
    """
    if not images:
        return HumanMessage(content=text)

    # Build content array with text and images
    content = []

    # Add text
    if text:
        content.append({"type": "text", "text": text})

    # Add images
    for image in images:
        # Extract base64 data from data URL
        data_url = image["data"]
        if data_url.startswith("data:"):
            # Format: data:image/png;base64,<base64_data>
            mime_type, base64_data = data_url.split(",", 1)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": data_url,  # ChatOpenAI accepts data URLs directly
                },
            })

    return HumanMessage(content=content)
```

### Part 5: Remove Tool Use Round Limitations

**5.1 Agent Configuration**

Update agent creation to support unlimited tool rounds:

```python
def create_browser_agent(
    tools: list,
    system_prompt: str,
    enable_reasoning: bool = True,
    max_iterations: Optional[int] = None,  # None = unlimited
):
    """Create browser automation agent with unlimited tool rounds.

    Args:
        tools: List of tools for the agent
        system_prompt: System prompt for the agent
        enable_reasoning: Enable reasoning display
        max_iterations: Max tool iterations (None for unlimited)

    Returns:
        Deep agent configured for long-horizon tasks
    """
    llm = create_llm(
        stream=True,
        enable_reasoning=enable_reasoning,
    )

    agent = create_deep_agent(
        llm=llm,
        tools=tools,
        system_message=system_prompt,
        max_iterations=max_iterations,  # Set to None for unlimited
        # Default is 100 in deepagents, we override to None
    )

    return agent
```

**5.2 Frontend: Streaming Without Limits**

Update `ChatProvider.tsx` to handle long-running tasks:

```typescript
const sendMessage = useCallback(
  async (text: string, images?: ImageUpload[]) => {
    setIsLoading(true);

    try {
      // Create multimodal message content
      const content = images && images.length > 0
        ? createMultimodalContent(text, images)
        : text;

      // Stream without iteration limits
      const stream = client.runs.stream(
        threadId,
        assistantId,
        {
          input: { messages: [{ role: "human", content }] },
          streamMode: "values",
          // No maxTokens or iteration limits - allow long-horizon tasks
        }
      );

      for await (const chunk of stream) {
        // Process chunks (reasoning, messages, todos, etc.)
        processChunk(chunk);
      }

    } catch (error) {
      console.error("Stream error:", error);
    } finally {
      setIsLoading(false);
    }
  },
  [threadId, assistantId, client]
);
```

**5.3 User Interruption Support**

Add interrupt button for long-running tasks:

```typescript
<Button
  variant="outline"
  size="sm"
  onClick={stopStream}
  disabled={!isLoading}
  className="gap-2"
>
  <Square size={14} />
  Stop
</Button>
```

### Part 6: Configuration & Environment

**6.1 Environment Variables**

Update `deep-agents-ui/.env.local.example`:

```bash
# LangGraph Backend
NEXT_PUBLIC_DEPLOYMENT_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=browser-agent

# Features
NEXT_PUBLIC_RALPH_MODE_ENABLED=false
NEXT_PUBLIC_REASONING_ENABLED=true
NEXT_PUBLIC_REASONING_EFFORT=medium

# Browser Streaming
NEXT_PUBLIC_BROWSER_STREAM_PORT=9223

# Image Upload
NEXT_PUBLIC_MAX_IMAGES=5
NEXT_PUBLIC_MAX_IMAGE_SIZE_MB=10
```

**6.2 Settings Dialog**

Update `ConfigDialog.tsx` to include reasoning settings:

```typescript
export function ConfigDialog() {
  const [reasoningEnabled, setReasoningEnabled] = useState(true);
  const [reasoningEffort, setReasoningEffort] = useState<"low" | "medium" | "high">("medium");

  return (
    <Dialog>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Reasoning Settings */}
          <div className="space-y-2">
            <Label>Reasoning Display</Label>
            <Switch
              checked={reasoningEnabled}
              onCheckedChange={setReasoningEnabled}
            />
            <p className="text-xs text-muted-foreground">
              Show agent's thinking process (extended thinking)
            </p>
          </div>

          <div className="space-y-2">
            <Label>Reasoning Effort</Label>
            <Select value={reasoningEffort} onValueChange={setReasoningEffort}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* ... other settings ... */}
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

---

## Summary of Agent & UI Layer

**ChatOpenAI Integration:**
- Replaced AzureChatOpenAI with ChatOpenAI supporting reasoning API
- Configuration: `use_responses_api=True`, `reasoning={"effort": "medium", "summary": "detailed"}`
- Streaming reasoning content via `additional_kwargs["reasoning"]`
- Backend extracts reasoning summary and encrypted content
- Models: GPT-5 and o4-mini exclusively

**Reasoning Display (Frontend):**
- ReasoningDisplay component mimics Claude's thinking display
- Collapsible with preview (Sparkles icon)
- Streams reasoning text character-by-character
- Italicized preview when collapsed
- Distinct from ThoughtProcess (ThoughtProcess = deprecated, ReasoningDisplay = new)

**Enhanced Browser Preview:**
- Auto-show when browser session activates
- Auto-hide 2 seconds after session closes
- Manual show/hide/minimize controls
- Persistent during browser interactions
- 400px width panel, collapsible to 12px

**Image Upload (Multimodal):**
- Drag-and-drop, file picker, clipboard paste support
- Max 5 images, 10MB each (configurable)
- Thumbnail preview with remove buttons
- Base64 encoding for transmission
- Backend creates multimodal HumanMessage with image_url content blocks
- ChatOpenAI processes images alongside text (GPT-5/o4-mini support vision)

**Long-Horizon Tasks:**
- Removed tool use round limitations (`max_iterations=None`)
- Streaming without token/iteration caps
- User interrupt button (Stop) for long-running tasks
- Human-in-the-loop middleware handles approvals during execution

**Configuration:**
- Environment variables for all features
- Settings dialog for reasoning effort, browser preview, image upload
- localStorage persistence for user preferences

**Integration:**
- All UI components use useChatContext hook for state
- LangGraph SDK streaming handles multimodal messages
- Middleware stack (Layer 4) manages human approvals
- Skills system (Layer 5) guides agent through complex tasks

---

## Production-Grade Browser-Use Agent: Complete Architecture

**All 6 Layers Designed:**

1. ✅ **Tool Layer**: 20 built-in browser tools + Bash tool for advanced commands
2. ✅ **Backend & Storage Layer**: SQLite/PostgreSQL + FilesystemBackend from deepagents
3. ✅ **Memory & Learning Layer**: LangSmith traces + Claude Diary + Domain knowledge
4. ✅ **Middleware Stack**: Core (todos, filesystem, summarization) + Browser-specific (session, memory, anti-detection) + Production (approval, logging, skill discovery)
5. ✅ **Skills System**: Progressive disclosure (metadata → SKILL.md → supporting files), auto-generation from traces
6. ✅ **Agent & UI Layer**: ChatOpenAI with reasoning, browser preview, multimodal support, unlimited iterations

**Next Step**: Implementation phase begins with Backend & Storage Layer (Layer 2) as specified by user.
