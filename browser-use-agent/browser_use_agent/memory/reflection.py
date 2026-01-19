"""Reflection engine for updating agent memory from experiences."""

from pathlib import Path
from typing import List, Dict

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from browser_use_agent.memory.diary import SessionDiary
from browser_use_agent.storage import StorageConfig


# Pydantic models for structured output
class RuleViolation(BaseModel):
    """A rule violation identified in the session."""
    rule: str = Field(description="The rule that was violated")
    violation: str = Field(description="Description of how it was violated")


class WeakGuideline(BaseModel):
    """A weak or vague guideline that needs strengthening."""
    guideline: str = Field(description="The weak guideline")
    issue: str = Field(description="Why it's weak or not enforced")


class DomainKnowledge(BaseModel):
    """Site-specific knowledge learned during the session."""
    domain: str = Field(description="The domain name (e.g., 'google', 'linkedin')")
    insights: List[str] = Field(description="List of insights about this domain")


class SkillOpportunity(BaseModel):
    """A repeatable workflow that could be extracted as a skill."""
    name: str = Field(description="Name for the potential skill")
    description: str = Field(description="What the skill would do")


class SessionAnalysis(BaseModel):
    """Analysis of a session diary entry."""
    rule_violations: List[RuleViolation] = Field(
        default_factory=list,
        description="Rule violations identified in the session"
    )
    weak_guidelines: List[WeakGuideline] = Field(
        default_factory=list,
        description="Weak guidelines that need strengthening"
    )
    new_patterns: List[str] = Field(
        default_factory=list,
        description="New patterns not captured in existing rules"
    )
    domain_knowledge: DomainKnowledge | None = Field(
        default=None,
        description="Site-specific learnings to document"
    )
    skill_opportunities: List[SkillOpportunity] = Field(
        default_factory=list,
        description="Repeatable workflows to extract as skills"
    )


class ReflectionEngine:
    """Reflects on diary entries and updates procedural memory.

    The reflection engine analyzes session diary entries to:
    - Identify rule violations and weak guidelines
    - Discover new patterns and domain knowledge
    - Find opportunities for skill extraction
    - Update AGENTS.md with synthesized learnings

    This is inspired by Claude Code's /reflect command pattern.
    Uses structured output via Pydantic models for reliable parsing.
    """

    def __init__(self):
        """Initialize reflection engine."""
        self.diary = SessionDiary()
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        # Create structured output version of LLM
        self.structured_llm = self.llm.with_structured_output(SessionAnalysis)
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

    async def _analyze_entry(self, entry: str, current_rules: str) -> SessionAnalysis:
        """Analyze diary entry against existing rules using structured output.

        Args:
            entry: Diary entry content
            current_rules: Current AGENTS.md content

        Returns:
            SessionAnalysis with structured findings
        """
        prompt = f"""Analyze this session diary entry against existing agent rules:

CURRENT RULES:
{current_rules or "(No existing rules)"}

DIARY ENTRY:
{entry}

Identify:
1. **Rule Violations**: Did the session violate any existing rules?
2. **Weak Guidelines**: Are any rules too vague or not enforced?
3. **New Patterns**: Any recurring patterns not captured in rules?
4. **Domain Knowledge**: Site-specific learnings to document?
5. **Skill Opportunities**: Repeatable workflows to extract as skills?

Return a structured analysis with these findings.
"""

        # Use structured output - no JSON parsing needed!
        analysis = await self.structured_llm.ainvoke([HumanMessage(content=prompt)])
        return analysis

    async def _synthesize_rules(self, current_rules: str, insights: List[SessionAnalysis]) -> str:
        """Synthesize insights into updated AGENTS.md content.

        Args:
            current_rules: Current AGENTS.md content
            insights: List of SessionAnalysis results

        Returns:
            Updated AGENTS.md content
        """
        # Convert insights to readable format for the LLM
        insights_text = self._format_insights_for_synthesis(insights)

        prompt = f"""Update agent memory rules based on reflection insights:

CURRENT RULES:
{current_rules or "(No existing rules - create initial structure)"}

INSIGHTS FROM SESSIONS:
{insights_text}

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

    def _format_insights_for_synthesis(self, insights: List[SessionAnalysis]) -> str:
        """Format SessionAnalysis objects into readable text for synthesis.

        Args:
            insights: List of SessionAnalysis results

        Returns:
            Formatted text summary
        """
        parts = []
        for i, analysis in enumerate(insights, 1):
            parts.append(f"\n### Session {i}")

            if analysis.rule_violations:
                parts.append("\n**Rule Violations:**")
                for v in analysis.rule_violations:
                    parts.append(f"- {v.rule}: {v.violation}")

            if analysis.weak_guidelines:
                parts.append("\n**Weak Guidelines:**")
                for w in analysis.weak_guidelines:
                    parts.append(f"- {w.guideline}: {w.issue}")

            if analysis.new_patterns:
                parts.append("\n**New Patterns:**")
                for p in analysis.new_patterns:
                    parts.append(f"- {p}")

            if analysis.domain_knowledge:
                parts.append(f"\n**Domain Knowledge ({analysis.domain_knowledge.domain}):**")
                for insight in analysis.domain_knowledge.insights:
                    parts.append(f"- {insight}")

            if analysis.skill_opportunities:
                parts.append("\n**Skill Opportunities:**")
                for s in analysis.skill_opportunities:
                    parts.append(f"- {s.name}: {s.description}")

        return "\n".join(parts)

    def _format_reflection(self, analysis: SessionAnalysis) -> str:
        """Format SessionAnalysis as markdown reflection.

        Args:
            analysis: SessionAnalysis object

        Returns:
            Formatted markdown
        """
        return f"""# Reflection Analysis

## Rule Violations
{self._format_violations(analysis.rule_violations)}

## Weak Guidelines
{self._format_weak(analysis.weak_guidelines)}

## New Patterns
{self._format_list(analysis.new_patterns)}

## Domain Knowledge
{self._format_domain(analysis.domain_knowledge)}

## Skill Opportunities
{self._format_skills(analysis.skill_opportunities)}
"""

    def _format_violations(self, violations: List[RuleViolation]) -> str:
        """Format rule violations as markdown."""
        if not violations:
            return "- (None detected)\n"
        return "\n".join([f"- **{v.rule}**: {v.violation}" for v in violations])

    def _format_weak(self, weak: List[WeakGuideline]) -> str:
        """Format weak guidelines as markdown."""
        if not weak:
            return "- (None identified)\n"
        return "\n".join([f"- **{w.guideline}**: {w.issue}" for w in weak])

    def _format_list(self, items: List[str]) -> str:
        """Format list as markdown."""
        if not items:
            return "- (None)\n"
        return "\n".join([f"- {item}" for item in items])

    def _format_domain(self, domain: DomainKnowledge | None) -> str:
        """Format domain knowledge as markdown."""
        if not domain:
            return "- (None)\n"
        insights_text = "\n".join([f"- {i}" for i in domain.insights])
        return f"**{domain.domain}**:\n{insights_text}"

    def _format_skills(self, skills: List[SkillOpportunity]) -> str:
        """Format skill opportunities as markdown."""
        if not skills:
            return "- (None)\n"
        return "\n".join([f"- **{s.name}**: {s.description}" for s in skills])
