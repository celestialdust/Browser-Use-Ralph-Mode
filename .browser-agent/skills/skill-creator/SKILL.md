---
name: skill-creator
description: Guide for creating effective skills that extend agent capabilities with specialized knowledge, workflows, or tool integrations. Use this skill when the user asks to: (1) create a new skill, (2) make a skill, (3) build a skill, (4) set up a skill, (5) initialize a skill, (6) scaffold a skill, (7) update or modify an existing skill, (8) validate a skill, (9) learn about skill structure, (10) understand how skills work, or (11) get guidance on skill design patterns. Trigger on phrases like "create a skill", "new skill", "make a skill", "skill for X", "how do I create a skill", or "help me build a skill".
---

# Skill Creator

This skill provides guidance for creating effective skills.

## About Skills

Skills are modular packages extending agent capabilities through specialized knowledge, workflows, and tools. They function as domain-specific onboarding systems that equip general-purpose agents with procedural expertise.

### Skill Location

Skills reside in `.browser-agent/skills/` directory:

```
.browser-agent/skills/
├── skill-name.md              # Main skill file with YAML frontmatter
├── skill-name/                # Optional supporting files directory
│   ├── scripts/               # Executable code
│   ├── references/            # Documentation loaded as needed
│   └── assets/                # Output files (templates, icons, fonts)
└── ...
```

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex tasks

## Core Principles

### Concise is Key

"The context window is a public good. Skills share the context window with everything else the agent needs." Only include information agents genuinely require. Each piece must justify its token cost.

Assume agents are already capable. Prefer concise examples over verbose explanations.

### Set Appropriate Degrees of Freedom

Match specificity to task fragility:

- **High freedom (text instructions)**: Multiple valid approaches, context-dependent decisions
- **Medium freedom (pseudocode/scripts with parameters)**: Preferred patterns exist, configuration affects behavior
- **Low freedom (specific scripts, few parameters)**: Fragile operations, critical consistency requirements

### Skill Anatomy

Every skill requires a `skill-name.md` file with optional supporting directory:

```
skill-name.md           # Required: Main skill with YAML frontmatter
skill-name/             # Optional: Supporting files
├── scripts/            # Executable code
├── references/         # Documentation loaded as needed
└── assets/             # Output files (templates, icons, fonts)
```

#### Skill File Structure

- **Frontmatter (YAML)**: Required `name` and `description` fields determine when the skill triggers
- **Body (Markdown)**: Instructions loaded after skill triggers

#### Bundled Resources

**Scripts (`scripts/`)**: Executable code for deterministic, repeatedly-used tasks. Include when code requires reliability or gets frequently rewritten.

**References (`references/`)**: Documentation loaded contextually. Ideal for schemas, APIs, policies, workflows. Keep detailed information separate from main skill file to maintain efficiency.

**Assets (`assets/`)**: Files for output production (templates, images, boilerplate code). Not loaded into context, used directly in deliverables.

#### What Not to Include

Avoid auxiliary documentation like README.md, INSTALLATION_GUIDE.md, CHANGELOG.md. Include only files supporting direct functionality.

### Progressive Disclosure Design

Skills use three-level loading to manage context:

1. **Metadata** - Name and description (~100 words, always available)
2. **Skill body** - When triggered (<5k words)
3. **Bundled resources** - As needed by the agent

Keep skill files under 500 lines. Reference separate files clearly to guide agents on when to read them.

**Pattern 1**: High-level guide with references pointing to detailed content

**Pattern 2**: Domain-specific organization to load only relevant sections

**Pattern 3**: Basic content with conditional links to advanced features

Guidelines: Keep references one level deep from main skill file. Include tables of contents in files exceeding 100 lines.

## Skill Creation Process

Follow these six steps:

1. Understand the skill with concrete examples
2. Plan reusable contents (scripts, references, assets)
3. Create the skill file
4. Add resources and edit content
5. Validate the skill
6. Iterate based on real usage

### Step 1: Understanding Through Examples

Clarify concrete usage patterns. Ask about functionality, specific examples, and trigger phrases. Conclude when skill scope is clear.

### Step 2: Planning Reusable Contents

Analyze each example to identify helpful resources:

- Repetitive code → `scripts/`
- Reference material → `references/`
- Output templates → `assets/`

### Step 3: Creating the Skill

Create a new skill file with this structure:

```markdown
---
name: skill-name
description: Brief description of what the skill does and when to use it. Include trigger phrases.
---

# Skill Title

## Overview
Brief explanation of the skill's purpose.

## Usage
Step-by-step instructions or workflow.

## Examples
Concrete examples demonstrating usage.
```

### Step 4: Editing the Skill

Start with reusable resources, then update skill content.

**Frontmatter**: Include `name` and `description`. The description is the primary trigger mechanism, detailing what the skill does and when to use it. Include all "when to use" information here.

**Body**: Write imperative instructions for using the skill and resources.

Test all scripts by running them. Delete unused files.

### Step 5: Validating the Skill

Check that:
- YAML frontmatter is properly formatted between `---` delimiters
- `name` and `description` fields are present
- Name uses hyphen-case (lowercase letters, digits, hyphens only)
- Description is clear and includes trigger phrases

### Step 6: Iterating

After real usage, improve the skill based on identified inefficiencies. Update resources and content accordingly.

## Skill Template

```markdown
---
name: my-skill-name
description: What this skill does. Use when user asks to [trigger phrases]. Helps with [use cases].
---

# My Skill Name

## Overview
Brief description of purpose and capabilities.

## Quick Start
Essential commands or steps to get started.

## Detailed Usage
More comprehensive instructions.

## Examples
Concrete usage examples.

## Troubleshooting
Common issues and solutions (optional).
```
