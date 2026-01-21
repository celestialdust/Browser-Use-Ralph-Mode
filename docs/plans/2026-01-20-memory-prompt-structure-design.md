# Memory/Prompt Structure Overhaul Design

**Date:** 2026-01-20
**Status:** Approved
**Issue:** Agent memory is unstructured, agent doesn't know fixed file paths, needs better guidance on skills and parallel execution

## Directory Structure

```
.browser-agent/
├── memory/
│   ├── AGENTS.md              # Learned patterns (standardized format)
│   ├── USER_PREFERENCES.md    # User preferences (NEW)
│   └── diary/                 # Session diaries (existing)
│       ├── {session}_{timestamp}.md
│       └── processed.log
├── skills/                    # Reusable workflows (existing)
│   └── {skill-name}/
│       └── SKILL.md
└── artifacts/
    ├── screenshots/           # Browser screenshots (existing)
    ├── file_outputs/          # User-requested files (NEW)
    └── tool_outputs/          # Large tool outputs (existing)
```

## File Formats

### AGENTS.md (Standardized Format)

```markdown
# Agent Learnings

## Website Patterns

### {domain}.com
- **Login flow**: {description}
- **Navigation quirks**: {description}
- **Element selectors**: {common patterns}
- **Last updated**: {date}

### google.com
- **Login flow**: "Sign in" top-right → email → password → 2FA may trigger
- **Navigation quirks**: Cookie consent banner may block elements
- **Element selectors**: Search box is usually first textbox ref
- **Last updated**: 2026-01-20

## Task Patterns

### {task-type}
- **Best approach**: {description}
- **Common pitfalls**: {what to avoid}
- **Tools to use**: {recommended tools}

### Authentication
- **Best approach**: Check chat for credentials first, then request_credentials
- **Common pitfalls**: Repeated login attempts trigger security blocks
- **Tools to use**: request_credentials, browser_fill

### Form Handling
- **Best approach**: Snapshot after each fill, refs change frequently
- **Common pitfalls**: Submit buttons often have multiple - use visible one
- **Tools to use**: browser_fill, browser_snapshot, browser_click

## Error Recovery

### {error-type}
- **Symptoms**: {what it looks like}
- **Solution**: {how to fix}
- **Prevention**: {how to avoid}

### "Element not found"
- **Symptoms**: Click/fill fails, element ref doesn't exist
- **Solution**: Re-snapshot, try alternative text, scroll into view
- **Prevention**: Always snapshot after navigation or DOM changes

### "Daemon failed to start"
- **Symptoms**: browser_navigate returns daemon error
- **Solution**: Wait 5s, retry once, then ask human
- **Prevention**: Close browser sessions when done

## General Rules

- Always snapshot after navigation
- Close browser when task complete
- Never store or guess credentials
- Ask human after 2-3 failed attempts with same approach
```

### USER_PREFERENCES.md (New File)

```markdown
# User Preferences

## General
- Timezone: {timezone}
- Language: {language}
- Confirmation: {when to ask for confirmation}

## Browsing
- Default browser: {browser}
- Preferred search engine: {engine}
- Cookie consent: {auto-accept or ask}

## Communication
- Detail level: {verbose or concise}
- Updates: {when to notify}

## Credentials
- {service}: {stored or ask each time}
```

**Prompt instruction for updating:**
```
When user mentions a preference:
1. Read USER_PREFERENCES.md
2. Add/update in appropriate section (General, Browsing, Communication, Credentials)
3. Use "Key: Value" format
4. Reference preferences when relevant to tasks
```

### Diary Format (Keep Existing)

```markdown
# Session Diary Entry

**Session ID**: {id}
**Date**: {iso_date}

## Accomplishments
- {item}

## Challenges Encountered
- {item}

## Design Decisions
- **{decision}**: {rationale}

## User Feedback
{feedback}

## Tags
{auto-extracted tags}
```

## Prompt Additions

### Fixed Paths Section

Add to `BROWSER_AGENT_SYSTEM_PROMPT` in `prompts.py`:

