import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import os from "os";

interface SkillMetadata {
  name: string;
  description: string;
  tags?: string;
  file: string;
  source: "backend";
}

function extractFrontmatter(content: string): Record<string, string> {
  if (!content.startsWith("---")) {
    return {};
  }

  const parts = content.split("---", 3);
  if (parts.length < 3) {
    return {};
  }

  const frontmatter = parts[1];
  const metadata: Record<string, string> = {};

  for (const line of frontmatter.trim().split("\n")) {
    const colonIndex = line.indexOf(":");
    if (colonIndex > -1) {
      const key = line.slice(0, colonIndex).trim();
      const value = line.slice(colonIndex + 1).trim();
      metadata[key] = value;
    }
  }

  return metadata;
}

export async function GET() {
  try {
    // Skills directory: ~/.browser-agent/skills/ or project's .browser-agent/skills/
    const homeDir = os.homedir();
    const projectSkillsDir = path.join(process.cwd(), "..", ".browser-agent", "skills");
    const userSkillsDir = path.join(homeDir, ".browser-agent", "skills");

    // Try project directory first, then user home directory
    const skillsDir = fs.existsSync(projectSkillsDir) ? projectSkillsDir : userSkillsDir;

    if (!fs.existsSync(skillsDir)) {
      return NextResponse.json({ skills: [], count: 0 });
    }

    const skills: SkillMetadata[] = [];
    const seenNames = new Set<string>();

    // Read flat files (*.md)
    const entries = fs.readdirSync(skillsDir, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith(".md")) {
        const filePath = path.join(skillsDir, entry.name);
        const content = fs.readFileSync(filePath, "utf-8");
        const metadata = extractFrontmatter(content);

        const name = metadata.name || entry.name.replace(".md", "");
        if (!seenNames.has(name)) {
          seenNames.add(name);
          skills.push({
            name,
            description: metadata.description || "No description",
            tags: metadata.tags,
            file: entry.name,
            source: "backend",
          });
        }
      }
    }

    // Read subdirectory skills (skill_name/SKILL.md)
    for (const entry of entries) {
      if (entry.isDirectory()) {
        const skillFilePath = path.join(skillsDir, entry.name, "SKILL.md");
        if (fs.existsSync(skillFilePath)) {
          const content = fs.readFileSync(skillFilePath, "utf-8");
          const metadata = extractFrontmatter(content);

          const name = metadata.name || entry.name;
          if (!seenNames.has(name)) {
            seenNames.add(name);
            skills.push({
              name,
              description: metadata.description || "No description",
              tags: metadata.tags,
              file: `${entry.name}/SKILL.md`,
              source: "backend",
            });
          }
        }
      }
    }

    // Sort by name
    skills.sort((a, b) => a.name.localeCompare(b.name));

    return NextResponse.json({ skills, count: skills.length });
  } catch (error) {
    console.error("Error loading skills:", error);
    return NextResponse.json(
      { error: "Failed to load skills", skills: [], count: 0 },
      { status: 500 }
    );
  }
}
