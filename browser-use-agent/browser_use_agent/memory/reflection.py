"""Reflection engine for updating agent memory from experiences."""

import json
from pathlib import Path
from typing import List, Dict

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from browser_use_agent.memory.diary import SessionDiary
from browser_use_agent.storage import StorageConfig


class ReflectionEngine:
    """Reflects on diary entries and updates procedural memory.

    The reflection engine analyzes session diary entries to:
    - Identify rule violations and weak guidelines
    - Discover new patterns and domain knowledge
    - Find opportunities for skill extraction
    - Update AGENTS.md with synthesized learnings

    This is inspired by Claude Code's /reflect command pattern.
    """

    def __init__(self):
        """Initialize reflection engine."""
        self.diary = SessionDiary()
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.agents_md_path = StorageConfig.get_agent_dir() / "memory" / "AGENTS.md"
        self.reflection_dir = StorageConfig.get_agent_dir() / "memory" / "reflections"
        self.reflection_dir.mkdir(parents=True, exist_ok=True)

    async def reflect(self, force: bool = False) -> str:
        """Analyze unprocessed diary entries and update AGENTS.md.

        Similar to Claude Code's /reflect command:
        1. Load unprocessed diary entries
        2. Analyze each entry against existing rules
        3. Identify violations, patterns, new learnings
        4. Update AGENTS.md with synthesized rules
        5. Mark entries as processed

        Args:
            force: Force reflection even if no unprocessed entries

        Returns:
            Summary message
        """
        entries = self.diary.get_unprocessed_entries()
        if not entries and not force:
            return "[Reflection] No unprocessed diary entries"

        print(f"[Reflection] Processing {len(entries)} diary entries")

        # Load current rules
        current_rules = ""
        if self.agents_md_path.exists():
            current_rules = self.agents_md_path.read_text()

        all_insights = []

        # Analyze each entry
        for entry_path in entries:
            entry_content = entry_path.read_text()

            print(f"[Reflection] Analyzing: {entry_path.name}")
            analysis = await self._analyze_entry(entry_content, current_rules)
            all_insights.append(analysis)

            # Save individual reflection
            reflection_path = self.reflection_dir / f"{entry_path.stem}_reflection.md"
            reflection_path.write_text(self._format_reflection(analysis))

            # Mark processed
            self.diary.mark_processed(entry_path)

        # Synthesize all insights into rule updates
        print("[Reflection] Synthesizing insights into updated rules")
        updated_rules = await self._synthesize_rules(current_rules, all_insights)

        # Update AGENTS.md
        self.agents_md_path.write_text(updated_rules)
        print(f"[Reflection] Updated {self.agents_md_path}")

        return f"[Reflection] Reflected on {len(entries)} entries, updated AGENTS.md"

    async def _analyze_entry(self, entry: str, current_rules: str) -> Dict:
        """Analyze diary entry against existing rules.

        Args:
            entry: Diary entry content
            current_rules: Current AGENTS.md content

        Returns:
            Analysis dict with findings
        """
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

Return JSON with analysis:
{{
  "rule_violations": [{{"rule": "...", "violation": "..."}}],
  "weak_guidelines": [{{"guideline": "...", "issue": "..."}}],
  "new_patterns": ["pattern1", "pattern2"],
  "domain_knowledge": {{"domain": "...", "insights": ["..."]}},
  "skill_opportunities": [{{"name": "...", "description": "..."}}]
}}
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            return {
                "rule_violations": [],
                "weak_guidelines": [],
                "new_patterns": [],
                "domain_knowledge": {},
                "skill_opportunities": []
            }

    async def _synthesize_rules(self, current_rules: str, insights: List[Dict]) -> str:
        """Synthesize insights into updated AGENTS.md content.

        Args:
            current_rules: Current AGENTS.md content
            insights: List of analysis results

        Returns:
            Updated AGENTS.md content
        """
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
Return ONLY the updated markdown content.
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    def _format_reflection(self, analysis: Dict) -> str:
        """Format analysis as markdown reflection.

        Args:
            analysis: Analysis dict

        Returns:
            Formatted markdown
        """
        return f"""# Reflection Analysis

## Rule Violations
{self._format_violations(analysis.get("rule_violations", []))}

## Weak Guidelines
{self._format_weak(analysis.get("weak_guidelines", []))}

## New Patterns
{self._format_list(analysis.get("new_patterns", []))}

## Domain Knowledge
{self._format_domain(analysis.get("domain_knowledge", {}))}

## Skill Opportunities
{self._format_skills(analysis.get("skill_opportunities", []))}
"""

    def _format_violations(self, violations: List[Dict]) -> str:
        """Format rule violations as markdown."""
        if not violations:
            return "- (None detected)\n"
        return "\n".join([f"- **{v['rule']}**: {v['violation']}" for v in violations])

    def _format_weak(self, weak: List[Dict]) -> str:
        """Format weak guidelines as markdown."""
        if not weak:
            return "- (None identified)\n"
        return "\n".join([f"- **{w['guideline']}**: {w['issue']}" for w in weak])

    def _format_list(self, items: List[str]) -> str:
        """Format list as markdown."""
        if not items:
            return "- (None)\n"
        return "\n".join([f"- {item}" for item in items])

    def _format_domain(self, domain: Dict) -> str:
        """Format domain knowledge as markdown."""
        if not domain:
            return "- (None)\n"
        domain_name = domain.get("domain", "unknown")
        insights = domain.get("insights", [])
        return f"**{domain_name}**:\n" + "\n".join([f"- {i}" for i in insights])

    def _format_skills(self, skills: List[Dict]) -> str:
        """Format skill opportunities as markdown."""
        if not skills:
            return "- (None)\n"
        return "\n".join([f"- **{s['name']}**: {s['description']}" for s in skills])
