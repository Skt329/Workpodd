"use client";

import { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  Brain,
  Wrench,
  CheckCircle2,
  AlertTriangle,
  MessageSquare,
  Bot,
  PlayCircle,
  XCircle,
  ChevronDown,
  ChevronRight,
  User,
} from "lucide-react";
import { useState } from "react";
import type { AgentEvent, EventType } from "@/lib/types";

interface Props {
  events: AgentEvent[];
}

const EVENT_CONFIG: Record<
  string,
  { icon: typeof Brain; color: string; label: string; bgColor: string }
> = {
  LLM_THINKING: {
    icon: Brain,
    color: "text-purple-400",
    label: "Thinking",
    bgColor: "bg-purple-500/15 border-purple-500/30",
  },
  TOOL_CALL: {
    icon: Wrench,
    color: "text-blue-400",
    label: "Tool Call",
    bgColor: "bg-blue-500/15 border-blue-500/30",
  },
  TOOL_RESULT: {
    icon: CheckCircle2,
    color: "text-emerald-400",
    label: "Tool Result",
    bgColor: "bg-emerald-500/15 border-emerald-500/30",
  },
  DECISION: {
    icon: CheckCircle2,
    color: "text-amber-400",
    label: "Decision",
    bgColor: "bg-amber-500/15 border-amber-500/30",
  },
  ERROR: {
    icon: XCircle,
    color: "text-red-400",
    label: "Error",
    bgColor: "bg-red-500/15 border-red-500/30",
  },
  RETRY: {
    icon: AlertTriangle,
    color: "text-orange-400",
    label: "Retry",
    bgColor: "bg-orange-500/15 border-orange-500/30",
  },
  CONVERSATION_START: {
    icon: PlayCircle,
    color: "text-emerald-400",
    label: "Session Start",
    bgColor: "bg-emerald-500/15 border-emerald-500/30",
  },
  CONVERSATION_END: {
    icon: XCircle,
    color: "text-zinc-400",
    label: "Session End",
    bgColor: "bg-zinc-500/15 border-zinc-500/30",
  },
  USER_MESSAGE: {
    icon: User,
    color: "text-sky-400",
    label: "User Message",
    bgColor: "bg-sky-500/15 border-sky-500/30",
  },
  AGENT_RESPONSE: {
    icon: Bot,
    color: "text-primary",
    label: "Agent Response",
    bgColor: "bg-primary/15 border-primary/30",
  },
};

function TraceNode({ event }: { event: AgentEvent }) {
  const [expanded, setExpanded] = useState(false);
  const config = EVENT_CONFIG[event.type] || EVENT_CONFIG.LLM_THINKING;
  const Icon = config.icon;

  const time = new Date(event.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const hasDetails =
    event.input_data || event.output_data || event.tool_name;

  return (
    <div className="animate-slide-up">
      <button
        onClick={() => hasDetails && setExpanded(!expanded)}
        className={`w-full flex items-start gap-3 rounded-xl px-4 py-3 border transition-all ${
          config.bgColor
        } ${hasDetails ? "cursor-pointer hover:brightness-110" : "cursor-default"}`}
      >
        {/* Timeline connector */}
        <div className="flex flex-col items-center gap-1 pt-0.5">
          <div className={`rounded-lg p-1.5 bg-background/50`}>
            <Icon className={`h-4 w-4 ${config.color}`} />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 text-left min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-semibold ${config.color}`}>
              {config.label}
            </span>
            {event.tool_name && (
              <Badge
                variant="outline"
                className="text-[10px] px-1.5 py-0 h-4 font-mono bg-background/50"
              >
                {event.tool_name}
              </Badge>
            )}
            {event.latency_ms !== undefined && event.latency_ms !== null && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 bg-background/50">
                {event.latency_ms}ms
              </Badge>
            )}
            <span className="text-[10px] text-muted-foreground ml-auto">
              {time}
            </span>
          </div>

          {/* Preview */}
          {event.input_data?.message && (
            <p className="text-xs text-muted-foreground mt-1 truncate">
              {String(event.input_data.message)}
            </p>
          )}
          {event.output_data?.response && (
            <p className="text-xs text-muted-foreground mt-1 truncate">
              {String(event.output_data.response)}
            </p>
          )}
          {event.output_data?.error && (
            <p className="text-xs text-red-400 mt-1 truncate">
              {String(event.output_data.error)}
            </p>
          )}
        </div>

        {/* Expand/collapse */}
        {hasDetails && (
          <div className="pt-1">
            {expanded ? (
              <ChevronDown className="h-3 w-3 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-3 w-3 text-muted-foreground" />
            )}
          </div>
        )}
      </button>

      {/* Expanded details */}
      {expanded && hasDetails && (
        <div className="ml-12 mt-1 mb-2 glass rounded-lg p-3 text-xs font-mono overflow-auto max-h-64">
          {event.input_data && (
            <div className="mb-2">
              <span className="text-muted-foreground font-sans text-[10px] uppercase tracking-wider">
                Input
              </span>
              <pre className="mt-1 text-foreground/80 whitespace-pre-wrap break-words">
                {JSON.stringify(event.input_data, null, 2)}
              </pre>
            </div>
          )}
          {event.output_data && (
            <div>
              <span className="text-muted-foreground font-sans text-[10px] uppercase tracking-wider">
                Output
              </span>
              <pre className="mt-1 text-foreground/80 whitespace-pre-wrap break-words">
                {JSON.stringify(event.output_data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ReasoningTrace({ events }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new events
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  if (events.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center h-full">
        <div className="text-center py-20">
          <div className="rounded-2xl bg-primary/10 p-5 mb-4 inline-block animate-pulse-slow">
            <Activity className="h-10 w-10 text-primary/40" />
          </div>
          <h3 className="text-base font-medium text-muted-foreground">
            Waiting for agent activity...
          </h3>
          <p className="text-sm text-muted-foreground/60 mt-1 max-w-xs mx-auto">
            Start a chat conversation to see real-time reasoning events here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="h-full overflow-y-auto px-6 py-4 space-y-2">
      {events.map((event, i) => (
        <TraceNode key={`${event.timestamp}-${i}`} event={event} />
      ))}
    </div>
  );
}
