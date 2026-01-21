"use client";

import { useEffect, useMemo, useRef, useCallback } from "react";
import { format } from "date-fns";
import { Loader2, MessageSquare, Settings, SquarePen } from "lucide-react";
import { useQueryState } from "nuqs";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { ThreadItem } from "@/app/hooks/useThreads";
import { useThreads } from "@/app/hooks/useThreads";

const GROUP_LABELS = {
  today: "Today",
  yesterday: "Yesterday",
  week: "This Week",
  older: "Older",
} as const;

function formatTime(date: Date, now = new Date()): string {
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return format(date, "HH:mm");
  if (days === 1) return "Yesterday";
  if (days < 7) return format(date, "EEEE");
  return format(date, "MM/dd");
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <p className="text-sm text-red-600">Failed to load threads</p>
      <p className="mt-1 text-xs text-muted-foreground">{message}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton
          key={i}
          className="h-16 w-full"
        />
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <MessageSquare className="mb-2 h-12 w-12 text-gray-300" />
      <p className="text-sm text-muted-foreground">No threads found</p>
    </div>
  );
}

interface ThreadListProps {
  onThreadSelect: (id: string) => void;
  onMutateReady?: (mutate: () => void) => void;
  onInterruptCountChange?: (count: number) => void;
  onNewThread?: () => void;
  onSettingsClick?: () => void;
}

export function ThreadList({
  onThreadSelect,
  onMutateReady,
  onInterruptCountChange,
  onNewThread,
  onSettingsClick,
}: ThreadListProps) {
  const [currentThreadId] = useQueryState("threadId");

  const threads = useThreads({
    limit: 20,
  });

  const flattened = useMemo(() => {
    return threads.data?.flat() ?? [];
  }, [threads.data]);

  const isLoadingMore =
    threads.size > 0 && threads.data?.[threads.size - 1] == null;
  const isEmpty = threads.data?.at(0)?.length === 0;
  const isReachingEnd = isEmpty || (threads.data?.at(-1)?.length ?? 0) < 20;

  // Group threads by time
  const grouped = useMemo(() => {
    const now = new Date();
    const groups: Record<keyof typeof GROUP_LABELS, ThreadItem[]> = {
      today: [],
      yesterday: [],
      week: [],
      older: [],
    };

    flattened.forEach((thread) => {
      const diff = now.getTime() - thread.updatedAt.getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));

      if (days === 0) {
        groups.today.push(thread);
      } else if (days === 1) {
        groups.yesterday.push(thread);
      } else if (days < 7) {
        groups.week.push(thread);
      } else {
        groups.older.push(thread);
      }
    });

    return groups;
  }, [flattened]);

  const interruptedCount = useMemo(() => {
    return flattened.filter((t) => t.status === "interrupted").length;
  }, [flattened]);

  // Expose thread list revalidation to parent component
  // Use refs to create a stable callback that always calls the latest mutate function
  const onMutateReadyRef = useRef(onMutateReady);
  const mutateRef = useRef(threads.mutate);

  useEffect(() => {
    onMutateReadyRef.current = onMutateReady;
  }, [onMutateReady]);

  useEffect(() => {
    mutateRef.current = threads.mutate;
  }, [threads.mutate]);

  const mutateFn = useCallback(() => {
    mutateRef.current();
  }, []);

  useEffect(() => {
    onMutateReadyRef.current?.(mutateFn);
    // Only run once on mount to avoid infinite loops
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Notify parent of interrupt count changes
  useEffect(() => {
    onInterruptCountChange?.(interruptedCount);
  }, [interruptedCount, onInterruptCountChange]);

  return (
    <div className="absolute inset-0 flex flex-col bg-background overflow-hidden">
      {/* New Thread button at the top - Claude style */}
      <div className="flex-shrink-0 p-3">
        {onNewThread && (
          <Button
            onClick={onNewThread}
            className="w-full justify-start gap-3 rounded-lg border border-border bg-background px-4 py-3 hover:bg-accent"
            variant="ghost"
          >
            <SquarePen className="h-5 w-5" />
            <span className="text-sm font-medium">New chat</span>
          </Button>
        )}
      </div>

      {/* Recents label - Claude style */}
      <div className="flex-shrink-0 px-3 pt-4 pb-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Recents
        </h3>
      </div>

      <ScrollArea className="h-0 flex-1 w-full overflow-hidden">
        {threads.error && <ErrorState message={threads.error.message} />}

        {!threads.error && !threads.data && threads.isLoading && (
          <LoadingState />
        )}

        {!threads.error && !threads.isLoading && isEmpty && <EmptyState />}

        {!threads.error && !isEmpty && (
          <div className="w-full overflow-hidden px-2 pb-2">
            {(
              Object.keys(GROUP_LABELS) as Array<keyof typeof GROUP_LABELS>
            ).map((group) => {
              const groupThreads = grouped[group];
              if (groupThreads.length === 0) return null;

              return (
                <div
                  key={group}
                  className="mb-3"
                >
                  {/* Show group labels except for "today" since we have Recents above */}
                  {group !== "today" && (
                    <h4 className="m-0 px-2 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {GROUP_LABELS[group]}
                    </h4>
                  )}
                  <div className="flex flex-col gap-0.5">
                    {groupThreads.map((thread) => (
                      <button
                        key={thread.id}
                        type="button"
                        onClick={() => onThreadSelect(thread.id)}
                        className={cn(
                          "group relative w-full cursor-pointer rounded-lg px-3 py-2.5 text-left transition-all duration-150 overflow-hidden",
                          currentThreadId === thread.id
                            ? "bg-accent text-foreground"
                            : "text-muted-foreground hover:bg-accent/50"
                        )}
                        aria-current={currentThreadId === thread.id}
                      >
                        <div className="flex items-center gap-2 overflow-hidden">
                          <MessageSquare className="h-4 w-4 flex-shrink-0" />
                          <span
                            className="flex-1 w-0 text-sm font-medium overflow-hidden whitespace-nowrap text-ellipsis"
                            title={thread.title}
                          >
                            {thread.title}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}

            {!isReachingEnd && (
              <div className="flex justify-center py-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => threads.setSize(threads.size + 1)}
                  disabled={isLoadingMore}
                >
                  {isLoadingMore ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    "Load More"
                  )}
                </Button>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      {/* Footer with settings - Claude style */}
      <div className="flex-shrink-0 border-t border-border p-3">
        {onSettingsClick && (
          <Button
            variant="ghost"
            onClick={onSettingsClick}
            className="w-full justify-start gap-3 rounded-lg px-3 py-2 hover:bg-accent"
          >
            <Settings className="h-5 w-5" />
            <span className="text-sm">Settings</span>
          </Button>
        )}
      </div>
    </div>
  );
}
