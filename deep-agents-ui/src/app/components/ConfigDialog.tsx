"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { StandaloneConfig } from "@/lib/config";
import { X } from "lucide-react";

// Skill type for the skill management UI
interface Skill {
  name: string;
  description: string;
  enabled: boolean;
  source: "backend" | "user";
}

interface ConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (config: StandaloneConfig) => void;
  initialConfig?: StandaloneConfig;
}

export function ConfigDialog({
  open,
  onOpenChange,
  onSave,
  initialConfig,
}: ConfigDialogProps) {
  const [deploymentUrl, setDeploymentUrl] = useState(
    initialConfig?.deploymentUrl || ""
  );
  const [assistantId, setAssistantId] = useState(
    initialConfig?.assistantId || ""
  );
  const [langsmithApiKey, setLangsmithApiKey] = useState(
    initialConfig?.langsmithApiKey || ""
  );
  const [ralphModeEnabled, setRalphModeEnabled] = useState(
    initialConfig?.ralphModeEnabled ?? false
  );
  const [ralphMaxIterations, setRalphMaxIterations] = useState(
    initialConfig?.ralphMaxIterations ?? 5
  );
  const [browserStreamPort, setBrowserStreamPort] = useState(
    initialConfig?.browserStreamPort ?? 9223
  );
  // Skills state - loaded from backend and localStorage
  const [skills, setSkills] = useState<Skill[]>([]);
  const [isLoadingSkills, setIsLoadingSkills] = useState(false);

  // Load skills from backend API and localStorage when dialog opens
  useEffect(() => {
    if (!open) return;

    const loadSkills = async () => {
      setIsLoadingSkills(true);
      const allSkills: Skill[] = [];
      const seenNames = new Set<string>();

      // Load backend skills from API
      try {
        const response = await fetch("/api/skills");
        if (response.ok) {
          const data = await response.json();
          for (const skill of data.skills || []) {
            if (!seenNames.has(skill.name)) {
              seenNames.add(skill.name);
              allSkills.push({
                name: skill.name,
                description: skill.description || "No description",
                enabled: true, // Backend skills are enabled by default
                source: "backend",
              });
            }
          }
        }
      } catch (e) {
        console.error("Failed to load backend skills:", e);
      }

      // Load user skills from localStorage
      try {
        const savedSkills = localStorage.getItem("browser-agent-skills");
        if (savedSkills) {
          const userSkills = JSON.parse(savedSkills);
          for (const skill of userSkills) {
            if (!seenNames.has(skill.name)) {
              seenNames.add(skill.name);
              allSkills.push({
                ...skill,
                source: skill.source || "user",
              });
            }
          }
        }
      } catch (e) {
        console.error("Failed to load skills from localStorage:", e);
      }

      setSkills(allSkills);
      setIsLoadingSkills(false);
    };

    loadSkills();
  }, [open]);

  // Save user skills to localStorage when they change
  const saveSkills = (updatedSkills: Skill[]) => {
    setSkills(updatedSkills);
    // Only save user skills to localStorage
    const userSkills = updatedSkills.filter((s) => s.source === "user");
    try {
      localStorage.setItem("browser-agent-skills", JSON.stringify(userSkills));
    } catch (e) {
      console.error("Failed to save skills to localStorage:", e);
    }
  };

  const toggleSkill = (skillName: string) => {
    const updatedSkills = skills.map((skill) =>
      skill.name === skillName ? { ...skill, enabled: !skill.enabled } : skill
    );
    saveSkills(updatedSkills);
  };

  const deleteSkill = (skillName: string) => {
    // Only allow deleting user skills
    const skill = skills.find((s) => s.name === skillName);
    if (skill?.source === "backend") {
      return; // Can't delete backend skills
    }
    const updatedSkills = skills.filter((skill) => skill.name !== skillName);
    saveSkills(updatedSkills);
  };

  useEffect(() => {
    if (open && initialConfig) {
      setDeploymentUrl(initialConfig.deploymentUrl);
      setAssistantId(initialConfig.assistantId);
      setLangsmithApiKey(initialConfig.langsmithApiKey || "");
      setRalphModeEnabled(initialConfig.ralphModeEnabled ?? false);
      setRalphMaxIterations(initialConfig.ralphMaxIterations ?? 5);
      setBrowserStreamPort(initialConfig.browserStreamPort ?? 9223);
    }
  }, [open, initialConfig]);

  const handleSave = () => {
    if (!deploymentUrl || !assistantId) {
      alert("Please fill in all required fields");
      return;
    }

    onSave({
      deploymentUrl,
      assistantId,
      langsmithApiKey: langsmithApiKey || undefined,
      ralphModeEnabled,
      ralphMaxIterations,
      browserStreamPort,
    });
    onOpenChange(false);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configuration</DialogTitle>
          <DialogDescription>
            Configure your LangGraph deployment settings. These settings are
            saved in your browser&apos;s local storage and override environment variables.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-6 py-4">
          {/* Deployment Settings */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">
              Deployment Settings
            </h3>
            <div className="grid gap-2">
              <Label htmlFor="deploymentUrl">Deployment URL</Label>
              <Input
                id="deploymentUrl"
                placeholder="http://127.0.0.1:2024"
                value={deploymentUrl}
                onChange={(e) => setDeploymentUrl(e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="assistantId">Assistant ID</Label>
              <Input
                id="assistantId"
                placeholder="browser-agent"
                value={assistantId}
                onChange={(e) => setAssistantId(e.target.value)}
              />
            </div>
          </div>

          {/* LangSmith Settings */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">
              LangSmith (Optional)
            </h3>
            <div className="grid gap-2">
              <Label htmlFor="langsmithApiKey">
                API Key
              </Label>
              <Input
                id="langsmithApiKey"
                type="password"
                placeholder="lsv2_pt_..."
                value={langsmithApiKey}
                onChange={(e) => setLangsmithApiKey(e.target.value)}
              />
            </div>
          </div>

          {/* Agent Behavior Settings */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">
              Agent Behavior
            </h3>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="ralphMode">Enable Ralph Mode</Label>
                <p className="text-xs text-muted-foreground">
                  Allow agent to iterate and refine tasks over multiple passes
                </p>
              </div>
              <Switch
                id="ralphMode"
                checked={ralphModeEnabled}
                onCheckedChange={setRalphModeEnabled}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="ralphMaxIterations">
                Max Iterations
              </Label>
              <Input
                id="ralphMaxIterations"
                type="number"
                min="1"
                max="20"
                placeholder="5"
                value={ralphMaxIterations}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10);
                  if (!isNaN(val) && val >= 1 && val <= 20) {
                    setRalphMaxIterations(val);
                  }
                }}
              />
              <p className="text-xs text-muted-foreground">
                Number of refinement iterations (1-20)
              </p>
            </div>
          </div>

          {/* Browser Settings */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">
              Browser Streaming
            </h3>
            <div className="grid gap-2">
              <Label htmlFor="browserStreamPort">
                Stream Port
              </Label>
              <Input
                id="browserStreamPort"
                type="number"
                min="1024"
                max="65535"
                placeholder="9223"
                value={browserStreamPort}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10);
                  if (!isNaN(val) && val >= 1024 && val <= 65535) {
                    setBrowserStreamPort(val);
                  }
                }}
              />
              <p className="text-xs text-muted-foreground">
                WebSocket port for browser viewport streaming
              </p>
            </div>
          </div>

          {/* Skills Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Skills</h3>
            <div className="border border-border rounded-md divide-y divide-border max-h-48 overflow-y-auto">
              {isLoadingSkills ? (
                <div className="p-3 text-sm text-muted-foreground text-center">
                  Loading skills...
                </div>
              ) : skills.length === 0 ? (
                <div className="p-3 text-sm text-muted-foreground text-center">
                  No skills available
                </div>
              ) : (
                skills.map((skill) => (
                  <div
                    key={skill.name}
                    className="flex items-center justify-between p-2 text-sm"
                  >
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <input
                        type="checkbox"
                        checked={skill.enabled}
                        onChange={() => toggleSkill(skill.name)}
                        className="h-4 w-4 rounded border-border flex-shrink-0"
                      />
                      <div className="flex flex-col min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium truncate">{skill.name}</span>
                          {skill.source === "backend" && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground flex-shrink-0">
                              system
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground truncate">
                          {skill.description.length > 60
                            ? `${skill.description.substring(0, 60)}...`
                            : skill.description}
                        </span>
                      </div>
                    </div>
                    {skill.source === "user" && (
                      <button
                        type="button"
                        onClick={() => deleteSkill(skill.name)}
                        className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-destructive transition-colors flex-shrink-0 ml-2"
                        aria-label={`Delete ${skill.name}`}
                      >
                        <X size={16} />
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              System skills are loaded from the skills directory. Toggle to enable/disable.
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button onClick={handleSave}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