```
<file_paths>
All paths are relative to .browser-agent/

**Memory (read/write):**
- memory/AGENTS.md - Learned patterns per site/task (update when learning something reusable)
- memory/USER_PREFERENCES.md - User preferences (update when user mentions preferences)
- memory/diary/ - Session diaries (auto-created, one per session)

**Skills (read-only):**
- skills/{name}/SKILL.md - Reusable workflows (ls skills/ to discover)

**Artifacts (write):**
- artifacts/screenshots/ - Browser screenshots (browser_screenshot saves here)
- artifacts/file_outputs/ - User-requested files (PDFs, exports, reports)
- artifacts/tool_outputs/ - Large tool outputs (auto-saved when >1000 chars)

When user requests a file (PDF, report, export):
→ Save to artifacts/file_outputs/{descriptive_name}.{ext}
→ Return the full path to user
</file_paths>
```

### Skills Discovery Section

Add to prompt:

```
<skills_discovery>
Skills are reusable workflows. To use:
1. ls .browser-agent/skills/ - List available skills
2. read_file(.browser-agent/skills/{name}/SKILL.md) - Get instructions
3. Follow the skill's step-by-step guide

Check skills before complex tasks - a workflow may already exist.
</skills_discovery>
```

### Parallel Execution Section

Add to prompt:

```
<parallel_execution>
Use task tool to spawn subagents for parallel work when:
- Multiple independent tasks (e.g., "research 3 companies")
- Repetitive operations (e.g., "process 5 files")
- Tasks with no dependencies between them

Do NOT parallelize when results depend on each other.
</parallel_execution>
```

## Implementation

### Files to Create

1. `.browser-agent/memory/USER_PREFERENCES.md` - Template file
2. `.browser-agent/artifacts/file_outputs/` - Directory (create on first use)

### Files to Modify

1. `browser-use-agent/browser_use_agent/prompts.py` - Add three new sections to system prompt
2. `browser-use-agent/browser_use_agent/storage/config.py` - Add `file_outputs` directory creation
3. `.browser-agent/memory/AGENTS.md` - Reformat to standardized structure

### Prompt Changes (prompts.py)

Add after `</memory_management>` section:

```python
BROWSER_AGENT_SYSTEM_PROMPT = """<system>
... existing content ...

<file_paths>
All paths are relative to .browser-agent/

**Memory (read/write):**
- memory/AGENTS.md - Learned patterns per site/task (update when learning something reusable)
- memory/USER_PREFERENCES.md - User preferences (update when user mentions preferences)
- memory/diary/ - Session diaries (auto-created, one per session)

**Skills (read-only):**
- skills/{name}/SKILL.md - Reusable workflows (ls skills/ to discover)

**Artifacts (write):**
- artifacts/screenshots/ - Browser screenshots (browser_screenshot saves here)
- artifacts/file_outputs/ - User-requested files (PDFs, exports, reports)
- artifacts/tool_outputs/ - Large tool outputs (auto-saved when >1000 chars)

When user requests a file (PDF, report, export):
→ Save to artifacts/file_outputs/{descriptive_name}.{ext}
→ Return the full path to user
</file_paths>

<skills_discovery>
Skills are reusable workflows. To use:
1. ls .browser-agent/skills/ - List available skills
2. read_file(.browser-agent/skills/{name}/SKILL.md) - Get instructions
3. Follow the skill's step-by-step guide

Check skills before complex tasks - a workflow may already exist.
</skills_discovery>

<parallel_execution>
Use task tool to spawn subagents for parallel work when:
- Multiple independent tasks (e.g., "research 3 companies")
- Repetitive operations (e.g., "process 5 files")
- Tasks with no dependencies between them

Do NOT parallelize when results depend on each other.
</parallel_execution>

... rest of existing content ...
</system>"""
```

## Testing

1. Start a new session
2. Mention a preference (e.g., "I prefer concise responses")
3. Verify USER_PREFERENCES.md is created/updated
4. Request a file export (e.g., "save this as a PDF")
5. Verify file is saved to artifacts/file_outputs/
6. Ask agent to learn a new site pattern
7. Verify AGENTS.md is updated in correct section
8. Ask agent to do parallel research
9. Verify task tool is used appropriately
