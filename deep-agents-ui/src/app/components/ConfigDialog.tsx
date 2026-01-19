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
  // Skills state - loaded from localStorage
  const [skills, setSkills] = useState<Skill[]>([]);

  // Load skills from localStorage on mount
  useEffect(() => {
    try {
      const savedSkills = localStorage.getItem("browser-agent-skills");
      if (savedSkills) {
        setSkills(JSON.parse(savedSkills));
      }
    } catch (e) {
      console.error("Failed to load skills from localStorage:", e);
    }
  }, []);

  // Save skills to localStorage when they change
  const saveSkills = (updatedSkills: Skill[]) => {
    setSkills(updatedSkills);
    try {
      localStorage.setItem("browser-agent-skills", JSON.stringify(updatedSkills));
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
            <div className="border border-border rounded-md divide-y divide-border max-h-40 overflow-y-auto">
              {skills.length === 0 ? (
                <div className="p-3 text-sm text-muted-foreground text-center">
                  No skills created yet
                </div>
              ) : (
                skills.map((skill) => (
                  <div
                    key={skill.name}
                    className="flex items-center justify-between p-2 text-sm"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <input
                        type="checkbox"
                        checked={skill.enabled}
                        onChange={() => toggleSkill(skill.name)}
                        className="h-4 w-4 rounded border-border"
                      />
                      <div className="flex flex-col min-w-0">
                        <span className="font-medium truncate">{skill.name}</span>
                        <span className="text-xs text-muted-foreground truncate max-w-[250px]">
                          {skill.description.length > 50
                            ? `${skill.description.substring(0, 50)}...`
                            : skill.description}
                        </span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => deleteSkill(skill.name)}
                      className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-destructive transition-colors flex-shrink-0"
                      aria-label={`Delete ${skill.name}`}
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Skills are reusable workflows learned by the agent. Toggle to enable/disable.
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
