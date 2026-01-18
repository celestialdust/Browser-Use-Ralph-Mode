"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useQueryState } from "nuqs";
import { getConfig, saveConfig, StandaloneConfig } from "@/lib/config";
import { ConfigDialog } from "@/app/components/ConfigDialog";
import { Button } from "@/components/ui/button";
import { Assistant } from "@langchain/langgraph-sdk";
import { ClientProvider, useClient } from "@/providers/ClientProvider";
import { Menu, PanelLeftClose } from "lucide-react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { ThreadList } from "@/app/components/ThreadList";
import { ChatProvider, useChatContext } from "@/providers/ChatProvider";
import { ChatInterface } from "@/app/components/ChatInterface";
import { BrowserPanel } from "@/app/components/BrowserPanel";

interface HomePageInnerProps {
  config: StandaloneConfig;
  configDialogOpen: boolean;
  setConfigDialogOpen: (open: boolean) => void;
  handleSaveConfig: (config: StandaloneConfig) => void;
}

// Wrapper component to access chat context for browser panel
function ChatWithBrowserPanel({ 
  assistant, 
  config 
}: { 
  assistant: Assistant | null;
  config: StandaloneConfig;
}) {
  const { browserSession } = useChatContext();
  
  return (
    <>
      <ResizablePanel
        id="chat"
        className="relative flex flex-col"
        order={2}
        defaultSize={browserSession?.isActive ? 50 : 80}
      >
        <ChatInterface assistant={assistant} />
      </ResizablePanel>
      
      {browserSession?.isActive && (
        <>
          <ResizableHandle />
          <ResizablePanel
            id="browser"
            order={3}
            defaultSize={30}
            minSize={20}
            maxSize={50}
          >
            <BrowserPanel browserSession={browserSession} />
          </ResizablePanel>
        </>
      )}
    </>
  );
}

function HomePageInner({
  config,
  configDialogOpen,
  setConfigDialogOpen,
  handleSaveConfig,
}: HomePageInnerProps) {
  const client = useClient();
  const [threadId, setThreadId] = useQueryState("threadId");
  const [sidebar, setSidebar] = useQueryState("sidebar");

  const [mutateThreads, setMutateThreads] = useState<(() => void) | null>(null);
  const [interruptCount, setInterruptCount] = useState(0);
  const [assistant, setAssistant] = useState<Assistant | null>(null);
  const [currentThreadTitle, setCurrentThreadTitle] = useState<string | null>(null);

  const fetchAssistant = useCallback(async () => {
    const isUUID =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        config.assistantId
      );

    if (isUUID) {
      // We should try to fetch the assistant directly with this UUID
      try {
        const data = await client.assistants.get(config.assistantId);
        setAssistant(data);
      } catch (error) {
        console.error("Failed to fetch assistant:", error);
        setAssistant({
          assistant_id: config.assistantId,
          graph_id: config.assistantId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          config: {},
          metadata: {},
          version: 1,
          name: "Assistant",
          context: {},
        });
      }
    } else {
      try {
        // We should try to list out the assistants for this graph, and then use the default one.
        // TODO: Paginate this search, but 100 should be enough for graph name
        const assistants = await client.assistants.search({
          graphId: config.assistantId,
          limit: 100,
        });
        const defaultAssistant = assistants.find(
          (assistant) => assistant.metadata?.["created_by"] === "system"
        );
        if (defaultAssistant === undefined) {
          throw new Error("No default assistant found");
        }
        setAssistant(defaultAssistant);
      } catch (error) {
        console.error(
          "Failed to find default assistant from graph_id: try setting the assistant_id directly:",
          error
        );
        setAssistant({
          assistant_id: config.assistantId,
          graph_id: config.assistantId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          config: {},
          metadata: {},
          version: 1,
          name: config.assistantId,
          context: {},
        });
      }
    }
  }, [client, config.assistantId]);

  useEffect(() => {
    fetchAssistant();
  }, [fetchAssistant]);

  // Fetch current thread title
  useEffect(() => {
    if (threadId && client) {
      client.threads
        .get(threadId)
        .then((thread) => {
          // Get title from metadata or try to extract from first message
          let title = thread.metadata?.title as string | undefined;
          
          if (!title && thread.values) {
            // Try to get first message content
            const values = thread.values as any;
            if (values.messages && Array.isArray(values.messages) && values.messages.length > 0) {
              const firstMessage = values.messages[0];
              const content = typeof firstMessage.content === 'string' 
                ? firstMessage.content 
                : '';
              
              // Get first 30 words max
              const words = content.trim().split(/\s+/);
              const maxWords = 30;
              title = words.slice(0, maxWords).join(' ');
              if (words.length > maxWords) {
                title += '...';
              }
            }
          }
          
          setCurrentThreadTitle(title || "New Chat");
        })
        .catch(() => {
          setCurrentThreadTitle("New Chat");
        });
    } else {
      setCurrentThreadTitle(null);
    }
  }, [threadId, client]);

  return (
    <>
      <ConfigDialog
        open={configDialogOpen}
        onOpenChange={setConfigDialogOpen}
        onSave={handleSaveConfig}
        initialConfig={config}
      />
      <div className="flex h-screen flex-col">
        <header className="flex h-14 items-center border-b border-border px-4">
          <div className="flex items-center gap-3">
            {sidebar ? (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebar(null)}
                className="h-8 w-8"
                aria-label="Close sidebar"
              >
                <PanelLeftClose className="h-5 w-5" />
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebar("1")}
                className="h-8 w-8"
                aria-label="Open sidebar"
              >
                <Menu className="h-5 w-5" />
                {interruptCount > 0 && (
                  <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] text-destructive-foreground">
                    {interruptCount}
                  </span>
                )}
              </Button>
            )}
          </div>
          <div className="flex-1 text-center px-4">
            <h1 className="text-sm font-semibold line-clamp-2">
              {currentThreadTitle || "Deep Agent UI"}
            </h1>
          </div>
          <div className="w-8" />
        </header>

        <div className="flex-1 overflow-hidden">
          <ChatProvider
            activeAssistant={assistant}
            onHistoryRevalidate={() => mutateThreads?.()}
            recursionLimit={config.recursionLimit}
            browserStreamPort={config.browserStreamPort}
          >
            <ResizablePanelGroup
              direction="horizontal"
              autoSaveId="standalone-chat-v2"
            >
              {sidebar && (
                <>
                  <ResizablePanel
                    id="thread-history"
                    order={1}
                    defaultSize={20}
                    minSize={15}
                    maxSize={30}
                    className="relative min-w-[280px]"
                  >
                    <ThreadList
                      onThreadSelect={async (id) => {
                        await setThreadId(id);
                      }}
                      onMutateReady={(fn) => setMutateThreads(() => fn)}
                      onInterruptCountChange={setInterruptCount}
                      onNewThread={() => setThreadId(null)}
                      onSettingsClick={() => setConfigDialogOpen(true)}
                    />
                  </ResizablePanel>
                  <ResizableHandle />
                </>
              )}

              <ChatWithBrowserPanel assistant={assistant} config={config} />
            </ResizablePanelGroup>
          </ChatProvider>
        </div>
      </div>
    </>
  );
}

