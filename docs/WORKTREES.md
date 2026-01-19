# Git Worktrees for Production Browser Agent Implementation

**Created:** 2026-01-19
**Status:** All worktrees initialized and ready

## Worktree Structure

All worktrees are located in `.worktrees/` (git-ignored):

```
/Users/xuejoey/Documents/github/Browser-Use/
├── .worktrees/
│   ├── phase-1-enhanced-tools/       (branch: phase-1-enhanced-tools)
│   ├── phase-2-backend-storage/      (branch: phase-2-backend-storage)
│   ├── phase-3-memory-learning/      (branch: phase-3-memory-learning)
│   ├── phase-4-middleware/           (branch: phase-4-middleware)
│   ├── phase-5-skills/               (branch: phase-5-skills)
│   └── phase-6-enhanced-ui/          (branch: phase-6-enhanced-ui)
└── docs/
    └── plans/
        └── 2026-01-19-production-browser-agent.md
```

## Phase Details

### Phase 1: Enhanced Tool Layer
- **Branch:** `phase-1-enhanced-tools`
- **Path:** `.worktrees/phase-1-enhanced-tools/`
- **Goal:** Expand from 18 to 25+ browser tools
- **Tasks:** 1.1-1.4 (Navigation, Interaction, Observation, Approval Config)
- **Dependencies:** ✅ Installed (uv venv + pip install -e .)

### Phase 2: Backend & Storage Layer
- **Branch:** `phase-2-backend-storage`
- **Path:** `.worktrees/phase-2-backend-storage/`
- **Goal:** Dual database support + FilesystemBackend integration
- **Tasks:** 2.1-2.3 (Storage Config, FilesystemBackend, Directory Init)
- **Dependencies:** ✅ Installed

### Phase 3: Memory & Learning Layer
- **Branch:** `phase-3-memory-learning`
- **Path:** `.worktrees/phase-3-memory-learning/`
- **Goal:** LangSmith traces, diary, reflection engine
- **Tasks:** 3.1-3.3 (Trace Fetcher, Session Diary, Reflection Engine)
- **Dependencies:** ✅ Installed

### Phase 4: Middleware Stack
- **Branch:** `phase-4-middleware`
- **Path:** `.worktrees/phase-4-middleware/`
- **Goal:** Browser-specific and production middleware
- **Tasks:** 4.1-4.2 (Browser Session, Human Approval)
- **Dependencies:** ✅ Installed

### Phase 5: Skills System
- **Branch:** `phase-5-skills`
- **Path:** `.worktrees/phase-5-skills/`
- **Goal:** Progressive skill loading and discovery
- **Tasks:** 5.1 (Skill Loader)
- **Dependencies:** ✅ Installed

### Phase 6: Enhanced UI Layer
- **Branch:** `phase-6-enhanced-ui`
- **Path:** `.worktrees/phase-6-enhanced-ui/`
- **Goal:** ChatOpenAI, reasoning display, multimodal
- **Tasks:** 6.1-6.2 (ChatOpenAI Migration, Reasoning Display)
- **Dependencies:** ✅ Installed

## How to Execute Each Phase

### Option 1: Execute with executing-plans skill (Recommended)

Open a new Claude Code session **in the specific worktree directory**:

```bash
# Example for Phase 1
cd /Users/xuejoey/Documents/github/Browser-Use/.worktrees/phase-1-enhanced-tools
claude code
```

Then in that session:

```
/executing-plans
```

The agent will:
1. Load the plan from `docs/plans/2026-01-19-production-browser-agent.md`
2. Extract tasks for the current phase
3. Execute them task-by-task with code review checkpoints
4. Merge back to main when complete

### Option 2: Manual execution

Navigate to worktree and work directly:

```bash
cd .worktrees/phase-1-enhanced-tools/browser-use-agent
source .venv/bin/activate
# Make changes following the plan
```

## Verification Commands

### List all worktrees
```bash
git worktree list
```

### Check worktree status
```bash
cd .worktrees/phase-1-enhanced-tools
git status
git branch
```

### Activate virtual environment
```bash
cd .worktrees/phase-1-enhanced-tools/browser-use-agent
source .venv/bin/activate
```

### Test backend setup
```bash
cd .worktrees/phase-1-enhanced-tools/browser-use-agent
source .venv/bin/activate
uv run python -c "from browser_use_agent.browser_agent import create_browser_agent; print('Agent imports successfully')"
```

## Merging Strategy

After completing a phase:

1. **Test thoroughly** in the worktree
2. **Commit all changes** with descriptive messages
3. **Switch to main**: `git checkout main`
4. **Merge the phase branch**: `git merge phase-1-enhanced-tools`
5. **Test in main branch**
6. **Push to remote**: `git push origin main`
7. **Clean up worktree** (optional): `git worktree remove .worktrees/phase-1-enhanced-tools`

## Dependencies Between Phases

- **Phase 1** → Independent (can start immediately)
- **Phase 2** → Depends on Phase 1 tools being available
- **Phase 3** → Depends on Phase 2 storage layer
- **Phase 4** → Depends on Phase 2 storage + Phase 1 tools
- **Phase 5** → Depends on Phase 2 storage
- **Phase 6** → Depends on all backend phases (2-5)

**Recommended execution order:** 1 → 2 → 3 → 4 → 5 → 6

## Notes

- Each worktree has its own `.venv` (isolated dependencies)
- `.worktrees/` is git-ignored (won't be committed)
- All worktrees share the same git object database (efficient)
- Each worktree can have different code running simultaneously
- Great for testing changes before merging to main

## Cleanup

When all phases are complete and merged:

```bash
# Remove all worktrees
git worktree remove .worktrees/phase-1-enhanced-tools
git worktree remove .worktrees/phase-2-backend-storage
git worktree remove .worktrees/phase-3-memory-learning
git worktree remove .worktrees/phase-4-middleware
git worktree remove .worktrees/phase-5-skills
git worktree remove .worktrees/phase-6-enhanced-ui

# Delete the .worktrees directory
rm -rf .worktrees
```