function HomePageContent() {
  const [config, setConfig] = useState<StandaloneConfig | null>(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [assistantId, setAssistantId] = useQueryState("assistantId");

  // On mount, check for saved config, otherwise show config dialog
  useEffect(() => {
    const savedConfig = getConfig();
    if (savedConfig) {
      setConfig(savedConfig);
      if (!assistantId) {
        setAssistantId(savedConfig.assistantId);
      }
    } else {
      setConfigDialogOpen(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // If config changes, update the assistantId
  useEffect(() => {
    if (config && !assistantId) {
      setAssistantId(config.assistantId);
    }
  }, [config, assistantId, setAssistantId]);

  const handleSaveConfig = useCallback((newConfig: StandaloneConfig) => {
    saveConfig(newConfig);
    setConfig(newConfig);
  }, []);

  const langsmithApiKey =
    config?.langsmithApiKey || process.env.NEXT_PUBLIC_LANGSMITH_API_KEY || "";

  if (!config) {
    return (
      <>
        <ConfigDialog
          open={configDialogOpen}
          onOpenChange={setConfigDialogOpen}
          onSave={handleSaveConfig}
        />
        <div className="flex h-screen items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold">Welcome to Standalone Chat</h1>
            <p className="mt-2 text-muted-foreground">
              Configure your deployment to get started
            </p>
            <Button
              onClick={() => setConfigDialogOpen(true)}
              className="mt-4"
            >
              Open Configuration
            </Button>
          </div>
        </div>
      </>
    );
  }

  return (
    <ClientProvider
      deploymentUrl={config.deploymentUrl}
      apiKey={langsmithApiKey}
    >
      <HomePageInner
        config={config}
        configDialogOpen={configDialogOpen}
        setConfigDialogOpen={setConfigDialogOpen}
        handleSaveConfig={handleSaveConfig}
      />
    </ClientProvider>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      }
    >
      <HomePageContent />
    </Suspense>
  );
}
